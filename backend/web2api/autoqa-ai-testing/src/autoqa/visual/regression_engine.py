"""
Visual regression engine with semantic comparison.

Provides multiple comparison algorithms for detecting visual differences.
Enterprise-grade features include:
- Anti-aliasing tolerance with Gaussian blur preprocessing
- Automatic dynamic region detection (ads, timestamps, avatars)
- Device/breakpoint-specific baselines with auto-selection
- Scroll position normalization
- Multi-threshold modes (strict, normal, loose, custom)
- Enhanced diff reporting with HTML reports
"""

from __future__ import annotations

import hashlib
import html
import io
import re
from base64 import b64encode
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any, Literal

import numpy as np
import structlog
from PIL import Image, ImageFilter
from scipy import ndimage

from autoqa.dsl.models import VisualComparisonMode

logger = structlog.get_logger(__name__)


class ComparisonMode(StrEnum):
    """Visual comparison algorithms."""

    PIXEL = "pixel"
    PERCEPTUAL = "perceptual"
    STRUCTURAL = "structural"
    SEMANTIC = "semantic"


class ThresholdMode(StrEnum):
    """Preset threshold modes for visual comparison."""

    STRICT = "strict"    # 0.99 similarity required (1% tolerance)
    NORMAL = "normal"    # 0.95 similarity required (5% tolerance)
    LOOSE = "loose"      # 0.85 similarity required (15% tolerance)
    CUSTOM = "custom"    # Use custom threshold value


THRESHOLD_VALUES: dict[ThresholdMode, float] = {
    ThresholdMode.STRICT: 0.01,  # 1% diff allowed
    ThresholdMode.NORMAL: 0.05,  # 5% diff allowed
    ThresholdMode.LOOSE: 0.15,   # 15% diff allowed
    ThresholdMode.CUSTOM: 0.05,  # Default for custom
}


