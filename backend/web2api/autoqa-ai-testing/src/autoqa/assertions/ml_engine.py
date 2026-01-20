"""
ML-based UI assertion engine for visual testing without LLM dependencies.

Provides machine learning and computer vision-based assertions:
- OCR text extraction and validation (pytesseract/easyocr)
- Image classification for UI state detection
- Object detection for element verification
- Color analysis (dominant colors, distribution)
- Layout analysis (element positions, alignment)
- Icon/logo matching using feature detection (SIFT/ORB)
- Form field detection
- Accessibility checks (contrast ratios, font sizes)
- Screenshot diff with region-based analysis
"""

from __future__ import annotations

import colorsys
import io
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any, Literal

import cv2
import numpy as np
import structlog
from PIL import Image
from sklearn.cluster import KMeans

logger = structlog.get_logger(__name__)

# Type aliases for clarity
type ImageInput = bytes | str | Path | Image.Image | np.ndarray[Any, np.dtype[np.uint8]]
type BoundingBox = tuple[int, int, int, int]  # x, y, width, height


class UIState(StrEnum):
    """Detected UI states for classification."""

    LOADING = "loading"
    ERROR = "error"
    SUCCESS = "success"
    EMPTY = "empty"
    NORMAL = "normal"


class AlignmentType(StrEnum):
    """Types of element alignment."""

    LEFT = "left"
    RIGHT = "right"
    CENTER = "center"
    TOP = "top"
    BOTTOM = "bottom"
    VERTICAL_CENTER = "vertical_center"


@dataclass(frozen=True, slots=True)
class OCRResult:
    """Result of OCR text extraction."""

    text: str
    confidence: float
    bounding_box: BoundingBox | None = None
    word_confidences: tuple[tuple[str, float], ...] = ()


@dataclass(frozen=True, slots=True)
class ColorInfo:
    """Information about a detected color."""

    rgb: tuple[int, int, int]
    hex_code: str
    percentage: float
    name: str | None = None

    @classmethod
    def from_rgb(cls, rgb: tuple[int, int, int], percentage: float) -> ColorInfo:
        """Create ColorInfo from RGB values."""
        hex_code = f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"
        name = cls._approximate_color_name(rgb)
        return cls(rgb=rgb, hex_code=hex_code, percentage=percentage, name=name)

    @staticmethod
    def _approximate_color_name(rgb: tuple[int, int, int]) -> str:
        """Approximate human-readable color name from RGB."""
        r, g, b = rgb
        h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
        h_deg = h * 360

        if v < 0.1:
            return "black"
        if v > 0.9 and s < 0.1:
            return "white"
        if s < 0.1:
            return "gray"
        if h_deg < 15 or h_deg >= 345:
            return "red"
        if 15 <= h_deg < 45:
            return "orange"
        if 45 <= h_deg < 75:
            return "yellow"
        if 75 <= h_deg < 165:
            return "green"
        if 165 <= h_deg < 195:
            return "cyan"
        if 195 <= h_deg < 255:
            return "blue"
        if 255 <= h_deg < 285:
            return "purple"
        return "magenta"


@dataclass(frozen=True, slots=True)
class DetectedElement:
    """A detected UI element."""

    element_type: str
    bounding_box: BoundingBox
    confidence: float
    attributes: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class LayoutInfo:
    """Layout analysis information."""

    elements: tuple[DetectedElement, ...]
    grid_structure: tuple[int, int] | None = None  # rows, cols
    alignment_score: float = 0.0
    symmetry_score: float = 0.0


@dataclass(frozen=True, slots=True)
class IconMatchResult:
    """Result of icon/logo matching."""

    matched: bool
    confidence: float
    location: BoundingBox | None = None
    matches_count: int = 0


@dataclass(frozen=True, slots=True)
class ContrastResult:
    """Result of contrast ratio calculation."""

    ratio: float
    passes_aa: bool  # WCAG AA (4.5:1 for normal text)
    passes_aaa: bool  # WCAG AAA (7:1 for normal text)
    foreground_color: tuple[int, int, int]
    background_color: tuple[int, int, int]


@dataclass
class MLAssertionResult:
    """Result of an ML-based assertion."""

    passed: bool
    message: str
    actual: Any = None
    expected: Any = None
    confidence: float = 1.0
    details: dict[str, Any] = field(default_factory=dict)


class ImageLoader:
    """Utility class for loading images from various sources."""

    @staticmethod
    def to_pil(image: ImageInput) -> Image.Image:
        """Convert various image formats to PIL Image."""
        if isinstance(image, Image.Image):
            return image.convert("RGB")
        if isinstance(image, np.ndarray):
            return Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        if isinstance(image, bytes):
            return Image.open(io.BytesIO(image)).convert("RGB")
        if isinstance(image, (str, Path)):
            return Image.open(image).convert("RGB")
        msg = f"Unsupported image type: {type(image)}"
        raise TypeError(msg)

    @staticmethod
    def to_cv2(image: ImageInput) -> np.ndarray[Any, np.dtype[np.uint8]]:
        """Convert various image formats to OpenCV BGR array."""
        if isinstance(image, np.ndarray):
            if len(image.shape) == 2:  # Grayscale
                return cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
            return image
        pil_img = ImageLoader.to_pil(image)
        return cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

    @staticmethod
    def to_grayscale(image: ImageInput) -> np.ndarray[Any, np.dtype[np.uint8]]:
        """Convert image to grayscale numpy array."""
        cv2_img = ImageLoader.to_cv2(image)
        return cv2.cvtColor(cv2_img, cv2.COLOR_BGR2GRAY)


class BaseMLAssertion(ABC):
    """Abstract base class for ML-based assertions."""

    def __init__(self) -> None:
        self._log = logger.bind(component=self.__class__.__name__)

    @abstractmethod
    def validate(self, image: ImageInput, **kwargs: Any) -> MLAssertionResult:
        """Execute the assertion against the provided image."""
        ...


