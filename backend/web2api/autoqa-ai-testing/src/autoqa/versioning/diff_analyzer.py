"""
Version diff analyzer for comparing test snapshots.

Provides comprehensive comparison of visual, text, element, layout,
and network differences between test runs.
"""

from __future__ import annotations

import difflib
import re
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import structlog

from autoqa.versioning.models import (
    BoundingBox,
    ChangeSeverity,
    ChangeType,
    ElementChange,
    LayoutChange,
    NetworkChange,
    NetworkRequest,
    TestSnapshot,
    TextChange,
    VersionDiff,
    VisualChange,
)

logger = structlog.get_logger(__name__)


class DiffAnalyzerError(Exception):
    """Raised when diff analysis fails."""

    pass


class VersionDiffAnalyzer:
    """
    Analyzes differences between two test snapshots.

    Detects:
    - Visual changes (screenshots) with percentage diff
    - Text content changes (added/removed/modified)
    - Element changes (new/removed/moved elements)
    - Layout shifts (position changes)
    - Color/style changes
    - Network request changes
    """

    # Thresholds for severity classification
    VISUAL_CRITICAL_THRESHOLD = 0.25  # 25% change
    VISUAL_HIGH_THRESHOLD = 0.10  # 10% change
    VISUAL_MEDIUM_THRESHOLD = 0.05  # 5% change

    LAYOUT_CRITICAL_SHIFT = 100  # pixels
    LAYOUT_HIGH_SHIFT = 50
    LAYOUT_MEDIUM_SHIFT = 20

    def __init__(
        self,
        reports_dir: str | Path = ".autoqa/reports/diffs",
        visual_threshold: float = 0.05,
    ) -> None:
        self._reports_dir = Path(reports_dir)
        self._visual_threshold = visual_threshold
        self._log = logger.bind(component="diff_analyzer")

        self._reports_dir.mkdir(parents=True, exist_ok=True)

    def compare_versions(
        self,
        snapshot_a: TestSnapshot,
        snapshot_b: TestSnapshot,
    ) -> VersionDiff:
        """
        Compare two snapshots and return comprehensive diff.

        Args:
            snapshot_a: First (older) snapshot
            snapshot_b: Second (newer) snapshot

        Returns:
            VersionDiff containing all detected changes
        """
        start_time = time.monotonic()

        self._log.info(
            "Comparing versions",
            test=snapshot_a.test_name,
            version_a=snapshot_a.version_id,
            version_b=snapshot_b.version_id,
        )

        diff = VersionDiff(
            snapshot_a=snapshot_a,
            snapshot_b=snapshot_b,
            generated_at=datetime.now(UTC),
        )

        # Visual comparison
        if snapshot_a.screenshot_path and snapshot_b.screenshot_path:
            diff.visual_changes = self._compare_visual(
                snapshot_a, snapshot_b
            )

        # Text content comparison
        diff.text_changes = self._compare_texts(snapshot_a, snapshot_b)

        # Element state comparison
        diff.element_changes = self._compare_elements(snapshot_a, snapshot_b)

        # Layout comparison
        diff.layout_changes = self._compare_layouts(snapshot_a, snapshot_b)

        # Network request comparison
        diff.network_changes = self._compare_network(snapshot_a, snapshot_b)

        # Calculate totals and severity counts
        self._calculate_summary(diff)

        diff.comparison_duration_ms = int((time.monotonic() - start_time) * 1000)

        self._log.info(
            "Comparison complete",
            total_changes=diff.total_changes,
            critical=diff.critical_changes,
            duration_ms=diff.comparison_duration_ms,
        )

        return diff

    def generate_diff_report(
        self,
        diff: VersionDiff,
        output_path: str | Path | None = None,
    ) -> str:
        """
        Generate HTML report for a diff.

        Args:
            diff: VersionDiff to generate report for
            output_path: Path to save report (optional)

        Returns:
            HTML content of the report
        """
        html = self._render_html_report(diff)

        if output_path:
            path = Path(output_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(html, encoding="utf-8")
            self._log.info("Diff report saved", path=str(path))
        else:
            # Save to default location
            filename = (
                f"{diff.snapshot_a.test_name}_"
                f"{diff.snapshot_a.timestamp.strftime('%Y-%m-%d')}_vs_"
                f"{diff.snapshot_b.timestamp.strftime('%Y-%m-%d')}.html"
            )
            safe_filename = re.sub(r"[^\w\-_.]", "_", filename)
            default_path = self._reports_dir / safe_filename
            default_path.write_text(html, encoding="utf-8")
            self._log.info("Diff report saved", path=str(default_path))

        return html

    def get_change_summary(self, diff: VersionDiff) -> str:
        """
        Generate a human-readable summary of changes.

        Args:
            diff: VersionDiff to summarize

        Returns:
            Text summary of changes
        """
        lines = [
            f"Version Diff Summary: {diff.snapshot_a.test_name}",
            f"From: {diff.snapshot_a.timestamp.strftime('%Y-%m-%d %H:%M:%S')} ({diff.snapshot_a.version_id})",
            f"To:   {diff.snapshot_b.timestamp.strftime('%Y-%m-%d %H:%M:%S')} ({diff.snapshot_b.version_id})",
            "",
            f"Total Changes: {diff.total_changes}",
            f"  Critical: {diff.critical_changes}",
            f"  High: {diff.high_changes}",
            f"  Medium: {diff.medium_changes}",
            f"  Low: {diff.low_changes}",
            "",
        ]

        # Visual changes
        if diff.visual_changes:
            vc = diff.visual_changes
            lines.append(f"Visual Changes: {vc.diff_percentage:.1%} difference")
            if vc.changed_regions:
                lines.append(f"  Changed regions: {len(vc.changed_regions)}")

        # Text changes
        if diff.text_changes:
            lines.append(f"Text Changes: {len(diff.text_changes)}")
            for tc in diff.text_changes[:5]:  # Show first 5
                lines.append(f"  - [{tc.change_type}] {tc.key or tc.selector}")
            if len(diff.text_changes) > 5:
                lines.append(f"  ... and {len(diff.text_changes) - 5} more")

        # Element changes
        if diff.element_changes:
            lines.append(f"Element Changes: {len(diff.element_changes)}")
            added = sum(1 for e in diff.element_changes if e.change_type == ChangeType.ADDED)
            removed = sum(1 for e in diff.element_changes if e.change_type == ChangeType.REMOVED)
            modified = sum(1 for e in diff.element_changes if e.change_type == ChangeType.MODIFIED)
            lines.append(f"  Added: {added}, Removed: {removed}, Modified: {modified}")

        # Layout changes
        if diff.layout_changes:
            lines.append(f"Layout Changes: {len(diff.layout_changes)}")
            max_shift = max(lc.shift_distance for lc in diff.layout_changes)
            lines.append(f"  Max shift: {max_shift:.1f}px")

        # Network changes
        if diff.network_changes:
            lines.append(f"Network Changes: {len(diff.network_changes)}")
            added = sum(1 for n in diff.network_changes if n.change_type == ChangeType.ADDED)
            removed = sum(1 for n in diff.network_changes if n.change_type == ChangeType.REMOVED)
            lines.append(f"  New requests: {added}, Removed: {removed}")

        return "\n".join(lines)

    def _compare_visual(
        self,
        snapshot_a: TestSnapshot,
        snapshot_b: TestSnapshot,
    ) -> VisualChange | None:
        """Compare screenshots between snapshots."""
        try:
            import numpy as np
            from PIL import Image
        except ImportError:
            self._log.warning("PIL/numpy not available for visual comparison")
            return None

        path_a = Path(snapshot_a.screenshot_path) if snapshot_a.screenshot_path else None
        path_b = Path(snapshot_b.screenshot_path) if snapshot_b.screenshot_path else None

        if not path_a or not path_b or not path_a.exists() or not path_b.exists():
            return None

        try:
            img_a = Image.open(path_a).convert("RGB")
            img_b = Image.open(path_b).convert("RGB")

            # Resize if dimensions differ
            if img_a.size != img_b.size:
                img_b = img_b.resize(img_a.size, Image.Resampling.LANCZOS)

            arr_a = np.array(img_a)
            arr_b = np.array(img_b)

            # Calculate pixel difference
            diff = np.abs(arr_a.astype(float) - arr_b.astype(float))
            diff_normalized = diff / 255.0

            # Calculate overall difference percentage
            diff_percentage = float(np.mean(diff_normalized))

            # Find changed regions (simplified)
            changed_regions = self._find_changed_regions(diff_normalized)

            # Determine severity
            if diff_percentage >= self.VISUAL_CRITICAL_THRESHOLD:
                severity = ChangeSeverity.CRITICAL
            elif diff_percentage >= self.VISUAL_HIGH_THRESHOLD:
                severity = ChangeSeverity.HIGH
            elif diff_percentage >= self.VISUAL_MEDIUM_THRESHOLD:
                severity = ChangeSeverity.MEDIUM
            else:
                severity = ChangeSeverity.LOW

            # Generate diff image
            diff_image_path = self._generate_diff_image(
                img_a, img_b, snapshot_a.test_name, snapshot_a.version_id, snapshot_b.version_id
            )

            return VisualChange(
                diff_percentage=diff_percentage,
                diff_image_path=str(diff_image_path) if diff_image_path else None,
                changed_regions=changed_regions,
                severity=severity,
            )

        except Exception as e:
            self._log.warning("Visual comparison failed", error=str(e))
            return None

    def _find_changed_regions(
        self,
        diff_array: Any,  # numpy array
        threshold: float = 0.1,
    ) -> list[BoundingBox]:
        """Find regions with significant changes."""
        try:
            import numpy as np
            from scipy import ndimage
        except ImportError:
            return []

        # Create binary mask of changed pixels
        mask = np.mean(diff_array, axis=2) > threshold

        # Label connected regions
        labeled, num_features = ndimage.label(mask)

        regions: list[BoundingBox] = []
        for i in range(1, num_features + 1):
            region_mask = labeled == i
            rows = np.any(region_mask, axis=1)
            cols = np.any(region_mask, axis=0)
            y_min, y_max = np.where(rows)[0][[0, -1]]
            x_min, x_max = np.where(cols)[0][[0, -1]]

            regions.append(BoundingBox(
                x=int(x_min),
                y=int(y_min),
                width=int(x_max - x_min),
                height=int(y_max - y_min),
            ))

        return regions[:10]  # Limit to 10 regions

    def _generate_diff_image(
        self,
        img_a: Any,  # PIL Image
        img_b: Any,  # PIL Image
        test_name: str,
        version_a: str,
        version_b: str,
    ) -> Path | None:
        """Generate a visual diff image."""
        try:
            from PIL import Image, ImageChops, ImageEnhance

            # Create difference image
            diff = ImageChops.difference(img_a, img_b)

            # Enhance difference for visibility
            enhancer = ImageEnhance.Contrast(diff)
            diff_enhanced = enhancer.enhance(5.0)

            # Create side-by-side comparison
            width = img_a.width
            height = img_a.height
            combined = Image.new("RGB", (width * 3, height))
            combined.paste(img_a, (0, 0))
            combined.paste(img_b, (width, 0))
            combined.paste(diff_enhanced, (width * 2, 0))

            # Save
            safe_name = re.sub(r"[^\w\-_]", "_", test_name)
            filename = f"diff_{safe_name}_{version_a}_vs_{version_b}.png"
            output_path = self._reports_dir / filename
            combined.save(output_path)

            return output_path

        except Exception as e:
            self._log.warning("Failed to generate diff image", error=str(e))
            return None

    def _compare_texts(
        self,
        snapshot_a: TestSnapshot,
        snapshot_b: TestSnapshot,
    ) -> list[TextChange]:
        """Compare extracted text content."""
        changes: list[TextChange] = []

        texts_a = snapshot_a.extracted_texts
        texts_b = snapshot_b.extracted_texts

        all_keys = set(texts_a.keys()) | set(texts_b.keys())

        for key in all_keys:
            old_val = texts_a.get(key)
            new_val = texts_b.get(key)

            if old_val is None and new_val is not None:
                changes.append(TextChange(
                    change_type=ChangeType.ADDED,
                    selector=None,
                    key=key,
                    old_value=None,
                    new_value=new_val,
                    severity=ChangeSeverity.MEDIUM,
                ))
            elif old_val is not None and new_val is None:
                changes.append(TextChange(
                    change_type=ChangeType.REMOVED,
                    selector=None,
                    key=key,
                    old_value=old_val,
                    new_value=None,
                    severity=ChangeSeverity.HIGH,
                ))
            elif old_val != new_val:
                # Calculate similarity to determine severity
                ratio = difflib.SequenceMatcher(None, old_val or "", new_val or "").ratio()
                if ratio < 0.5:
                    severity = ChangeSeverity.HIGH
                elif ratio < 0.8:
                    severity = ChangeSeverity.MEDIUM
                else:
                    severity = ChangeSeverity.LOW

                changes.append(TextChange(
                    change_type=ChangeType.MODIFIED,
                    selector=None,
                    key=key,
                    old_value=old_val,
                    new_value=new_val,
                    severity=severity,
                ))

        # Also compare page title and URL
        if snapshot_a.page_title != snapshot_b.page_title:
            changes.append(TextChange(
                change_type=ChangeType.MODIFIED,
                selector=None,
                key="_page_title",
                old_value=snapshot_a.page_title,
                new_value=snapshot_b.page_title,
                severity=ChangeSeverity.MEDIUM,
            ))

        if snapshot_a.page_url != snapshot_b.page_url:
            changes.append(TextChange(
                change_type=ChangeType.MODIFIED,
                selector=None,
                key="_page_url",
                old_value=snapshot_a.page_url,
                new_value=snapshot_b.page_url,
                severity=ChangeSeverity.HIGH,
            ))

        return changes

    def _compare_elements(
        self,
        snapshot_a: TestSnapshot,
        snapshot_b: TestSnapshot,
    ) -> list[ElementChange]:
        """Compare element states between snapshots."""
        changes: list[ElementChange] = []

        # Index by selector
        elements_a = {e.selector: e for e in snapshot_a.element_states}
        elements_b = {e.selector: e for e in snapshot_b.element_states}

        all_selectors = set(elements_a.keys()) | set(elements_b.keys())

        for selector in all_selectors:
            old_elem = elements_a.get(selector)
            new_elem = elements_b.get(selector)

            if old_elem is None and new_elem is not None:
                changes.append(ElementChange(
                    change_type=ChangeType.ADDED,
                    selector=selector,
                    old_state=None,
                    new_state=new_elem,
                    severity=ChangeSeverity.MEDIUM,
                ))
            elif old_elem is not None and new_elem is None:
                changes.append(ElementChange(
                    change_type=ChangeType.REMOVED,
                    selector=selector,
                    old_state=old_elem,
                    new_state=None,
                    severity=ChangeSeverity.HIGH,
                ))
            elif old_elem is not None and new_elem is not None:
                # Check for modifications
                changed_attrs: list[str] = []
                changed_styles: list[str] = []

                # Compare attributes
                all_attrs = set(old_elem.attributes.keys()) | set(new_elem.attributes.keys())
                for attr in all_attrs:
                    if old_elem.attributes.get(attr) != new_elem.attributes.get(attr):
                        changed_attrs.append(attr)

                # Compare computed styles
                all_styles = set(old_elem.computed_styles.keys()) | set(new_elem.computed_styles.keys())
                for style in all_styles:
                    if old_elem.computed_styles.get(style) != new_elem.computed_styles.get(style):
                        changed_styles.append(style)

                # Compare visibility/enabled state
                visibility_changed = old_elem.is_visible != new_elem.is_visible
                enabled_changed = old_elem.is_enabled != new_elem.is_enabled

                if changed_attrs or changed_styles or visibility_changed or enabled_changed:
                    # Determine severity
                    if visibility_changed or enabled_changed:
                        severity = ChangeSeverity.HIGH
                    elif len(changed_attrs) > 3 or len(changed_styles) > 5:
                        severity = ChangeSeverity.MEDIUM
                    else:
                        severity = ChangeSeverity.LOW

                    changes.append(ElementChange(
                        change_type=ChangeType.MODIFIED,
                        selector=selector,
                        old_state=old_elem,
                        new_state=new_elem,
                        changed_attributes=changed_attrs,
                        changed_styles=changed_styles,
                        severity=severity,
                    ))

        return changes

    def _compare_layouts(
        self,
        snapshot_a: TestSnapshot,
        snapshot_b: TestSnapshot,
    ) -> list[LayoutChange]:
        """Compare element positions between snapshots."""
        changes: list[LayoutChange] = []

        # Index by selector
        elements_a = {e.selector: e for e in snapshot_a.element_states if e.bounding_box}
        elements_b = {e.selector: e for e in snapshot_b.element_states if e.bounding_box}

        common_selectors = set(elements_a.keys()) & set(elements_b.keys())

        for selector in common_selectors:
            old_elem = elements_a[selector]
            new_elem = elements_b[selector]

            if old_elem.bounding_box and new_elem.bounding_box:
                old_box = old_elem.bounding_box
                new_box = new_elem.bounding_box

                shift_x = new_box.x - old_box.x
                shift_y = new_box.y - old_box.y
                shift_distance = (shift_x ** 2 + shift_y ** 2) ** 0.5

                # Also check size changes
                size_changed = (
                    old_box.width != new_box.width or
                    old_box.height != new_box.height
                )

                if shift_distance > 5 or size_changed:  # Threshold: 5px
                    # Determine severity
                    if shift_distance >= self.LAYOUT_CRITICAL_SHIFT:
                        severity = ChangeSeverity.CRITICAL
                    elif shift_distance >= self.LAYOUT_HIGH_SHIFT:
                        severity = ChangeSeverity.HIGH
                    elif shift_distance >= self.LAYOUT_MEDIUM_SHIFT:
                        severity = ChangeSeverity.MEDIUM
                    else:
                        severity = ChangeSeverity.LOW

                    changes.append(LayoutChange(
                        selector=selector,
                        old_position=old_box,
                        new_position=new_box,
                        shift_x=shift_x,
                        shift_y=shift_y,
                        shift_distance=shift_distance,
                        severity=severity,
                    ))

        return changes

    def _compare_network(
        self,
        snapshot_a: TestSnapshot,
        snapshot_b: TestSnapshot,
    ) -> list[NetworkChange]:
        """Compare network requests between snapshots."""
        changes: list[NetworkChange] = []

        # Group requests by URL pattern (normalize)
        def normalize_url(url: str) -> str:
            parsed = urlparse(url)
            # Remove query params for comparison
            return f"{parsed.scheme}://{parsed.netloc}{parsed.path}"

        requests_a: dict[str, list[NetworkRequest]] = {}
        for req in snapshot_a.network_requests:
            key = normalize_url(req.url)
            requests_a.setdefault(key, []).append(req)

        requests_b: dict[str, list[NetworkRequest]] = {}
        for req in snapshot_b.network_requests:
            key = normalize_url(req.url)
            requests_b.setdefault(key, []).append(req)

        all_urls = set(requests_a.keys()) | set(requests_b.keys())

        for url_pattern in all_urls:
            old_reqs = requests_a.get(url_pattern, [])
            new_reqs = requests_b.get(url_pattern, [])

            if not old_reqs and new_reqs:
                # New request
                changes.append(NetworkChange(
                    change_type=ChangeType.ADDED,
                    url_pattern=url_pattern,
                    old_request=None,
                    new_request=new_reqs[0],
                    severity=ChangeSeverity.MEDIUM,
                ))
            elif old_reqs and not new_reqs:
                # Removed request
                changes.append(NetworkChange(
                    change_type=ChangeType.REMOVED,
                    url_pattern=url_pattern,
                    old_request=old_reqs[0],
                    new_request=None,
                    severity=ChangeSeverity.HIGH,
                ))
            elif old_reqs and new_reqs:
                # Compare first request of each
                old_req = old_reqs[0]
                new_req = new_reqs[0]

                status_changed = old_req.status_code != new_req.status_code
                response_time_changed = False

                if old_req.response_time_ms and new_req.response_time_ms:
                    time_diff = abs(old_req.response_time_ms - new_req.response_time_ms)
                    response_time_changed = time_diff > 500  # 500ms threshold

                if status_changed or response_time_changed:
                    # Determine severity
                    if status_changed:
                        old_status = old_req.status_code or 0
                        new_status = new_req.status_code or 0
                        if (old_status < 400 <= new_status) or (new_status < 400 <= old_status):
                            severity = ChangeSeverity.CRITICAL
                        else:
                            severity = ChangeSeverity.HIGH
                    else:
                        severity = ChangeSeverity.LOW

                    changes.append(NetworkChange(
                        change_type=ChangeType.MODIFIED,
                        url_pattern=url_pattern,
                        old_request=old_req,
                        new_request=new_req,
                        status_code_changed=status_changed,
                        response_time_changed=response_time_changed,
                        severity=severity,
                    ))

        return changes

    def _calculate_summary(self, diff: VersionDiff) -> None:
        """Calculate summary metrics for the diff."""
        all_severities: list[ChangeSeverity] = []

        if diff.visual_changes:
            all_severities.append(diff.visual_changes.severity)

        for tc in diff.text_changes:
            all_severities.append(tc.severity)

        for ec in diff.element_changes:
            all_severities.append(ec.severity)

        for lc in diff.layout_changes:
            all_severities.append(lc.severity)

        for nc in diff.network_changes:
            all_severities.append(nc.severity)

        diff.total_changes = len(all_severities)
        diff.critical_changes = sum(1 for s in all_severities if s == ChangeSeverity.CRITICAL)
        diff.high_changes = sum(1 for s in all_severities if s == ChangeSeverity.HIGH)
        diff.medium_changes = sum(1 for s in all_severities if s == ChangeSeverity.MEDIUM)
        diff.low_changes = sum(1 for s in all_severities if s == ChangeSeverity.LOW)

    def _render_html_report(self, diff: VersionDiff) -> str:
        """Render HTML report for a diff."""
        # CSS styles
        css = """
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; }
        h1 { color: #333; border-bottom: 2px solid #007bff; padding-bottom: 10px; }
        h2 { color: #555; margin-top: 30px; }
        .summary { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 20px; }
        .summary-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px; margin-top: 15px; }
        .metric { text-align: center; padding: 15px; border-radius: 8px; }
        .metric-value { font-size: 2em; font-weight: bold; }
        .metric-label { color: #666; font-size: 0.9em; }
        .critical { background: #ffebee; color: #c62828; }
        .high { background: #fff3e0; color: #ef6c00; }
        .medium { background: #fff8e1; color: #f9a825; }
        .low { background: #e8f5e9; color: #2e7d32; }
        .change-list { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .change-item { border-bottom: 1px solid #eee; padding: 15px 0; }
        .change-item:last-child { border-bottom: none; }
        .change-type { display: inline-block; padding: 3px 8px; border-radius: 4px; font-size: 0.85em; font-weight: bold; margin-right: 10px; }
        .added { background: #e8f5e9; color: #2e7d32; }
        .removed { background: #ffebee; color: #c62828; }
        .modified { background: #e3f2fd; color: #1565c0; }
        .moved { background: #f3e5f5; color: #7b1fa2; }
        .severity-badge { display: inline-block; padding: 2px 6px; border-radius: 3px; font-size: 0.75em; margin-left: 5px; }
        code { background: #f5f5f5; padding: 2px 6px; border-radius: 3px; font-family: 'Monaco', 'Consolas', monospace; }
        .old-value { background: #ffebee; text-decoration: line-through; }
        .new-value { background: #e8f5e9; }
        .diff-image { max-width: 100%; border-radius: 8px; margin-top: 15px; }
        .timestamps { color: #666; font-size: 0.9em; margin-bottom: 20px; }
        """

        # Build HTML
        html_parts = [
            "<!DOCTYPE html>",
            "<html lang='en'>",
            "<head>",
            "<meta charset='UTF-8'>",
            "<meta name='viewport' content='width=device-width, initial-scale=1.0'>",
            f"<title>Diff Report: {diff.snapshot_a.test_name}</title>",
            f"<style>{css}</style>",
            "</head>",
            "<body>",
            "<div class='container'>",
            f"<h1>Version Diff Report: {diff.snapshot_a.test_name}</h1>",
            "<div class='timestamps'>",
            f"<strong>From:</strong> {diff.snapshot_a.timestamp.strftime('%Y-%m-%d %H:%M:%S')} ({diff.snapshot_a.version_id})<br>",
            f"<strong>To:</strong> {diff.snapshot_b.timestamp.strftime('%Y-%m-%d %H:%M:%S')} ({diff.snapshot_b.version_id})<br>",
            f"<strong>Generated:</strong> {diff.generated_at.strftime('%Y-%m-%d %H:%M:%S')}",
            "</div>",
        ]

        # Summary section
        html_parts.extend([
            "<div class='summary'>",
            "<h2>Summary</h2>",
            "<div class='summary-grid'>",
            f"<div class='metric'><div class='metric-value'>{diff.total_changes}</div><div class='metric-label'>Total Changes</div></div>",
            f"<div class='metric critical'><div class='metric-value'>{diff.critical_changes}</div><div class='metric-label'>Critical</div></div>",
            f"<div class='metric high'><div class='metric-value'>{diff.high_changes}</div><div class='metric-label'>High</div></div>",
            f"<div class='metric medium'><div class='metric-value'>{diff.medium_changes}</div><div class='metric-label'>Medium</div></div>",
            f"<div class='metric low'><div class='metric-value'>{diff.low_changes}</div><div class='metric-label'>Low</div></div>",
            "</div>",
            "</div>",
        ])

        # Visual changes
        if diff.visual_changes:
            vc = diff.visual_changes
            html_parts.extend([
                "<div class='change-list'>",
                "<h2>Visual Changes</h2>",
                f"<p>Difference: <strong>{vc.diff_percentage:.2%}</strong> ",
                f"<span class='severity-badge {vc.severity}'>{vc.severity}</span></p>",
            ])
            if vc.diff_image_path:
                html_parts.append(f"<img src='{vc.diff_image_path}' alt='Visual diff' class='diff-image'>")
            html_parts.append("</div>")

        # Text changes
        if diff.text_changes:
            html_parts.extend([
                "<div class='change-list'>",
                "<h2>Text Changes</h2>",
            ])
            for tc in diff.text_changes:
                html_parts.append("<div class='change-item'>")
                html_parts.append(f"<span class='change-type {tc.change_type}'>{tc.change_type}</span>")
                html_parts.append(f"<code>{tc.key or tc.selector}</code>")
                html_parts.append(f"<span class='severity-badge {tc.severity}'>{tc.severity}</span>")
                if tc.old_value:
                    html_parts.append(f"<br><span class='old-value'>{tc.old_value[:100]}{'...' if len(tc.old_value or '') > 100 else ''}</span>")
                if tc.new_value:
                    html_parts.append(f"<br><span class='new-value'>{tc.new_value[:100]}{'...' if len(tc.new_value or '') > 100 else ''}</span>")
                html_parts.append("</div>")
            html_parts.append("</div>")

        # Element changes
        if diff.element_changes:
            html_parts.extend([
                "<div class='change-list'>",
                "<h2>Element Changes</h2>",
            ])
            for ec in diff.element_changes:
                html_parts.append("<div class='change-item'>")
                html_parts.append(f"<span class='change-type {ec.change_type}'>{ec.change_type}</span>")
                html_parts.append(f"<code>{ec.selector}</code>")
                html_parts.append(f"<span class='severity-badge {ec.severity}'>{ec.severity}</span>")
                if ec.changed_attributes:
                    html_parts.append(f"<br>Changed attributes: {', '.join(ec.changed_attributes)}")
                if ec.changed_styles:
                    html_parts.append(f"<br>Changed styles: {', '.join(ec.changed_styles[:5])}{'...' if len(ec.changed_styles) > 5 else ''}")
                html_parts.append("</div>")
            html_parts.append("</div>")

        # Layout changes
        if diff.layout_changes:
            html_parts.extend([
                "<div class='change-list'>",
                "<h2>Layout Changes</h2>",
            ])
            for lc in diff.layout_changes:
                html_parts.append("<div class='change-item'>")
                html_parts.append("<span class='change-type moved'>shifted</span>")
                html_parts.append(f"<code>{lc.selector}</code>")
                html_parts.append(f"<span class='severity-badge {lc.severity}'>{lc.severity}</span>")
                html_parts.append(f"<br>Shift: ({lc.shift_x}px, {lc.shift_y}px) = {lc.shift_distance:.1f}px")
                html_parts.append("</div>")
            html_parts.append("</div>")

        # Network changes
        if diff.network_changes:
            html_parts.extend([
                "<div class='change-list'>",
                "<h2>Network Changes</h2>",
            ])
            for nc in diff.network_changes:
                html_parts.append("<div class='change-item'>")
                html_parts.append(f"<span class='change-type {nc.change_type}'>{nc.change_type}</span>")
                html_parts.append(f"<code>{nc.url_pattern[:80]}{'...' if len(nc.url_pattern) > 80 else ''}</code>")
                html_parts.append(f"<span class='severity-badge {nc.severity}'>{nc.severity}</span>")
                if nc.status_code_changed:
                    old_status = nc.old_request.status_code if nc.old_request else "N/A"
                    new_status = nc.new_request.status_code if nc.new_request else "N/A"
                    html_parts.append(f"<br>Status: {old_status} -> {new_status}")
                html_parts.append("</div>")
            html_parts.append("</div>")

        html_parts.extend([
            "</div>",
            "</body>",
            "</html>",
        ])

        return "\n".join(html_parts)