@dataclass
class Region:
    """Represents a rectangular region in an image."""

    x: int
    y: int
    width: int
    height: int
    label: str = ""
    confidence: float = 1.0

    def to_dict(self) -> dict[str, int | str | float]:
        """Convert to dictionary format."""
        return {
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "label": self.label,
            "confidence": self.confidence,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Region:
        """Create Region from dictionary."""
        return cls(
            x=int(data.get("x", 0)),
            y=int(data.get("y", 0)),
            width=int(data.get("width", 0)),
            height=int(data.get("height", 0)),
            label=str(data.get("label", "")),
            confidence=float(data.get("confidence", 1.0)),
        )


@dataclass
class ChangedRegion:
    """Represents a region that changed between images."""

    x: int
    y: int
    width: int
    height: int
    diff_percentage: float
    pixel_count: int


@dataclass
class ComparisonResult:
    """Result of visual comparison with enhanced reporting."""

    passed: bool
    message: str
    diff_percentage: float = 0.0
    diff_path: str | None = None
    baseline_path: str | None = None
    current_path: str | None = None
    similarity_score: float = 1.0
    details: dict[str, Any] | None = None
    # Enhanced reporting fields
    changed_pixel_count: int = 0
    total_pixel_count: int = 0
    changed_regions: list[ChangedRegion] = field(default_factory=list)
    html_report_path: str | None = None
    dynamic_regions_detected: list[Region] = field(default_factory=list)


class VisualRegressionEngine:
    """
    Enterprise-grade engine for visual regression testing.

    Supports multiple comparison modes:
    - Pixel: Exact pixel-by-pixel comparison
    - Perceptual: Perceptual hash based comparison
    - Structural: SSIM-based structural similarity
    - Semantic: AI-based semantic comparison

    Enterprise features:
    - Anti-aliasing tolerance with Gaussian blur preprocessing
    - Automatic dynamic region detection (ads, timestamps, avatars)
    - Device/breakpoint-specific baselines with auto-selection
    - Scroll position normalization
    - Multi-threshold modes (strict, normal, loose, custom)
    - Enhanced diff reporting with HTML reports
    """

    def __init__(
        self,
        baseline_dir: str | Path,
        diff_dir: str | Path | None = None,
        auto_update_baselines: bool = False,
    ) -> None:
        self._baseline_dir = Path(baseline_dir)
        self._diff_dir = Path(diff_dir) if diff_dir else self._baseline_dir / "diffs"
        self._auto_update = auto_update_baselines
        self._log = logger.bind(component="visual_regression")

        self._baseline_dir.mkdir(parents=True, exist_ok=True)
        self._diff_dir.mkdir(parents=True, exist_ok=True)

    # =========================================================================
    # Enterprise Feature: Device/Breakpoint Baselines
    # =========================================================================

    def get_baseline_for_viewport(
        self,
        name: str,
        width: int,
        height: int,
        exact_match_only: bool = False,
    ) -> tuple[Path | None, tuple[int, int] | None]:
        """
        Get baseline image for a specific viewport size.

        Naming convention: {name}_{width}x{height}.png
        Falls back to closest matching baseline if exact match not found.

        Args:
            name: Base name of the baseline
            width: Viewport width
            height: Viewport height
            exact_match_only: If True, only return exact matches

        Returns:
            Tuple of (path, actual_dimensions) or (None, None) if not found
        """
        # Try exact match first
        exact_path = self._baseline_dir / f"{name}_{width}x{height}.png"
        if exact_path.exists():
            return exact_path, (width, height)

        if exact_match_only:
            return None, None

        # Find closest matching baseline
        pattern = re.compile(rf"^{re.escape(name)}_(\d+)x(\d+)\.png$")
        candidates: list[tuple[Path, int, int, float]] = []

        for baseline_file in self._baseline_dir.glob(f"{name}_*x*.png"):
            match = pattern.match(baseline_file.name)
            if match:
                bw, bh = int(match.group(1)), int(match.group(2))
                # Calculate aspect ratio difference + size difference score
                aspect_diff = abs((width / height) - (bw / bh)) if height > 0 and bh > 0 else float("inf")
                size_diff = abs(width - bw) + abs(height - bh)
                score = aspect_diff * 1000 + size_diff  # Prioritize aspect ratio
                candidates.append((baseline_file, bw, bh, score))

        if not candidates:
            # Fall back to non-viewport-specific baseline
            fallback = self._baseline_dir / f"{name}.png"
            if fallback.exists():
                return fallback, None
            return None, None

        # Return closest match
        candidates.sort(key=lambda x: x[3])
        best = candidates[0]
        self._log.info(
            "Using closest viewport baseline",
            requested=f"{width}x{height}",
            using=f"{best[1]}x{best[2]}",
            baseline=best[0].name,
        )
        return best[0], (best[1], best[2])

    def save_baseline_for_viewport(
        self,
        name: str,
        image: Image.Image,
        width: int,
        height: int,
    ) -> Path:
        """Save baseline with viewport dimensions in filename."""
        path = self._baseline_dir / f"{name}_{width}x{height}.png"
        image.save(path)
        self._log.info("Viewport baseline saved", name=name, viewport=f"{width}x{height}")
        return path

    # =========================================================================
    # Enterprise Feature: Auto-Detect Dynamic Regions
    # =========================================================================

    def auto_detect_dynamic_regions(
        self,
        image: bytes | str | Path | Image.Image,
        entropy_threshold: float = 6.5,
        variance_threshold: float = 2000.0,
        min_region_size: int = 50,
        grid_size: int = 32,
    ) -> list[Region]:
        """
        Automatically detect dynamic regions using entropy and variance analysis.

        High-entropy regions typically contain:
        - Advertisements (highly varied content)
        - User avatars (unique per session)
        - Timestamps/dates (constantly changing)
        - Dynamic counters/statistics

        Args:
            image: Image to analyze
            entropy_threshold: Entropy threshold (0-8, higher = more chaotic)
            variance_threshold: Color variance threshold
            min_region_size: Minimum region dimension to report
            grid_size: Analysis grid cell size in pixels

        Returns:
            List of detected dynamic regions
        """
        img = self._load_image(image)
        img_array = np.array(img)
        h, w = img_array.shape[:2]

        dynamic_regions: list[Region] = []
        grid_h = (h + grid_size - 1) // grid_size
        grid_w = (w + grid_size - 1) // grid_size

        # Create entropy and variance maps
        entropy_map = np.zeros((grid_h, grid_w))
        variance_map = np.zeros((grid_h, grid_w))

        for gy in range(grid_h):
            for gx in range(grid_w):
                y1 = gy * grid_size
                y2 = min((gy + 1) * grid_size, h)
                x1 = gx * grid_size
                x2 = min((gx + 1) * grid_size, w)

                cell = img_array[y1:y2, x1:x2]

                # Calculate entropy (measure of randomness/information)
                gray_cell = np.mean(cell, axis=2).astype(np.uint8)
                hist, _ = np.histogram(gray_cell, bins=256, range=(0, 256))
                hist = hist[hist > 0]
                probs = hist / hist.sum()
                entropy = -np.sum(probs * np.log2(probs))
                entropy_map[gy, gx] = entropy

                # Calculate variance across color channels
                variance = np.var(cell)
                variance_map[gy, gx] = variance

        # Find high-entropy, high-variance regions
        high_entropy = entropy_map > entropy_threshold
        high_variance = variance_map > variance_threshold
        dynamic_mask = high_entropy & high_variance

        # Label connected components
        labeled, num_features = ndimage.label(dynamic_mask)

        for label_id in range(1, num_features + 1):
            coords = np.where(labeled == label_id)
            if len(coords[0]) == 0:
                continue

            gy_min, gy_max = coords[0].min(), coords[0].max()
            gx_min, gx_max = coords[1].min(), coords[1].max()

            region_x = gx_min * grid_size
            region_y = gy_min * grid_size
            region_w = (gx_max - gx_min + 1) * grid_size
            region_h = (gy_max - gy_min + 1) * grid_size

            # Skip small regions
            if region_w < min_region_size or region_h < min_region_size:
                continue

            # Calculate confidence based on entropy/variance deviation
            region_entropy = entropy_map[gy_min:gy_max+1, gx_min:gx_max+1].mean()
            confidence = min(1.0, region_entropy / 8.0)

            dynamic_regions.append(Region(
                x=region_x,
                y=region_y,
                width=min(region_w, w - region_x),
                height=min(region_h, h - region_y),
                label="auto_detected_dynamic",
                confidence=confidence,
            ))

        self._log.info("Dynamic regions detected", count=len(dynamic_regions))
        return dynamic_regions

    # =========================================================================
    # Enterprise Feature: Anti-Aliasing Tolerance
    # =========================================================================

    def apply_anti_aliasing_preprocessing(
        self,
        image: Image.Image,
        sigma: float = 1.0,
        morphological_smoothing: bool = True,
    ) -> Image.Image:
        """
        Apply anti-aliasing preprocessing to reduce font rendering differences.

        Args:
            image: Input image
            sigma: Gaussian blur sigma (0.5-3.0 typical)
            morphological_smoothing: Apply morphological operations for text smoothing

        Returns:
            Preprocessed image
        """
        if sigma <= 0:
            preprocessed = image.copy()
        else:
            # Apply Gaussian blur
            radius = max(1, int(sigma * 2))
            preprocessed = image.filter(ImageFilter.GaussianBlur(radius=radius))

        if morphological_smoothing:
            # Convert to numpy for morphological operations
            img_array = np.array(preprocessed)

            # Apply morphological closing then opening to smooth edges
            # This helps normalize font rendering differences across platforms
            for channel in range(3):
                channel_data = img_array[:, :, channel]
                # Closing (dilation then erosion) - fills small holes
                closed = ndimage.grey_closing(channel_data, size=(2, 2))
                # Opening (erosion then dilation) - removes small protrusions
                opened = ndimage.grey_opening(closed, size=(2, 2))
                img_array[:, :, channel] = opened

            preprocessed = Image.fromarray(img_array)

        return preprocessed

    # =========================================================================
    # Enterprise Feature: Scroll Position Normalization
    # =========================================================================

    def normalize_scroll_position(
        self,
        image: Image.Image,
        crop_browser_chrome: bool = True,
        chrome_height_estimate: int = 0,
    ) -> Image.Image:
        """
        Normalize image assuming it starts from top of page.

        Args:
            image: Input screenshot
            crop_browser_chrome: Attempt to detect and crop browser chrome
            chrome_height_estimate: Manual chrome height to crop (0 = auto-detect)

        Returns:
            Normalized image
        """
        if not crop_browser_chrome:
            return image

        img_array = np.array(image)
        h, w = img_array.shape[:2]

        if chrome_height_estimate > 0:
            crop_top = min(chrome_height_estimate, h // 4)
        else:
            # Auto-detect browser chrome by looking for uniform color bands at top
            crop_top = 0
            for y in range(min(150, h // 4)):
                row = img_array[y]
                row_variance = np.var(row)
                # Very uniform rows (like browser chrome) have low variance
                if row_variance < 100:
                    crop_top = y + 1
                else:
                    break

        if crop_top > 0:
            self._log.debug("Cropping browser chrome", pixels=crop_top)
            return Image.fromarray(img_array[crop_top:])

        return image

    # =========================================================================
    # Enterprise Feature: Enhanced Diff Reporting
    # =========================================================================

    def _identify_changed_regions(
        self,
        diff_mask: np.ndarray,
        min_region_pixels: int = 100,
    ) -> list[ChangedRegion]:
        """Identify distinct regions that changed."""
        # Label connected components in the diff mask
        labeled, num_features = ndimage.label(diff_mask)
        regions: list[ChangedRegion] = []

        for label_id in range(1, num_features + 1):
            coords = np.where(labeled == label_id)
            if len(coords[0]) < min_region_pixels:
                continue

            y_min, y_max = int(coords[0].min()), int(coords[0].max())
            x_min, x_max = int(coords[1].min()), int(coords[1].max())
            pixel_count = len(coords[0])
            region_area = (y_max - y_min + 1) * (x_max - x_min + 1)

            regions.append(ChangedRegion(
                x=x_min,
                y=y_min,
                width=x_max - x_min + 1,
                height=y_max - y_min + 1,
                diff_percentage=pixel_count / region_area if region_area > 0 else 0,
                pixel_count=pixel_count,
            ))

        return regions

    def generate_html_diff_report(
        self,
        baseline_name: str,
        result: ComparisonResult,
        baseline_img: Image.Image,
        current_img: Image.Image,
        diff_img: Image.Image,
    ) -> Path:
        """
        Generate an HTML diff report with side-by-side comparison.

        Args:
            baseline_name: Name of the baseline
            result: Comparison result
            baseline_img: Baseline image
            current_img: Current image
            diff_img: Diff visualization image

        Returns:
            Path to the generated HTML report
        """
        report_path = self._diff_dir / f"{baseline_name}_report.html"

        def img_to_base64(img: Image.Image) -> str:
            buffer = io.BytesIO()
            img.save(buffer, format="PNG")
            return b64encode(buffer.getvalue()).decode("utf-8")

        baseline_b64 = img_to_base64(baseline_img)
        current_b64 = img_to_base64(current_img)
        diff_b64 = img_to_base64(diff_img)

        changed_regions_html = ""
        for i, region in enumerate(result.changed_regions, 1):
            changed_regions_html += f"""
            <tr>
                <td>{i}</td>
                <td>({region.x}, {region.y})</td>
                <td>{region.width}x{region.height}</td>
                <td>{region.pixel_count:,}</td>
                <td>{region.diff_percentage:.1%}</td>
            </tr>"""

        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Visual Regression Report: {html.escape(baseline_name)}</title>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #1a1a2e; color: #eee; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; border-radius: 12px; margin-bottom: 30px; }}
        .header h1 {{ font-size: 24px; margin-bottom: 10px; }}
        .status {{ display: inline-block; padding: 6px 16px; border-radius: 20px; font-weight: 600; }}
        .status.passed {{ background: #10b981; }}
        .status.failed {{ background: #ef4444; }}
        .metrics {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }}
        .metric {{ background: #16213e; padding: 20px; border-radius: 8px; text-align: center; }}
        .metric-value {{ font-size: 36px; font-weight: bold; color: #667eea; }}
        .metric-label {{ color: #888; margin-top: 5px; }}
        .images {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin-bottom: 30px; }}
        .image-card {{ background: #16213e; border-radius: 8px; overflow: hidden; }}
        .image-card h3 {{ padding: 15px; background: #0f3460; }}
        .image-card img {{ width: 100%; height: auto; display: block; }}
        .regions-table {{ width: 100%; background: #16213e; border-radius: 8px; overflow: hidden; }}
        .regions-table th, .regions-table td {{ padding: 12px 15px; text-align: left; }}
        .regions-table th {{ background: #0f3460; }}
        .regions-table tr:hover {{ background: #1f4068; }}
        @media (max-width: 1200px) {{ .images {{ grid-template-columns: 1fr; }} }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Visual Regression Report</h1>
        <p>Baseline: <strong>{html.escape(baseline_name)}</strong></p>
        <p style="margin-top: 10px;"><span class="status {'passed' if result.passed else 'failed'}">{'PASSED' if result.passed else 'FAILED'}</span></p>
    </div>

    <div class="metrics">
        <div class="metric">
            <div class="metric-value">{result.similarity_score:.1%}</div>
            <div class="metric-label">Similarity Score</div>
        </div>
        <div class="metric">
            <div class="metric-value">{result.diff_percentage:.2%}</div>
            <div class="metric-label">Difference</div>
        </div>
        <div class="metric">
            <div class="metric-value">{result.changed_pixel_count:,}</div>
            <div class="metric-label">Changed Pixels</div>
        </div>
        <div class="metric">
            <div class="metric-value">{len(result.changed_regions)}</div>
            <div class="metric-label">Changed Regions</div>
        </div>
    </div>

    <div class="images">
        <div class="image-card">
            <h3>Baseline</h3>
            <img src="data:image/png;base64,{baseline_b64}" alt="Baseline">
        </div>
        <div class="image-card">
            <h3>Current</h3>
            <img src="data:image/png;base64,{current_b64}" alt="Current">
        </div>
        <div class="image-card">
            <h3>Difference</h3>
            <img src="data:image/png;base64,{diff_b64}" alt="Diff">
        </div>
    </div>

    <h2 style="margin-bottom: 15px;">Changed Regions</h2>
    <table class="regions-table">
        <thead>
            <tr>
                <th>#</th>
                <th>Position (x, y)</th>
                <th>Size</th>
                <th>Pixels Changed</th>
                <th>Region Density</th>
            </tr>
        </thead>
        <tbody>
            {changed_regions_html if changed_regions_html else '<tr><td colspan="5" style="text-align:center;color:#888;">No significant changed regions detected</td></tr>'}
        </tbody>
    </table>
</body>
</html>"""

        report_path.write_text(html_content)
        self._log.info("HTML diff report generated", path=str(report_path))
        return report_path

    # =========================================================================
    # Main Compare Method (Enhanced)
    # =========================================================================

    def compare(
        self,
        baseline_name: str,
        current_image: bytes | str | Path | Image.Image,
        mode: VisualComparisonMode | ComparisonMode = ComparisonMode.SEMANTIC,
        threshold: float = 0.05,
        ignore_regions: list[dict[str, int]] | None = None,
        ignore_colors: bool = False,
        update_baseline: bool = False,
        # Enterprise features
        threshold_mode: ThresholdMode | Literal["strict", "normal", "loose", "custom"] = ThresholdMode.CUSTOM,
        anti_aliasing_tolerance: float = 0.0,
        anti_aliasing_sigma: float = 1.0,
        auto_mask_dynamic: bool = False,
        viewport_width: int | None = None,
        viewport_height: int | None = None,
        normalize_scroll: bool = True,
        generate_html_report: bool = False,
    ) -> ComparisonResult:
        """
        Compare current image against baseline with enterprise features.

        Args:
            baseline_name: Name of the baseline image
            current_image: Current screenshot to compare
            mode: Comparison algorithm to use
            threshold: Maximum allowed difference (0.0 to 1.0) - used when threshold_mode is "custom"
            ignore_regions: Regions to ignore in comparison
            ignore_colors: Whether to ignore color differences
            update_baseline: Whether to update baseline if missing or on failure
            threshold_mode: Preset threshold mode ("strict", "normal", "loose", "custom")
            anti_aliasing_tolerance: Anti-aliasing tolerance (0-1), applies blur preprocessing
            anti_aliasing_sigma: Gaussian blur sigma for anti-aliasing preprocessing
            auto_mask_dynamic: Automatically detect and mask dynamic regions
            viewport_width: Viewport width for breakpoint-specific baselines
            viewport_height: Viewport height for breakpoint-specific baselines
            normalize_scroll: Normalize scroll position (crop browser chrome)
            generate_html_report: Generate detailed HTML diff report

        Returns:
            ComparisonResult with comparison details and enhanced reporting
        """
        current_img = self._load_image(current_image)

        # Enterprise: Resolve threshold from mode
        resolved_threshold_mode = ThresholdMode(threshold_mode) if isinstance(threshold_mode, str) else threshold_mode
        effective_threshold = threshold if resolved_threshold_mode == ThresholdMode.CUSTOM else THRESHOLD_VALUES[resolved_threshold_mode]

        # Enterprise: Viewport-specific baseline selection
        if viewport_width is not None and viewport_height is not None:
            baseline_path, actual_dims = self.get_baseline_for_viewport(
                baseline_name, viewport_width, viewport_height
            )
            if baseline_path is None:
                baseline_path = self._baseline_dir / f"{baseline_name}.png"
        else:
            baseline_path = self._baseline_dir / f"{baseline_name}.png"

        # Enterprise: Scroll position normalization
        if normalize_scroll:
            current_img = self.normalize_scroll_position(current_img)

        # Enterprise: Auto-detect dynamic regions
        detected_dynamic_regions: list[Region] = []
        if auto_mask_dynamic:
            detected_dynamic_regions = self.auto_detect_dynamic_regions(current_img)
            dynamic_ignore_regions = [r.to_dict() for r in detected_dynamic_regions]
            if ignore_regions:
                ignore_regions = ignore_regions + dynamic_ignore_regions  # type: ignore[assignment]
            else:
                ignore_regions = dynamic_ignore_regions  # type: ignore[assignment]

        if not baseline_path.exists():
            if update_baseline or self._auto_update:
                if viewport_width is not None and viewport_height is not None:
                    saved_path = self.save_baseline_for_viewport(baseline_name, current_img, viewport_width, viewport_height)
                else:
                    saved_path = self._save_baseline(baseline_name, current_img)
                return ComparisonResult(
                    passed=True,
                    message="Baseline created",
                    baseline_path=str(saved_path),
                    dynamic_regions_detected=detected_dynamic_regions,
                )
            else:
                return ComparisonResult(
                    passed=False,
                    message=f"Baseline not found: {baseline_name}",
                    diff_percentage=1.0,
                    dynamic_regions_detected=detected_dynamic_regions,
                )

        baseline_img = Image.open(baseline_path)

        # Enterprise: Normalize scroll on baseline too
        if normalize_scroll:
            baseline_img = self.normalize_scroll_position(baseline_img)

        if current_img.size != baseline_img.size:
            self._log.warning(
                "Image size mismatch",
                baseline=baseline_img.size,
                current=current_img.size,
            )
            current_img = current_img.resize(baseline_img.size, Image.Resampling.LANCZOS)

        # Enterprise: Anti-aliasing preprocessing
        if anti_aliasing_tolerance > 0:
            effective_sigma = anti_aliasing_sigma * anti_aliasing_tolerance
            current_img = self.apply_anti_aliasing_preprocessing(
                current_img, sigma=effective_sigma, morphological_smoothing=True
            )
            baseline_img = self.apply_anti_aliasing_preprocessing(
                baseline_img, sigma=effective_sigma, morphological_smoothing=True
            )

        if ignore_regions:
            current_img = self._mask_regions(current_img, ignore_regions)
            baseline_img = self._mask_regions(baseline_img, ignore_regions)

        if ignore_colors:
            current_img = current_img.convert("L").convert("RGB")
            baseline_img = baseline_img.convert("L").convert("RGB")

        comparison_mode = ComparisonMode(mode.value) if isinstance(mode, VisualComparisonMode) else mode

        match comparison_mode:
            case ComparisonMode.PIXEL:
                result = self._compare_pixel(baseline_img, current_img, effective_threshold)
            case ComparisonMode.PERCEPTUAL:
                result = self._compare_perceptual(baseline_img, current_img, effective_threshold)
            case ComparisonMode.STRUCTURAL:
                result = self._compare_structural(baseline_img, current_img, effective_threshold)
            case ComparisonMode.SEMANTIC:
                result = self._compare_semantic(baseline_img, current_img, effective_threshold)
            case _:
                raise ValueError(f"Unknown comparison mode: {mode}")

        result.baseline_path = str(baseline_path)
        result.dynamic_regions_detected = detected_dynamic_regions

        # Enterprise: Enhanced diff reporting - calculate changed regions
        baseline_arr = np.array(baseline_img)
        current_arr = np.array(current_img)
        diff_arr = np.abs(baseline_arr.astype(int) - current_arr.astype(int))
        diff_gray = np.mean(diff_arr, axis=2)
        diff_mask = diff_gray > 10

        result.total_pixel_count = baseline_arr.shape[0] * baseline_arr.shape[1]
        result.changed_pixel_count = int(np.sum(diff_mask))
        result.changed_regions = self._identify_changed_regions(diff_mask)

        if not result.passed:
            current_path = self._diff_dir / f"{baseline_name}_current.png"
            diff_path = self._diff_dir / f"{baseline_name}_diff.png"

            current_img.save(current_path)
            result.current_path = str(current_path)

            diff_image = self._generate_diff_image(baseline_img, current_img)
            diff_image.save(diff_path)
            result.diff_path = str(diff_path)

            # Enterprise: HTML diff report
            if generate_html_report:
                report_path = self.generate_html_diff_report(
                    baseline_name, result, baseline_img, current_img, diff_image
                )
                result.html_report_path = str(report_path)

            if update_baseline:
                if viewport_width is not None and viewport_height is not None:
                    self.save_baseline_for_viewport(baseline_name, current_img, viewport_width, viewport_height)
                else:
                    self._save_baseline(baseline_name, current_img)
                result.message += " (baseline updated)"

        return result

    def _load_image(self, image: bytes | str | Path | Image.Image) -> Image.Image:
        """Load image from various sources."""
        if isinstance(image, Image.Image):
            return image.convert("RGB")
        elif isinstance(image, bytes):
            return Image.open(io.BytesIO(image)).convert("RGB")
        elif isinstance(image, (str, Path)):
            return Image.open(image).convert("RGB")
        else:
            raise ValueError(f"Unsupported image type: {type(image)}")

    def _save_baseline(self, name: str, image: Image.Image) -> Path:
        """Save image as baseline."""
        path = self._baseline_dir / f"{name}.png"
        image.save(path)
        self._log.info("Baseline saved", name=name, path=str(path))
        return path

    def _mask_regions(
        self, image: Image.Image, regions: list[dict[str, int]]
    ) -> Image.Image:
        """Mask specified regions with black."""
        from PIL import ImageDraw

        masked = image.copy()
        draw = ImageDraw.Draw(masked)

        for region in regions:
            x = region.get("x", 0)
            y = region.get("y", 0)
            w = region.get("width", 0)
            h = region.get("height", 0)
            draw.rectangle([x, y, x + w, y + h], fill="black")

        return masked

    def _compare_pixel(
        self, baseline: Image.Image, current: Image.Image, threshold: float
    ) -> ComparisonResult:
        """Pixel-by-pixel comparison."""
        baseline_arr = np.array(baseline)
        current_arr = np.array(current)

        diff = np.abs(baseline_arr.astype(int) - current_arr.astype(int))
        diff_pixels = np.sum(diff > 0)
        total_pixels = baseline_arr.size

        diff_percentage = diff_pixels / total_pixels

        passed = diff_percentage <= threshold

        return ComparisonResult(
            passed=passed,
            message="Pixel comparison " + ("passed" if passed else "failed"),
            diff_percentage=diff_percentage,
            similarity_score=1.0 - diff_percentage,
            details={
                "diff_pixels": int(diff_pixels),
                "total_pixels": int(total_pixels),
                "method": "pixel",
            },
        )

    def _compare_perceptual(
        self, baseline: Image.Image, current: Image.Image, threshold: float
    ) -> ComparisonResult:
        """Perceptual hash based comparison."""
        try:
            import imagehash

            baseline_hash = imagehash.phash(baseline)
            current_hash = imagehash.phash(current)

            hash_diff = baseline_hash - current_hash
            max_diff = 64

            diff_percentage = hash_diff / max_diff
            passed = diff_percentage <= threshold

            return ComparisonResult(
                passed=passed,
                message="Perceptual comparison " + ("passed" if passed else "failed"),
                diff_percentage=diff_percentage,
                similarity_score=1.0 - diff_percentage,
                details={
                    "hash_distance": hash_diff,
                    "baseline_hash": str(baseline_hash),
                    "current_hash": str(current_hash),
                    "method": "perceptual",
                },
            )
        except ImportError:
            self._log.warning("imagehash not available, falling back to pixel comparison")
            return self._compare_pixel(baseline, current, threshold)

    def _compare_structural(
        self, baseline: Image.Image, current: Image.Image, threshold: float
    ) -> ComparisonResult:
        """Structural similarity (SSIM) comparison."""
        try:
            from skimage.metrics import structural_similarity as ssim

            baseline_gray = np.array(baseline.convert("L"))
            current_gray = np.array(current.convert("L"))

            similarity, diff_map = ssim(
                baseline_gray,
                current_gray,
                full=True,
                data_range=255,
            )

            diff_percentage = 1.0 - similarity
            passed = diff_percentage <= threshold

            return ComparisonResult(
                passed=passed,
                message="Structural comparison " + ("passed" if passed else "failed"),
                diff_percentage=diff_percentage,
                similarity_score=similarity,
                details={
                    "ssim_score": float(similarity),
                    "method": "structural",
                },
            )
        except ImportError:
            self._log.warning("scikit-image not available, falling back to perceptual")
            return self._compare_perceptual(baseline, current, threshold)

    def _compare_semantic(
        self, baseline: Image.Image, current: Image.Image, threshold: float
    ) -> ComparisonResult:
        """
        Semantic comparison using multiple algorithms.

        Combines structural similarity with perceptual hashing for
        more intelligent comparison that tolerates minor UI changes.
        """
        struct_result = self._compare_structural(baseline, current, threshold)
        percept_result = self._compare_perceptual(baseline, current, threshold)

        combined_score = (struct_result.similarity_score * 0.6 +
                         percept_result.similarity_score * 0.4)

        diff_percentage = 1.0 - combined_score
        passed = diff_percentage <= threshold

        return ComparisonResult(
            passed=passed,
            message="Semantic comparison " + ("passed" if passed else "failed"),
            diff_percentage=diff_percentage,
            similarity_score=combined_score,
            details={
                "structural_score": struct_result.similarity_score,
                "perceptual_score": percept_result.similarity_score,
                "combined_score": combined_score,
                "method": "semantic",
            },
        )

    def _generate_diff_image(
        self, baseline: Image.Image, current: Image.Image
    ) -> Image.Image:
        """Generate a visual diff image highlighting differences."""
        baseline_arr = np.array(baseline).astype(float)
        current_arr = np.array(current).astype(float)

        diff = np.abs(baseline_arr - current_arr)

        diff_normalized = (diff / diff.max() * 255).astype(np.uint8) if diff.max() > 0 else diff.astype(np.uint8)

        diff_gray = np.mean(diff_normalized, axis=2)

        diff_mask = diff_gray > 10

        result = current_arr.copy()
        result[diff_mask] = [255, 0, 0]

        blended = (baseline_arr * 0.3 + result * 0.7).astype(np.uint8)

        return Image.fromarray(blended)

    def update_baseline(
        self,
        baseline_name: str,
        image: bytes | str | Path | Image.Image,
    ) -> Path:
        """Manually update a baseline image."""
        img = self._load_image(image)
        return self._save_baseline(baseline_name, img)

    def delete_baseline(self, baseline_name: str) -> bool:
        """Delete a baseline image."""
        path = self._baseline_dir / f"{baseline_name}.png"
        if path.exists():
            path.unlink()
            self._log.info("Baseline deleted", name=baseline_name)
            return True
        return False

    def list_baselines(self) -> list[str]:
        """List all baseline names."""
        return [p.stem for p in self._baseline_dir.glob("*.png")]

    def get_baseline_hash(self, baseline_name: str) -> str | None:
        """Get hash of baseline image for versioning."""
        path = self._baseline_dir / f"{baseline_name}.png"
        if not path.exists():
            return None

        with open(path, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()[:16]