class OCRAssertion(BaseMLAssertion):
    """
    OCR-based text assertions using pytesseract or easyocr.

    Extracts text from images and validates against expected values.
    """

    def __init__(
        self,
        backend: Literal["pytesseract", "easyocr"] = "easyocr",
        languages: list[str] | None = None,
    ) -> None:
        super().__init__()
        self._backend = backend
        self._languages = languages or ["en"]
        self._reader: Any = None

    def _get_reader(self) -> Any:
        """Lazy-load the OCR reader."""
        if self._reader is None:
            if self._backend == "easyocr":
                import easyocr

                self._reader = easyocr.Reader(self._languages, gpu=False)
            # For pytesseract, no reader initialization needed
        return self._reader

    def extract_text(
        self,
        image: ImageInput,
        region: BoundingBox | None = None,
    ) -> OCRResult:
        """
        Extract text from image using OCR.

        Args:
            image: Input image
            region: Optional region to extract from (x, y, width, height)

        Returns:
            OCRResult with extracted text and confidence
        """
        pil_img = ImageLoader.to_pil(image)

        if region:
            x, y, w, h = region
            pil_img = pil_img.crop((x, y, x + w, y + h))

        if self._backend == "easyocr":
            return self._extract_easyocr(pil_img)
        return self._extract_pytesseract(pil_img)

    def _extract_easyocr(self, image: Image.Image) -> OCRResult:
        """Extract text using EasyOCR."""
        reader = self._get_reader()
        img_array = np.array(image)

        results = reader.readtext(img_array, detail=1)

        if not results:
            return OCRResult(text="", confidence=0.0)

        texts = []
        word_confidences = []
        total_conf = 0.0

        for _bbox, text, conf in results:
            texts.append(text)
            word_confidences.append((text, conf))
            total_conf += conf

        full_text = " ".join(texts)
        avg_confidence = total_conf / len(results) if results else 0.0

        return OCRResult(
            text=full_text,
            confidence=avg_confidence,
            word_confidences=tuple(word_confidences),
        )

    def _extract_pytesseract(self, image: Image.Image) -> OCRResult:
        """Extract text using pytesseract."""
        import pytesseract

        data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)

        texts = []
        word_confidences = []
        total_conf = 0.0
        word_count = 0

        for i, text in enumerate(data["text"]):
            if text.strip():
                conf = float(data["conf"][i])
                if conf > 0:  # pytesseract returns -1 for non-text
                    texts.append(text)
                    word_confidences.append((text, conf / 100.0))
                    total_conf += conf / 100.0
                    word_count += 1

        full_text = " ".join(texts)
        avg_confidence = total_conf / word_count if word_count > 0 else 0.0

        return OCRResult(
            text=full_text,
            confidence=avg_confidence,
            word_confidences=tuple(word_confidences),
        )

    def validate(
        self,
        image: ImageInput,
        *,
        expected_text: str | None = None,
        contains: str | None = None,
        min_confidence: float = 0.5,
        region: BoundingBox | None = None,
        **kwargs: Any,
    ) -> MLAssertionResult:
        """
        Validate OCR text extraction.

        Args:
            image: Input image
            expected_text: Exact text expected (equals comparison)
            contains: Text that should be contained in result
            min_confidence: Minimum confidence threshold
            region: Optional region to limit OCR

        Returns:
            MLAssertionResult with validation outcome
        """
        result = self.extract_text(image, region=region)

        if result.confidence < min_confidence:
            return MLAssertionResult(
                passed=False,
                message=f"OCR confidence {result.confidence:.2%} below threshold {min_confidence:.2%}",
                actual=result.text,
                expected=expected_text or contains,
                confidence=result.confidence,
                details={"word_confidences": result.word_confidences},
            )

        if expected_text is not None:
            normalized_expected = expected_text.strip().lower()
            normalized_actual = result.text.strip().lower()
            passed = normalized_actual == normalized_expected

            return MLAssertionResult(
                passed=passed,
                message="OCR text equals expected" if passed else "OCR text mismatch",
                actual=result.text,
                expected=expected_text,
                confidence=result.confidence,
                details={"word_confidences": result.word_confidences},
            )

        if contains is not None:
            normalized_contains = contains.strip().lower()
            normalized_actual = result.text.strip().lower()
            passed = normalized_contains in normalized_actual

            return MLAssertionResult(
                passed=passed,
                message="OCR text contains expected" if passed else "OCR text does not contain expected",
                actual=result.text,
                expected=contains,
                confidence=result.confidence,
                details={"word_confidences": result.word_confidences},
            )

        # Just extraction without specific assertion
        return MLAssertionResult(
            passed=True,
            message="OCR text extracted successfully",
            actual=result.text,
            confidence=result.confidence,
            details={"word_confidences": result.word_confidences},
        )


class ImageClassifier(BaseMLAssertion):
    """
    Image classification for UI state detection.

    Uses visual features to classify UI states:
    - Loading (spinners, progress bars)
    - Error (red colors, error icons)
    - Success (green colors, checkmarks)
    - Empty (minimal content, placeholder text)
    """

    # Color ranges for state detection (HSV)
    ERROR_HUE_RANGE = (0, 10, 170, 180)  # Red hues
    SUCCESS_HUE_RANGE = (35, 85)  # Green hues
    WARNING_HUE_RANGE = (15, 35)  # Orange/yellow hues

    def __init__(self) -> None:
        super().__init__()

    def classify_state(self, image: ImageInput) -> tuple[UIState, float]:
        """
        Classify the UI state of an image.

        Returns:
            Tuple of (detected state, confidence)
        """
        cv2_img = ImageLoader.to_cv2(image)
        hsv = cv2.cvtColor(cv2_img, cv2.COLOR_BGR2HSV)

        # Analyze color distribution
        state_scores: dict[UIState, float] = {
            UIState.ERROR: self._score_error_state(hsv, cv2_img),
            UIState.SUCCESS: self._score_success_state(hsv),
            UIState.LOADING: self._score_loading_state(cv2_img),
            UIState.EMPTY: self._score_empty_state(cv2_img),
        }

        # Get best match
        best_state = max(state_scores, key=lambda k: state_scores[k])
        best_score = state_scores[best_state]

        # Default to NORMAL if no strong signals
        if best_score < 0.3:
            return UIState.NORMAL, 1.0 - best_score

        return best_state, best_score

    def _score_error_state(
        self,
        hsv: np.ndarray[Any, np.dtype[np.uint8]],
        bgr: np.ndarray[Any, np.dtype[np.uint8]],
    ) -> float:
        """Score likelihood of error state based on red colors."""
        # Red wraps around in HSV, so check two ranges
        lower_red1 = np.array([0, 100, 100])
        upper_red1 = np.array([10, 255, 255])
        lower_red2 = np.array([170, 100, 100])
        upper_red2 = np.array([180, 255, 255])

        mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
        mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
        red_mask = cv2.bitwise_or(mask1, mask2)

        red_ratio = np.sum(red_mask > 0) / red_mask.size
        return min(red_ratio * 10, 1.0)  # Scale up small red areas

    def _score_success_state(self, hsv: np.ndarray[Any, np.dtype[np.uint8]]) -> float:
        """Score likelihood of success state based on green colors."""
        lower_green = np.array([35, 100, 100])
        upper_green = np.array([85, 255, 255])

        green_mask = cv2.inRange(hsv, lower_green, upper_green)
        green_ratio = np.sum(green_mask > 0) / green_mask.size

        return min(green_ratio * 10, 1.0)

    def _score_loading_state(self, bgr: np.ndarray[Any, np.dtype[np.uint8]]) -> float:
        """Score likelihood of loading state using circular detection."""
        gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)

        # Detect circles (spinners often contain circular elements)
        circles = cv2.HoughCircles(
            gray,
            cv2.HOUGH_GRADIENT,
            dp=1,
            minDist=20,
            param1=50,
            param2=30,
            minRadius=10,
            maxRadius=100,
        )

        if circles is not None:
            circle_count = len(circles[0])
            return min(circle_count * 0.3, 1.0)

        return 0.0

    def _score_empty_state(self, bgr: np.ndarray[Any, np.dtype[np.uint8]]) -> float:
        """Score likelihood of empty state based on content sparsity."""
        gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)

        # Calculate edge density (empty states have fewer edges)
        edges = cv2.Canny(gray, 50, 150)
        edge_ratio = np.sum(edges > 0) / edges.size

        # Low edge density suggests empty state
        if edge_ratio < 0.02:
            return 0.8
        if edge_ratio < 0.05:
            return 0.5

        return 0.0

    def validate(
        self,
        image: ImageInput,
        *,
        expected_state: UIState | str | None = None,
        min_confidence: float = 0.5,
        **kwargs: Any,
    ) -> MLAssertionResult:
        """
        Validate UI state classification.

        Args:
            image: Input image
            expected_state: Expected UI state
            min_confidence: Minimum confidence threshold

        Returns:
            MLAssertionResult with classification outcome
        """
        detected_state, confidence = self.classify_state(image)

        if expected_state is not None:
            expected = UIState(expected_state) if isinstance(expected_state, str) else expected_state
            passed = detected_state == expected and confidence >= min_confidence

            return MLAssertionResult(
                passed=passed,
                message=f"UI state is {detected_state.value}" if passed else f"Expected {expected.value}, got {detected_state.value}",
                actual=detected_state.value,
                expected=expected.value,
                confidence=confidence,
                details={"detected_state": detected_state.value},
            )

        return MLAssertionResult(
            passed=True,
            message=f"Detected UI state: {detected_state.value}",
            actual=detected_state.value,
            confidence=confidence,
            details={"detected_state": detected_state.value},
        )


class ColorAnalyzer(BaseMLAssertion):
    """
    Color analysis for UI validation.

    Provides:
    - Dominant color detection using K-means clustering
    - Color distribution analysis
    - Specific color presence checking
    """

    def __init__(self, n_colors: int = 5) -> None:
        super().__init__()
        self._n_colors = n_colors

    def get_dominant_colors(
        self,
        image: ImageInput,
        n_colors: int | None = None,
    ) -> list[ColorInfo]:
        """
        Extract dominant colors from image using K-means clustering.

        Args:
            image: Input image
            n_colors: Number of dominant colors to extract

        Returns:
            List of ColorInfo sorted by dominance (percentage)
        """
        pil_img = ImageLoader.to_pil(image)
        img_array = np.array(pil_img)

        # Reshape to list of pixels
        pixels = img_array.reshape(-1, 3)

        # Use K-means clustering
        n = n_colors or self._n_colors
        kmeans = KMeans(n_clusters=n, random_state=42, n_init=10)
        kmeans.fit(pixels)

        # Get cluster centers and counts
        colors = kmeans.cluster_centers_.astype(int)
        labels = kmeans.labels_
        counts = np.bincount(labels)

        # Calculate percentages
        total = len(labels)
        color_info_list = []

        for color, count in zip(colors, counts, strict=False):
            percentage = count / total
            rgb = (int(color[0]), int(color[1]), int(color[2]))
            color_info_list.append(ColorInfo.from_rgb(rgb, percentage))

        # Sort by percentage descending
        color_info_list.sort(key=lambda c: c.percentage, reverse=True)
        return color_info_list

    def has_color(
        self,
        image: ImageInput,
        target_color: tuple[int, int, int] | str,
        tolerance: int = 30,
        min_percentage: float = 0.01,
    ) -> tuple[bool, float]:
        """
        Check if image contains a specific color.

        Args:
            image: Input image
            target_color: RGB tuple or hex string
            tolerance: Color matching tolerance (0-255)
            min_percentage: Minimum percentage of pixels needed

        Returns:
            Tuple of (found, percentage)
        """
        if isinstance(target_color, str):
            # Parse hex color
            hex_val = target_color.lstrip("#")
            target_rgb = tuple(int(hex_val[i : i + 2], 16) for i in (0, 2, 4))
        else:
            target_rgb = target_color

        cv2_img = ImageLoader.to_cv2(image)
        rgb_img = cv2.cvtColor(cv2_img, cv2.COLOR_BGR2RGB)

        # Calculate distance from target color
        target_array = np.array(target_rgb, dtype=np.float32)
        diff = np.abs(rgb_img.astype(np.float32) - target_array)
        distance = np.sqrt(np.sum(diff**2, axis=2))

        # Count pixels within tolerance
        matching = distance <= tolerance
        percentage = np.sum(matching) / matching.size

        return percentage >= min_percentage, float(percentage)

    def validate(
        self,
        image: ImageInput,
        *,
        dominant_color: tuple[int, int, int] | str | None = None,
        has_color: tuple[int, int, int] | str | None = None,
        color_tolerance: int = 30,
        min_percentage: float = 0.01,
        **kwargs: Any,
    ) -> MLAssertionResult:
        """
        Validate color properties of an image.

        Args:
            image: Input image
            dominant_color: Expected dominant color (RGB or hex)
            has_color: Color that should be present
            color_tolerance: Tolerance for color matching
            min_percentage: Minimum percentage for has_color check

        Returns:
            MLAssertionResult with color analysis outcome
        """
        if dominant_color is not None:
            colors = self.get_dominant_colors(image, n_colors=1)
            if not colors:
                return MLAssertionResult(
                    passed=False,
                    message="Failed to extract dominant color",
                    actual=None,
                    expected=dominant_color,
                )

            actual = colors[0]

            if isinstance(dominant_color, str):
                # Check if similar
                passed, _ = self.has_color(image, dominant_color, tolerance=color_tolerance, min_percentage=0.1)
            else:
                passed, _ = self.has_color(image, dominant_color, tolerance=color_tolerance, min_percentage=0.1)

            return MLAssertionResult(
                passed=passed,
                message="Dominant color matches" if passed else "Dominant color mismatch",
                actual=actual.hex_code,
                expected=dominant_color if isinstance(dominant_color, str) else f"#{dominant_color[0]:02x}{dominant_color[1]:02x}{dominant_color[2]:02x}",
                confidence=actual.percentage,
                details={"top_colors": [{"hex": c.hex_code, "percentage": c.percentage, "name": c.name} for c in self.get_dominant_colors(image)]},
            )

        if has_color is not None:
            found, percentage = self.has_color(image, has_color, tolerance=color_tolerance, min_percentage=min_percentage)

            return MLAssertionResult(
                passed=found,
                message=f"Color found ({percentage:.2%} of image)" if found else "Color not found in image",
                actual=f"{percentage:.2%}",
                expected=f">= {min_percentage:.2%}",
                confidence=percentage,
                details={"color": has_color, "percentage": percentage},
            )

        # Default: return dominant colors
        colors = self.get_dominant_colors(image)
        return MLAssertionResult(
            passed=True,
            message="Color analysis complete",
            actual=[c.hex_code for c in colors],
            confidence=colors[0].percentage if colors else 0.0,
            details={"colors": [{"hex": c.hex_code, "percentage": c.percentage, "name": c.name} for c in colors]},
        )


class LayoutAnalyzer(BaseMLAssertion):
    """
    Layout analysis for UI structure validation.

    Provides:
    - Element position detection using contours
    - Alignment verification
    - Element counting
    - Grid structure detection
    """

    def __init__(self) -> None:
        super().__init__()

    def detect_elements(
        self,
        image: ImageInput,
        min_area: int = 100,
        max_area: int | None = None,
    ) -> list[DetectedElement]:
        """
        Detect UI elements in image using contour detection.

        Args:
            image: Input image
            min_area: Minimum element area in pixels
            max_area: Maximum element area (None = no limit)

        Returns:
            List of detected elements with bounding boxes
        """
        cv2_img = ImageLoader.to_cv2(image)
        gray = cv2.cvtColor(cv2_img, cv2.COLOR_BGR2GRAY)

        # Apply edge detection
        edges = cv2.Canny(gray, 50, 150)

        # Dilate to connect nearby edges
        kernel = np.ones((3, 3), np.uint8)
        dilated = cv2.dilate(edges, kernel, iterations=2)

        # Find contours
        contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        elements = []
        image_area = cv2_img.shape[0] * cv2_img.shape[1]
        effective_max_area = max_area or (image_area * 0.9)

        for contour in contours:
            area = cv2.contourArea(contour)
            if min_area <= area <= effective_max_area:
                x, y, w, h = cv2.boundingRect(contour)

                # Classify element type based on aspect ratio and size
                aspect_ratio = w / h if h > 0 else 0
                element_type = self._classify_element(aspect_ratio, area, image_area)

                elements.append(
                    DetectedElement(
                        element_type=element_type,
                        bounding_box=(x, y, w, h),
                        confidence=0.8,  # Base confidence for contour detection
                        attributes={"area": area, "aspect_ratio": aspect_ratio},
                    )
                )

        return elements

    def _classify_element(
        self,
        aspect_ratio: float,
        area: int,
        image_area: int,
    ) -> str:
        """Classify element type based on visual properties."""
        relative_size = area / image_area

        if 0.8 <= aspect_ratio <= 1.2 and relative_size < 0.01:
            return "icon"
        if aspect_ratio > 3 and relative_size < 0.05:
            return "button"
        if aspect_ratio > 5:
            return "input_field"
        if relative_size > 0.3:
            return "container"
        if relative_size < 0.001:
            return "dot"

        return "element"

    def check_alignment(
        self,
        elements: list[DetectedElement],
        alignment: AlignmentType,
        tolerance: int = 10,
    ) -> tuple[bool, float]:
        """
        Check if elements are aligned.

        Args:
            elements: List of detected elements
            alignment: Type of alignment to check
            tolerance: Pixel tolerance for alignment

        Returns:
            Tuple of (aligned, score)
        """
        if len(elements) < 2:
            return True, 1.0

        positions = []
        for elem in elements:
            x, y, w, h = elem.bounding_box
            match alignment:
                case AlignmentType.LEFT:
                    positions.append(x)
                case AlignmentType.RIGHT:
                    positions.append(x + w)
                case AlignmentType.CENTER:
                    positions.append(x + w // 2)
                case AlignmentType.TOP:
                    positions.append(y)
                case AlignmentType.BOTTOM:
                    positions.append(y + h)
                case AlignmentType.VERTICAL_CENTER:
                    positions.append(y + h // 2)

        # Calculate standard deviation
        std_dev = np.std(positions)
        aligned = std_dev <= tolerance
        score = max(0, 1 - (std_dev / tolerance)) if tolerance > 0 else float(aligned)

        return aligned, float(score)

    def count_elements(
        self,
        image: ImageInput,
        element_type: str | None = None,
        min_area: int = 100,
    ) -> int:
        """
        Count elements in image.

        Args:
            image: Input image
            element_type: Optional type filter
            min_area: Minimum element area

        Returns:
            Count of matching elements
        """
        elements = self.detect_elements(image, min_area=min_area)

        if element_type is not None:
            elements = [e for e in elements if e.element_type == element_type]

        return len(elements)

    def validate(
        self,
        image: ImageInput,
        *,
        expected_count: int | None = None,
        min_count: int | None = None,
        max_count: int | None = None,
        alignment: AlignmentType | str | None = None,
        element_type: str | None = None,
        alignment_tolerance: int = 10,
        **kwargs: Any,
    ) -> MLAssertionResult:
        """
        Validate layout properties.

        Args:
            image: Input image
            expected_count: Exact element count expected
            min_count: Minimum element count
            max_count: Maximum element count
            alignment: Alignment to verify
            element_type: Filter by element type
            alignment_tolerance: Pixel tolerance for alignment

        Returns:
            MLAssertionResult with layout validation outcome
        """
        elements = self.detect_elements(image)

        if element_type is not None:
            elements = [e for e in elements if e.element_type == element_type]

        count = len(elements)

        if expected_count is not None:
            passed = count == expected_count
            return MLAssertionResult(
                passed=passed,
                message=f"Element count is {count}" if passed else f"Expected {expected_count} elements, found {count}",
                actual=count,
                expected=expected_count,
                confidence=1.0 if passed else 0.0,
                details={"elements": [{"type": e.element_type, "bbox": e.bounding_box} for e in elements]},
            )

        if min_count is not None or max_count is not None:
            above_min = count >= min_count if min_count is not None else True
            below_max = count <= max_count if max_count is not None else True
            passed = above_min and below_max

            expected_range = ""
            if min_count is not None and max_count is not None:
                expected_range = f"{min_count}-{max_count}"
            elif min_count is not None:
                expected_range = f">= {min_count}"
            else:
                expected_range = f"<= {max_count}"

            return MLAssertionResult(
                passed=passed,
                message=f"Element count ({count}) in range" if passed else f"Element count ({count}) outside range {expected_range}",
                actual=count,
                expected=expected_range,
                confidence=1.0 if passed else 0.0,
                details={"elements": [{"type": e.element_type, "bbox": e.bounding_box} for e in elements]},
            )

        if alignment is not None:
            align_type = AlignmentType(alignment) if isinstance(alignment, str) else alignment
            aligned, score = self.check_alignment(elements, align_type, alignment_tolerance)

            return MLAssertionResult(
                passed=aligned,
                message=f"Elements are {align_type.value}-aligned" if aligned else f"Elements not {align_type.value}-aligned",
                actual=f"alignment_score={score:.2f}",
                expected=align_type.value,
                confidence=score,
                details={"alignment_score": score, "element_count": count},
            )

        # Default: return element analysis
        return MLAssertionResult(
            passed=True,
            message=f"Layout analysis: {count} elements detected",
            actual=count,
            confidence=1.0,
            details={"elements": [{"type": e.element_type, "bbox": e.bounding_box} for e in elements]},
        )


class IconMatcher(BaseMLAssertion):
    """
    Icon/logo matching using feature detection.

    Uses ORB (Oriented FAST and Rotated BRIEF) for feature matching
    as it's patent-free alternative to SIFT/SURF.
    """

    def __init__(
        self,
        n_features: int = 500,
        match_threshold: float = 0.7,
    ) -> None:
        super().__init__()
        self._n_features = n_features
        self._match_threshold = match_threshold
        self._orb = cv2.ORB_create(nfeatures=n_features)
        self._bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)

    def match_template(
        self,
        image: ImageInput,
        template: ImageInput,
        min_confidence: float = 0.5,
    ) -> IconMatchResult:
        """
        Match a template (icon/logo) in an image using feature matching.

        Args:
            image: Source image to search in
            template: Template image to find
            min_confidence: Minimum match confidence

        Returns:
            IconMatchResult with match details
        """
        img_gray = ImageLoader.to_grayscale(image)
        template_gray = ImageLoader.to_grayscale(template)

        # Detect keypoints and compute descriptors
        kp1, des1 = self._orb.detectAndCompute(template_gray, None)
        kp2, des2 = self._orb.detectAndCompute(img_gray, None)

        if des1 is None or des2 is None or len(des1) == 0 or len(des2) == 0:
            return IconMatchResult(matched=False, confidence=0.0, matches_count=0)

        # Match descriptors
        matches = self._bf.knnMatch(des1, des2, k=2)

        # Apply Lowe's ratio test
        good_matches = []
        for match_pair in matches:
            if len(match_pair) == 2:
                m, n = match_pair
                if m.distance < self._match_threshold * n.distance:
                    good_matches.append(m)

        # Calculate confidence
        min_matches_needed = max(10, len(kp1) * 0.1)
        confidence = min(len(good_matches) / min_matches_needed, 1.0)

        if len(good_matches) >= min_matches_needed and confidence >= min_confidence:
            # Find bounding box of matched region
            src_pts = np.float32([kp1[m.queryIdx].pt for m in good_matches]).reshape(-1, 1, 2)
            dst_pts = np.float32([kp2[m.trainIdx].pt for m in good_matches]).reshape(-1, 1, 2)

            # Get homography
            M, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)

            if M is not None:
                h, w = template_gray.shape
                pts = np.float32([[0, 0], [0, h - 1], [w - 1, h - 1], [w - 1, 0]]).reshape(-1, 1, 2)
                dst = cv2.perspectiveTransform(pts, M)

                # Get bounding box
                x_coords = dst[:, 0, 0]
                y_coords = dst[:, 0, 1]
                x, y = int(min(x_coords)), int(min(y_coords))
                w_box = int(max(x_coords) - x)
                h_box = int(max(y_coords) - y)

                return IconMatchResult(
                    matched=True,
                    confidence=confidence,
                    location=(x, y, w_box, h_box),
                    matches_count=len(good_matches),
                )

            return IconMatchResult(
                matched=True,
                confidence=confidence,
                matches_count=len(good_matches),
            )

        return IconMatchResult(
            matched=False,
            confidence=confidence,
            matches_count=len(good_matches),
        )

    def match_template_correlation(
        self,
        image: ImageInput,
        template: ImageInput,
        threshold: float = 0.8,
    ) -> IconMatchResult:
        """
        Match template using OpenCV template matching (correlation).

        Better for exact pixel matches, less tolerant of rotation/scale.

        Args:
            image: Source image
            template: Template to find
            threshold: Match threshold (0-1)

        Returns:
            IconMatchResult with match details
        """
        img = ImageLoader.to_cv2(image)
        tmpl = ImageLoader.to_cv2(template)

        # Convert to grayscale for matching
        img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        tmpl_gray = cv2.cvtColor(tmpl, cv2.COLOR_BGR2GRAY)

        # Ensure template is smaller than image
        if tmpl_gray.shape[0] > img_gray.shape[0] or tmpl_gray.shape[1] > img_gray.shape[1]:
            return IconMatchResult(matched=False, confidence=0.0)

        # Template matching
        result = cv2.matchTemplate(img_gray, tmpl_gray, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

        if max_val >= threshold:
            h, w = tmpl_gray.shape
            return IconMatchResult(
                matched=True,
                confidence=float(max_val),
                location=(max_loc[0], max_loc[1], w, h),
                matches_count=1,
            )

        return IconMatchResult(
            matched=False,
            confidence=float(max_val),
            matches_count=0,
        )

    def validate(
        self,
        image: ImageInput,
        *,
        template: ImageInput | None = None,
        template_path: str | Path | None = None,
        method: Literal["feature", "correlation"] = "feature",
        min_confidence: float = 0.5,
        **kwargs: Any,
    ) -> MLAssertionResult:
        """
        Validate icon/logo presence.

        Args:
            image: Source image
            template: Template image
            template_path: Path to template image
            method: Matching method ('feature' or 'correlation')
            min_confidence: Minimum match confidence

        Returns:
            MLAssertionResult with match outcome
        """
        if template is None and template_path is not None:
            template = Image.open(template_path)
        elif template is None:
            return MLAssertionResult(
                passed=False,
                message="No template provided for icon matching",
            )

        if method == "correlation":
            result = self.match_template_correlation(image, template, threshold=min_confidence)
        else:
            result = self.match_template(image, template, min_confidence=min_confidence)

        return MLAssertionResult(
            passed=result.matched,
            message="Icon/logo found" if result.matched else "Icon/logo not found",
            actual=f"confidence={result.confidence:.2%}",
            expected=f">= {min_confidence:.2%}",
            confidence=result.confidence,
            details={
                "location": result.location,
                "matches_count": result.matches_count,
                "method": method,
            },
        )


class AccessibilityChecker(BaseMLAssertion):
    """
    Accessibility checks for UI validation.

    Provides:
    - Contrast ratio calculation (WCAG compliance)
    - Font size detection
    - Touch target size validation
    """

    # WCAG contrast ratio requirements
    WCAG_AA_NORMAL = 4.5
    WCAG_AA_LARGE = 3.0
    WCAG_AAA_NORMAL = 7.0
    WCAG_AAA_LARGE = 4.5

    def __init__(self) -> None:
        super().__init__()

    def calculate_luminance(self, rgb: tuple[int, int, int]) -> float:
        """
        Calculate relative luminance per WCAG 2.1.

        Args:
            rgb: RGB color tuple (0-255)

        Returns:
            Relative luminance (0-1)
        """

        def adjust(value: int) -> float:
            v = value / 255
            return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4

        r, g, b = rgb
        return 0.2126 * adjust(r) + 0.7152 * adjust(g) + 0.0722 * adjust(b)

    def calculate_contrast_ratio(
        self,
        foreground: tuple[int, int, int],
        background: tuple[int, int, int],
    ) -> float:
        """
        Calculate contrast ratio between two colors per WCAG 2.1.

        Args:
            foreground: Foreground RGB color
            background: Background RGB color

        Returns:
            Contrast ratio (1-21)
        """
        l1 = self.calculate_luminance(foreground)
        l2 = self.calculate_luminance(background)

        lighter = max(l1, l2)
        darker = min(l1, l2)

        return (lighter + 0.05) / (darker + 0.05)

    def check_contrast(
        self,
        image: ImageInput,
        region: BoundingBox | None = None,
    ) -> ContrastResult:
        """
        Estimate contrast ratio from image by detecting foreground/background.

        Args:
            image: Input image
            region: Optional region to analyze

        Returns:
            ContrastResult with contrast analysis
        """
        pil_img = ImageLoader.to_pil(image)

        if region:
            x, y, w, h = region
            pil_img = pil_img.crop((x, y, x + w, y + h))

        # Use color analyzer to get dominant colors
        analyzer = ColorAnalyzer(n_colors=2)
        colors = analyzer.get_dominant_colors(pil_img, n_colors=2)

        if len(colors) < 2:
            # Fallback: assume white background
            fg_color = colors[0].rgb if colors else (0, 0, 0)
            bg_color = (255, 255, 255)
        else:
            # Assume larger area is background
            if colors[0].percentage > colors[1].percentage:
                bg_color = colors[0].rgb
                fg_color = colors[1].rgb
            else:
                fg_color = colors[0].rgb
                bg_color = colors[1].rgb

        ratio = self.calculate_contrast_ratio(fg_color, bg_color)

        return ContrastResult(
            ratio=ratio,
            passes_aa=ratio >= self.WCAG_AA_NORMAL,
            passes_aaa=ratio >= self.WCAG_AAA_NORMAL,
            foreground_color=fg_color,
            background_color=bg_color,
        )

    def validate(
        self,
        image: ImageInput,
        *,
        min_contrast_ratio: float | None = None,
        wcag_level: Literal["AA", "AAA"] | None = None,
        region: BoundingBox | None = None,
        **kwargs: Any,
    ) -> MLAssertionResult:
        """
        Validate accessibility requirements.

        Args:
            image: Input image
            min_contrast_ratio: Minimum contrast ratio required
            wcag_level: WCAG compliance level to check
            region: Optional region to analyze

        Returns:
            MLAssertionResult with accessibility check outcome
        """
        result = self.check_contrast(image, region=region)

        if min_contrast_ratio is not None:
            passed = result.ratio >= min_contrast_ratio

            return MLAssertionResult(
                passed=passed,
                message=f"Contrast ratio {result.ratio:.2f}:1 {'meets' if passed else 'below'} requirement",
                actual=f"{result.ratio:.2f}:1",
                expected=f">= {min_contrast_ratio}:1",
                confidence=min(result.ratio / min_contrast_ratio, 1.0),
                details={
                    "foreground": result.foreground_color,
                    "background": result.background_color,
                    "passes_aa": result.passes_aa,
                    "passes_aaa": result.passes_aaa,
                },
            )

        if wcag_level is not None:
            if wcag_level == "AA":
                passed = result.passes_aa
                required = self.WCAG_AA_NORMAL
            else:
                passed = result.passes_aaa
                required = self.WCAG_AAA_NORMAL

            return MLAssertionResult(
                passed=passed,
                message=f"WCAG {wcag_level} {'compliant' if passed else 'non-compliant'} (ratio: {result.ratio:.2f}:1)",
                actual=f"{result.ratio:.2f}:1",
                expected=f">= {required}:1 (WCAG {wcag_level})",
                confidence=min(result.ratio / required, 1.0),
                details={
                    "foreground": result.foreground_color,
                    "background": result.background_color,
                    "passes_aa": result.passes_aa,
                    "passes_aaa": result.passes_aaa,
                },
            )

        # Default: return contrast analysis
        return MLAssertionResult(
            passed=True,
            message=f"Contrast ratio: {result.ratio:.2f}:1",
            actual=f"{result.ratio:.2f}:1",
            confidence=1.0,
            details={
                "ratio": result.ratio,
                "foreground": result.foreground_color,
                "background": result.background_color,
                "passes_aa": result.passes_aa,
                "passes_aaa": result.passes_aaa,
            },
        )


class FormFieldDetector(BaseMLAssertion):
    """
    Form field detection using contour analysis.

    Detects:
    - Input fields (text boxes)
    - Buttons
    - Checkboxes
    - Radio buttons
    - Dropdowns
    """

    def __init__(self) -> None:
        super().__init__()

    def detect_fields(
        self,
        image: ImageInput,
    ) -> list[DetectedElement]:
        """
        Detect form fields in image.

        Args:
            image: Input image

        Returns:
            List of detected form elements
        """
        cv2_img = ImageLoader.to_cv2(image)
        gray = cv2.cvtColor(cv2_img, cv2.COLOR_BGR2GRAY)

        # Apply adaptive thresholding
        binary = cv2.adaptiveThreshold(
            gray,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV,
            11,
            2,
        )

        # Find contours
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        elements = []
        image_height, image_width = cv2_img.shape[:2]
        image_area = image_height * image_width

        for contour in contours:
            area = cv2.contourArea(contour)
            if area < 500 or area > image_area * 0.5:
                continue

            x, y, w, h = cv2.boundingRect(contour)
            aspect_ratio = w / h if h > 0 else 0

            # Classify based on shape characteristics
            field_type = self._classify_form_field(
                contour,
                aspect_ratio,
                area,
                w,
                h,
            )

            if field_type is not None:
                elements.append(
                    DetectedElement(
                        element_type=field_type,
                        bounding_box=(x, y, w, h),
                        confidence=0.7,
                        attributes={
                            "aspect_ratio": aspect_ratio,
                            "area": area,
                        },
                    )
                )

        return elements

    def _classify_form_field(
        self,
        contour: np.ndarray[Any, Any],
        aspect_ratio: float,
        area: int,
        width: int,
        height: int,
    ) -> str | None:
        """Classify contour as form field type."""
        # Approximate contour
        epsilon = 0.02 * cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, epsilon, True)
        vertices = len(approx)

        # Square-ish small elements = checkbox/radio
        if 0.8 <= aspect_ratio <= 1.2 and area < 2000:
            if vertices == 4:
                return "checkbox"
            if vertices > 6:
                return "radio_button"

        # Wide rectangles = input fields
        if aspect_ratio > 3 and vertices == 4:
            return "input_field"

        # Medium rectangles = buttons
        if 1.5 <= aspect_ratio <= 4 and vertices == 4 and area > 1000:
            return "button"

        # Rectangles with dropdown indicators
        if aspect_ratio > 2 and area > 500:
            return "dropdown"

        return None

    def validate(
        self,
        image: ImageInput,
        *,
        expected_fields: dict[str, int] | None = None,
        min_fields: int | None = None,
        field_type: str | None = None,
        **kwargs: Any,
    ) -> MLAssertionResult:
        """
        Validate form field detection.

        Args:
            image: Input image
            expected_fields: Expected count per field type
            min_fields: Minimum total fields expected
            field_type: Filter by specific field type

        Returns:
            MLAssertionResult with form field detection outcome
        """
        fields = self.detect_fields(image)

        if field_type is not None:
            fields = [f for f in fields if f.element_type == field_type]

        if expected_fields is not None:
            counts: dict[str, int] = {}
            for f in fields:
                counts[f.element_type] = counts.get(f.element_type, 0) + 1

            all_match = all(counts.get(ft, 0) == cnt for ft, cnt in expected_fields.items())

            return MLAssertionResult(
                passed=all_match,
                message="Form fields match expected" if all_match else "Form fields mismatch",
                actual=counts,
                expected=expected_fields,
                confidence=1.0 if all_match else 0.5,
                details={"fields": [{"type": f.element_type, "bbox": f.bounding_box} for f in fields]},
            )

        if min_fields is not None:
            count = len(fields)
            passed = count >= min_fields

            return MLAssertionResult(
                passed=passed,
                message=f"Found {count} form fields" if passed else f"Expected >= {min_fields} fields, found {count}",
                actual=count,
                expected=f">= {min_fields}",
                confidence=1.0 if passed else count / min_fields,
                details={"fields": [{"type": f.element_type, "bbox": f.bounding_box} for f in fields]},
            )

        # Default: return field analysis
        return MLAssertionResult(
            passed=True,
            message=f"Detected {len(fields)} form fields",
            actual=len(fields),
            confidence=1.0,
            details={"fields": [{"type": f.element_type, "bbox": f.bounding_box} for f in fields]},
        )


class RegionDiffAnalyzer(BaseMLAssertion):
    """
    Region-based screenshot diff analysis.

    Provides:
    - Region extraction and comparison
    - Change detection with region identification
    - Semantic diff (ignore minor changes)
    """

    def __init__(self) -> None:
        super().__init__()

    def compare_regions(
        self,
        image1: ImageInput,
        image2: ImageInput,
        grid_size: tuple[int, int] = (4, 4),
        threshold: float = 0.1,
    ) -> list[tuple[BoundingBox, float]]:
        """
        Compare two images region by region.

        Args:
            image1: First image
            image2: Second image
            grid_size: Grid division (rows, cols)
            threshold: Difference threshold per region

        Returns:
            List of (region_bbox, diff_score) for changed regions
        """
        img1 = ImageLoader.to_cv2(image1)
        img2 = ImageLoader.to_cv2(image2)

        # Resize if different sizes
        if img1.shape != img2.shape:
            img2 = cv2.resize(img2, (img1.shape[1], img1.shape[0]))

        height, width = img1.shape[:2]
        rows, cols = grid_size

        region_height = height // rows
        region_width = width // cols

        changed_regions = []

        for row in range(rows):
            for col in range(cols):
                x = col * region_width
                y = row * region_height
                w = region_width
                h = region_height

                # Extract regions
                r1 = img1[y : y + h, x : x + w]
                r2 = img2[y : y + h, x : x + w]

                # Calculate difference
                diff = cv2.absdiff(r1, r2)
                diff_score = np.mean(diff) / 255

                if diff_score > threshold:
                    changed_regions.append(((x, y, w, h), float(diff_score)))

        return changed_regions

    def validate(
        self,
        image: ImageInput,
        *,
        baseline: ImageInput | None = None,
        baseline_path: str | Path | None = None,
        grid_size: tuple[int, int] = (4, 4),
        max_changed_regions: int = 0,
        region_threshold: float = 0.1,
        **kwargs: Any,
    ) -> MLAssertionResult:
        """
        Validate region-based diff.

        Args:
            image: Current image
            baseline: Baseline image
            baseline_path: Path to baseline image
            grid_size: Grid division for region analysis
            max_changed_regions: Maximum allowed changed regions
            region_threshold: Threshold for region change detection

        Returns:
            MLAssertionResult with diff analysis outcome
        """
        if baseline is None and baseline_path is not None:
            baseline = Image.open(baseline_path)
        elif baseline is None:
            return MLAssertionResult(
                passed=False,
                message="No baseline provided for comparison",
            )

        changed = self.compare_regions(
            image,
            baseline,
            grid_size=grid_size,
            threshold=region_threshold,
        )

        changed_count = len(changed)
        passed = changed_count <= max_changed_regions

        return MLAssertionResult(
            passed=passed,
            message=f"{changed_count} regions changed" if passed else f"Too many regions changed: {changed_count} > {max_changed_regions}",
            actual=changed_count,
            expected=f"<= {max_changed_regions}",
            confidence=1.0 - (changed_count / (grid_size[0] * grid_size[1])),
            details={
                "changed_regions": [{"bbox": bbox, "score": score} for bbox, score in changed],
                "grid_size": grid_size,
                "total_regions": grid_size[0] * grid_size[1],
            },
        )


class MLAssertionEngine:
    """
    Unified engine for ML-based UI assertions.

    Provides a single interface to all ML assertion types:
    - OCR text validation
    - UI state classification
    - Color analysis
    - Layout analysis
    - Icon/logo matching
    - Accessibility checks
    - Form field detection
    - Region-based diff
    """

    def __init__(
        self,
        ocr_backend: Literal["pytesseract", "easyocr"] = "easyocr",
        ocr_languages: list[str] | None = None,
    ) -> None:
        self._log = logger.bind(component="ml_assertion_engine")

        # Lazy-initialized analyzers
        self._ocr: OCRAssertion | None = None
        self._classifier: ImageClassifier | None = None
        self._color_analyzer: ColorAnalyzer | None = None
        self._layout_analyzer: LayoutAnalyzer | None = None
        self._icon_matcher: IconMatcher | None = None
        self._accessibility_checker: AccessibilityChecker | None = None
        self._form_detector: FormFieldDetector | None = None
        self._region_diff: RegionDiffAnalyzer | None = None

        self._ocr_backend = ocr_backend
        self._ocr_languages = ocr_languages

    @property
    def ocr(self) -> OCRAssertion:
        """Get OCR assertion engine (lazy-loaded)."""
        if self._ocr is None:
            self._ocr = OCRAssertion(
                backend=self._ocr_backend,
                languages=self._ocr_languages,
            )
        return self._ocr

    @property
    def classifier(self) -> ImageClassifier:
        """Get image classifier (lazy-loaded)."""
        if self._classifier is None:
            self._classifier = ImageClassifier()
        return self._classifier

    @property
    def color_analyzer(self) -> ColorAnalyzer:
        """Get color analyzer (lazy-loaded)."""
        if self._color_analyzer is None:
            self._color_analyzer = ColorAnalyzer()
        return self._color_analyzer

    @property
    def layout_analyzer(self) -> LayoutAnalyzer:
        """Get layout analyzer (lazy-loaded)."""
        if self._layout_analyzer is None:
            self._layout_analyzer = LayoutAnalyzer()
        return self._layout_analyzer

    @property
    def icon_matcher(self) -> IconMatcher:
        """Get icon matcher (lazy-loaded)."""
        if self._icon_matcher is None:
            self._icon_matcher = IconMatcher()
        return self._icon_matcher

    @property
    def accessibility_checker(self) -> AccessibilityChecker:
        """Get accessibility checker (lazy-loaded)."""
        if self._accessibility_checker is None:
            self._accessibility_checker = AccessibilityChecker()
        return self._accessibility_checker

    @property
    def form_detector(self) -> FormFieldDetector:
        """Get form field detector (lazy-loaded)."""
        if self._form_detector is None:
            self._form_detector = FormFieldDetector()
        return self._form_detector

    @property
    def region_diff(self) -> RegionDiffAnalyzer:
        """Get region diff analyzer (lazy-loaded)."""
        if self._region_diff is None:
            self._region_diff = RegionDiffAnalyzer()
        return self._region_diff

    # Convenience methods for common assertions

    def assert_ocr_text_equals(
        self,
        image: ImageInput,
        expected_text: str,
        min_confidence: float = 0.5,
        region: BoundingBox | None = None,
    ) -> MLAssertionResult:
        """Assert OCR-extracted text equals expected value."""
        return self.ocr.validate(
            image,
            expected_text=expected_text,
            min_confidence=min_confidence,
            region=region,
        )

    def assert_ocr_text_contains(
        self,
        image: ImageInput,
        contains: str,
        min_confidence: float = 0.5,
        region: BoundingBox | None = None,
    ) -> MLAssertionResult:
        """Assert OCR-extracted text contains expected substring."""
        return self.ocr.validate(
            image,
            contains=contains,
            min_confidence=min_confidence,
            region=region,
        )

    def assert_ui_state(
        self,
        image: ImageInput,
        expected_state: UIState | str,
        min_confidence: float = 0.5,
    ) -> MLAssertionResult:
        """Assert UI is in expected state (loading, error, success, empty, normal)."""
        return self.classifier.validate(
            image,
            expected_state=expected_state,
            min_confidence=min_confidence,
        )

    def assert_dominant_color(
        self,
        image: ImageInput,
        expected_color: tuple[int, int, int] | str,
        tolerance: int = 30,
    ) -> MLAssertionResult:
        """Assert dominant color matches expected."""
        return self.color_analyzer.validate(
            image,
            dominant_color=expected_color,
            color_tolerance=tolerance,
        )

    def assert_has_color(
        self,
        image: ImageInput,
        color: tuple[int, int, int] | str,
        min_percentage: float = 0.01,
        tolerance: int = 30,
    ) -> MLAssertionResult:
        """Assert image contains specified color."""
        return self.color_analyzer.validate(
            image,
            has_color=color,
            min_percentage=min_percentage,
            color_tolerance=tolerance,
        )

    def assert_element_count(
        self,
        image: ImageInput,
        expected_count: int,
        element_type: str | None = None,
    ) -> MLAssertionResult:
        """Assert detected element count equals expected."""
        return self.layout_analyzer.validate(
            image,
            expected_count=expected_count,
            element_type=element_type,
        )

    def assert_elements_aligned(
        self,
        image: ImageInput,
        alignment: AlignmentType | str,
        tolerance: int = 10,
    ) -> MLAssertionResult:
        """Assert elements are aligned."""
        return self.layout_analyzer.validate(
            image,
            alignment=alignment,
            alignment_tolerance=tolerance,
        )

    def assert_icon_present(
        self,
        image: ImageInput,
        template: ImageInput | str | Path,
        min_confidence: float = 0.5,
    ) -> MLAssertionResult:
        """Assert icon/logo is present in image."""
        template_input: ImageInput
        if isinstance(template, (str, Path)):
            template_input = Image.open(template)
        else:
            template_input = template
        return self.icon_matcher.validate(
            image,
            template=template_input,
            min_confidence=min_confidence,
        )

    def assert_contrast_ratio_min(
        self,
        image: ImageInput,
        min_ratio: float,
        region: BoundingBox | None = None,
    ) -> MLAssertionResult:
        """Assert contrast ratio meets minimum requirement."""
        return self.accessibility_checker.validate(
            image,
            min_contrast_ratio=min_ratio,
            region=region,
        )

    def assert_wcag_compliant(
        self,
        image: ImageInput,
        level: Literal["AA", "AAA"] = "AA",
        region: BoundingBox | None = None,
    ) -> MLAssertionResult:
        """Assert image meets WCAG contrast requirements."""
        return self.accessibility_checker.validate(
            image,
            wcag_level=level,
            region=region,
        )

    def assert_form_fields(
        self,
        image: ImageInput,
        expected_fields: dict[str, int] | None = None,
        min_fields: int | None = None,
    ) -> MLAssertionResult:
        """Assert form fields match expected configuration."""
        return self.form_detector.validate(
            image,
            expected_fields=expected_fields,
            min_fields=min_fields,
        )

    def assert_region_diff(
        self,
        image: ImageInput,
        baseline: ImageInput | str | Path,
        max_changed_regions: int = 0,
        grid_size: tuple[int, int] = (4, 4),
    ) -> MLAssertionResult:
        """Assert region-based diff within tolerance."""
        baseline_input: ImageInput
        if isinstance(baseline, (str, Path)):
            baseline_input = Image.open(baseline)
        else:
            baseline_input = baseline
        return self.region_diff.validate(
            image,
            baseline=baseline_input,
            max_changed_regions=max_changed_regions,
            grid_size=grid_size,
        )
