"""
ML-based element classification for intelligent test generation.

Uses ML techniques to:
- Classify elements by purpose (login, search, checkout, navigation)
- Detect element relationships (label-input, button-form)
- Identify critical user journeys from element patterns
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import StrEnum, auto
from typing import TYPE_CHECKING, Any

import numpy as np
import structlog
from sklearn.cluster import DBSCAN
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

if TYPE_CHECKING:
    from autoqa.builder.analyzer.page_analyzer import InteractiveElement, BoundingBox

logger = structlog.get_logger(__name__)


@dataclass
class ClassifierConfig:
    """Configuration for element classifier."""

    min_confidence: float = 0.5
    """Minimum confidence threshold for classification."""

    enable_ml_classification: bool = True
    """Whether to use ML-based classification."""

    enable_pattern_matching: bool = True
    """Whether to use pattern-based classification."""

    enable_visual_grouping: bool = True
    """Whether to use visual clustering."""

    clustering_eps: float = 50.0
    """DBSCAN epsilon for visual clustering."""

    min_cluster_samples: int = 2
    """Minimum samples for DBSCAN clustering."""


class ElementPurpose(StrEnum):
    """Classification of element purpose."""

    # Authentication
    LOGIN_USERNAME = auto()
    LOGIN_PASSWORD = auto()
    LOGIN_SUBMIT = auto()
    REGISTER_EMAIL = auto()
    REGISTER_PASSWORD = auto()
    REGISTER_SUBMIT = auto()
    LOGOUT = auto()
    FORGOT_PASSWORD = auto()

    # Search
    SEARCH_INPUT = auto()
    SEARCH_SUBMIT = auto()
    SEARCH_FILTER = auto()
    SEARCH_SORT = auto()

    # Navigation
    NAVIGATION_LINK = auto()
    NAVIGATION_MENU = auto()
    NAVIGATION_BREADCRUMB = auto()
    PAGINATION_PREV = auto()
    PAGINATION_NEXT = auto()
    PAGINATION_PAGE = auto()

    # E-commerce
    ADD_TO_CART = auto()
    REMOVE_FROM_CART = auto()
    CHECKOUT = auto()
    QUANTITY_INPUT = auto()
    PRODUCT_SELECT = auto()

    # Form
    FORM_INPUT = auto()
    FORM_SELECT = auto()
    FORM_CHECKBOX = auto()
    FORM_RADIO = auto()
    FORM_SUBMIT = auto()
    FORM_RESET = auto()
    FORM_CANCEL = auto()

    # Actions
    ACTION_SAVE = auto()
    ACTION_DELETE = auto()
    ACTION_EDIT = auto()
    ACTION_CREATE = auto()
    ACTION_CONFIRM = auto()
    ACTION_CANCEL = auto()
    ACTION_CLOSE = auto()

    # Content
    CONTENT_EXPAND = auto()
    CONTENT_COLLAPSE = auto()
    CONTENT_TAB = auto()
    CONTENT_ACCORDION = auto()

    # Media
    MEDIA_PLAY = auto()
    MEDIA_PAUSE = auto()
    MEDIA_VOLUME = auto()
    MEDIA_FULLSCREEN = auto()

    # Social
    SOCIAL_SHARE = auto()
    SOCIAL_LIKE = auto()
    SOCIAL_COMMENT = auto()

    # Unknown
    UNKNOWN = auto()


class RelationshipType(StrEnum):
    """Types of element relationships."""

    LABEL_FOR = "label_for"
    BUTTON_FORM = "button_form"
    INPUT_FORM = "input_form"
    SIBLING = "sibling"
    PARENT_CHILD = "parent_child"
    VISUALLY_GROUPED = "visually_grouped"
    SEMANTICALLY_RELATED = "semantically_related"


@dataclass
class ElementRelationship:
    """Relationship between two elements."""

    source_selector: str
    target_selector: str
    relationship_type: RelationshipType
    confidence: float
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ClassificationResult:
    """Result of element classification."""

    element_selector: str
    purpose: ElementPurpose
    confidence: float
    alternative_purposes: list[tuple[ElementPurpose, float]] = field(default_factory=list)
    features_used: list[str] = field(default_factory=list)


@dataclass
class UserJourney:
    """Detected user journey pattern."""

    journey_name: str
    journey_type: str
    steps: list[ClassificationResult]
    confidence: float
    entry_point: str
    exit_point: str | None = None


class ElementClassifier:
    """
    ML-based element classifier for intelligent test generation.

    Uses text analysis, pattern matching, and spatial clustering to:
    - Classify element purposes
    - Detect relationships between elements
    - Identify user journey patterns
    """

    # Keyword patterns for classification
    CLASSIFICATION_PATTERNS: dict[ElementPurpose, dict[str, list[str]]] = {
        # Authentication
        ElementPurpose.LOGIN_USERNAME: {
            "keywords": ["username", "user", "email", "login", "account", "userid", "user_name"],
            "patterns": [r"user[\-_]?name", r"log[\-_]?in", r"email"],
        },
        ElementPurpose.LOGIN_PASSWORD: {
            "keywords": ["password", "passwd", "pwd", "pass", "secret"],
            "patterns": [r"pass[\-_]?word", r"pwd"],
        },
        ElementPurpose.LOGIN_SUBMIT: {
            "keywords": ["login", "signin", "sign in", "log in", "submit"],
            "patterns": [r"log[\-_]?in", r"sign[\-_]?in"],
        },
        ElementPurpose.REGISTER_EMAIL: {
            "keywords": ["email", "mail", "register"],
            "patterns": [r"e[\-_]?mail", r"register"],
        },
        ElementPurpose.REGISTER_SUBMIT: {
            "keywords": ["register", "signup", "sign up", "create account", "join"],
            "patterns": [r"sign[\-_]?up", r"register", r"create"],
        },
        ElementPurpose.LOGOUT: {
            "keywords": ["logout", "signout", "sign out", "log out"],
            "patterns": [r"log[\-_]?out", r"sign[\-_]?out"],
        },
        ElementPurpose.FORGOT_PASSWORD: {
            "keywords": ["forgot", "reset", "recover", "forgotten"],
            "patterns": [r"forgot", r"reset", r"recover"],
        },
        # Search
        ElementPurpose.SEARCH_INPUT: {
            "keywords": ["search", "query", "find", "look"],
            "patterns": [r"search", r"query", r"q="],
        },
        ElementPurpose.SEARCH_SUBMIT: {
            "keywords": ["search", "find", "go"],
            "patterns": [r"search"],
        },
        ElementPurpose.SEARCH_FILTER: {
            "keywords": ["filter", "refine", "narrow"],
            "patterns": [r"filter"],
        },
        ElementPurpose.SEARCH_SORT: {
            "keywords": ["sort", "order", "arrange"],
            "patterns": [r"sort", r"order[\-_]?by"],
        },
        # Navigation
        ElementPurpose.NAVIGATION_LINK: {
            "keywords": ["home", "about", "contact", "services", "products", "menu"],
            "patterns": [r"nav", r"menu"],
        },
        ElementPurpose.PAGINATION_PREV: {
            "keywords": ["previous", "prev", "back", "prior"],
            "patterns": [r"prev", r"back"],
        },
        ElementPurpose.PAGINATION_NEXT: {
            "keywords": ["next", "forward", "more"],
            "patterns": [r"next", r"forward"],
        },
        # E-commerce
        ElementPurpose.ADD_TO_CART: {
            "keywords": ["add to cart", "add to bag", "buy", "purchase", "add"],
            "patterns": [r"add[\-_]?to[\-_]?cart", r"add[\-_]?to[\-_]?bag", r"buy"],
        },
        ElementPurpose.REMOVE_FROM_CART: {
            "keywords": ["remove", "delete", "clear"],
            "patterns": [r"remove", r"delete"],
        },
        ElementPurpose.CHECKOUT: {
            "keywords": ["checkout", "check out", "proceed", "pay", "purchase"],
            "patterns": [r"check[\-_]?out", r"proceed", r"payment"],
        },
        ElementPurpose.QUANTITY_INPUT: {
            "keywords": ["quantity", "qty", "amount", "count"],
            "patterns": [r"qty", r"quantity", r"amount"],
        },
        # Form actions
        ElementPurpose.FORM_SUBMIT: {
            "keywords": ["submit", "send", "save", "confirm", "ok", "apply"],
            "patterns": [r"submit", r"send"],
        },
        ElementPurpose.FORM_RESET: {
            "keywords": ["reset", "clear", "restart"],
            "patterns": [r"reset", r"clear"],
        },
        ElementPurpose.FORM_CANCEL: {
            "keywords": ["cancel", "close", "dismiss", "abort"],
            "patterns": [r"cancel", r"close"],
        },
        # Actions
        ElementPurpose.ACTION_SAVE: {
            "keywords": ["save", "store", "keep", "preserve"],
            "patterns": [r"save", r"store"],
        },
        ElementPurpose.ACTION_DELETE: {
            "keywords": ["delete", "remove", "trash", "destroy"],
            "patterns": [r"delete", r"remove", r"trash"],
        },
        ElementPurpose.ACTION_EDIT: {
            "keywords": ["edit", "modify", "change", "update"],
            "patterns": [r"edit", r"modify", r"update"],
        },
        ElementPurpose.ACTION_CREATE: {
            "keywords": ["create", "new", "add", "make"],
            "patterns": [r"create", r"new", r"add"],
        },
        ElementPurpose.ACTION_CONFIRM: {
            "keywords": ["confirm", "yes", "ok", "accept", "agree"],
            "patterns": [r"confirm", r"accept"],
        },
        ElementPurpose.ACTION_CLOSE: {
            "keywords": ["close", "dismiss", "hide", "x"],
            "patterns": [r"close", r"dismiss"],
        },
        # Content interaction
        ElementPurpose.CONTENT_EXPAND: {
            "keywords": ["expand", "show more", "view all", "see more"],
            "patterns": [r"expand", r"show[\-_]?more"],
        },
        ElementPurpose.CONTENT_COLLAPSE: {
            "keywords": ["collapse", "show less", "hide", "minimize"],
            "patterns": [r"collapse", r"show[\-_]?less"],
        },
        # Media
        ElementPurpose.MEDIA_PLAY: {
            "keywords": ["play", "start", "watch"],
            "patterns": [r"play", r"start"],
        },
        ElementPurpose.MEDIA_PAUSE: {
            "keywords": ["pause", "stop"],
            "patterns": [r"pause", r"stop"],
        },
        # Social
        ElementPurpose.SOCIAL_SHARE: {
            "keywords": ["share", "post", "tweet", "send"],
            "patterns": [r"share"],
        },
        ElementPurpose.SOCIAL_LIKE: {
            "keywords": ["like", "favorite", "heart", "love"],
            "patterns": [r"like", r"favorite"],
        },
    }

    # Journey patterns
    JOURNEY_PATTERNS: dict[str, list[ElementPurpose]] = {
        "login": [
            ElementPurpose.LOGIN_USERNAME,
            ElementPurpose.LOGIN_PASSWORD,
            ElementPurpose.LOGIN_SUBMIT,
        ],
        "registration": [
            ElementPurpose.REGISTER_EMAIL,
            ElementPurpose.REGISTER_PASSWORD,
            ElementPurpose.REGISTER_SUBMIT,
        ],
        "search": [
            ElementPurpose.SEARCH_INPUT,
            ElementPurpose.SEARCH_SUBMIT,
        ],
        "checkout": [
            ElementPurpose.ADD_TO_CART,
            ElementPurpose.CHECKOUT,
        ],
        "pagination": [
            ElementPurpose.PAGINATION_PREV,
            ElementPurpose.PAGINATION_PAGE,
            ElementPurpose.PAGINATION_NEXT,
        ],
    }

    def __init__(self, config: ClassifierConfig | None = None) -> None:
        self.config = config or ClassifierConfig()
        self._log = logger.bind(component="element_classifier")
        self._vectorizer = TfidfVectorizer(
            analyzer="char_wb",
            ngram_range=(2, 4),
            max_features=1000,
        )
        self._compiled_patterns: dict[ElementPurpose, list[re.Pattern[str]]] = {}
        self._compile_patterns()

    def _compile_patterns(self) -> None:
        """Pre-compile regex patterns for efficiency."""
        for purpose, config in self.CLASSIFICATION_PATTERNS.items():
            patterns = config.get("patterns", [])
            self._compiled_patterns[purpose] = [
                re.compile(p, re.IGNORECASE) for p in patterns
            ]

    def classify_element(
        self, element: InteractiveElement
    ) -> ClassificationResult:
        """
        Classify an interactive element's purpose.

        Args:
            element: Element to classify

        Returns:
            Classification result with confidence
        """
        # Extract features from element
        features = self._extract_features(element)

        # Calculate scores for each purpose
        scores: dict[ElementPurpose, float] = {}
        features_used: dict[ElementPurpose, list[str]] = {}

        for purpose, config in self.CLASSIFICATION_PATTERNS.items():
            score, used_features = self._calculate_purpose_score(features, config)
            if score > 0:
                scores[purpose] = score
                features_used[purpose] = used_features

        # Get best match
        if not scores:
            return ClassificationResult(
                element_selector=element.selector,
                purpose=ElementPurpose.UNKNOWN,
                confidence=0.0,
            )

        sorted_purposes = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        best_purpose, best_score = sorted_purposes[0]

        # Normalize confidence to 0-1
        max_possible_score = 4.0  # keyword + pattern + type + context
        confidence = min(best_score / max_possible_score, 1.0)

        # Get alternatives
        alternatives = [
            (purpose, min(score / max_possible_score, 1.0))
            for purpose, score in sorted_purposes[1:4]
            if score > 0.3 * best_score
        ]

        return ClassificationResult(
            element_selector=element.selector,
            purpose=best_purpose,
            confidence=confidence,
            alternative_purposes=alternatives,
            features_used=features_used.get(best_purpose, []),
        )

    def _extract_features(self, element: InteractiveElement) -> dict[str, Any]:
        """Extract classification features from element."""
        # Combine all text-based features
        text_features = " ".join(filter(None, [
            element.text_content,
            element.placeholder,
            element.name,
            element.element_id,
            element.aria_label,
            element.aria_role,
            element.element_type,
        ])).lower()

        # Extract data attribute values
        data_text = " ".join(element.data_attributes.values()).lower()

        return {
            "text": text_features,
            "data_text": data_text,
            "tag_name": element.tag_name,
            "element_type": element.element_type,
            "aria_role": element.aria_role,
            "href": element.href,
            "is_required": element.is_required,
            "interactions": element.interactions,
            "validation": element.validation_attributes,
        }

    def _calculate_purpose_score(
        self,
        features: dict[str, Any],
        config: dict[str, list[str]],
    ) -> tuple[float, list[str]]:
        """Calculate score for a specific purpose."""
        score = 0.0
        used_features: list[str] = []
        text = features["text"] + " " + features.get("data_text", "")

        # Keyword matching
        keywords = config.get("keywords", [])
        for keyword in keywords:
            if keyword in text:
                score += 1.0
                used_features.append(f"keyword:{keyword}")
                break  # Only count one keyword match per purpose

        # Pattern matching
        patterns = config.get("patterns", [])
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                score += 1.5
                used_features.append(f"pattern:{pattern}")
                break  # Only count one pattern match per purpose

        return score, used_features

    def classify_elements(
        self, elements: list[InteractiveElement]
    ) -> list[ClassificationResult]:
        """
        Classify multiple elements.

        Args:
            elements: List of elements to classify

        Returns:
            List of classification results
        """
        return [self.classify_element(el) for el in elements]

    def detect_relationships(
        self, elements: list[InteractiveElement]
    ) -> list[ElementRelationship]:
        """
        Detect relationships between elements.

        Args:
            elements: List of elements to analyze

        Returns:
            List of detected relationships
        """
        relationships: list[ElementRelationship] = []

        # Build element index for efficient lookup
        element_map = {el.selector: el for el in elements}

        for element in elements:
            # Check for label-input relationships
            label_rel = self._detect_label_relationship(element, element_map)
            if label_rel:
                relationships.append(label_rel)

            # Check for form membership
            if element.parent_component and "form" in element.parent_component.lower():
                relationships.append(
                    ElementRelationship(
                        source_selector=element.selector,
                        target_selector=element.parent_component,
                        relationship_type=RelationshipType.INPUT_FORM,
                        confidence=1.0,
                    )
                )

        # Detect visually grouped elements using spatial clustering
        grouped_rels = self._detect_visual_groupings(elements)
        relationships.extend(grouped_rels)

        # Detect semantically related elements
        semantic_rels = self._detect_semantic_relationships(elements)
        relationships.extend(semantic_rels)

        return relationships

    def _detect_label_relationship(
        self,
        element: InteractiveElement,
        element_map: dict[str, InteractiveElement],
    ) -> ElementRelationship | None:
        """Detect label-input relationships."""
        if element.tag_name != "input":
            return None

        # Look for associated label
        if element.element_id:
            for other_selector, other_el in element_map.items():
                if other_el.tag_name == "label":
                    # Check if label's for attribute matches
                    label_for = other_el.data_attributes.get("for", "")
                    if label_for == element.element_id:
                        return ElementRelationship(
                            source_selector=other_selector,
                            target_selector=element.selector,
                            relationship_type=RelationshipType.LABEL_FOR,
                            confidence=1.0,
                        )

        return None

    def _detect_visual_groupings(
        self, elements: list[InteractiveElement]
    ) -> list[ElementRelationship]:
        """Detect visually grouped elements using spatial clustering."""
        relationships: list[ElementRelationship] = []

        # Filter elements with valid bounding boxes
        elements_with_bbox = [
            el for el in elements
            if el.bounding_box and el.bounding_box.width > 0
        ]

        if len(elements_with_bbox) < 2:
            return relationships

        # Create feature matrix for clustering (x, y positions)
        positions = np.array([
            [el.bounding_box.center_x, el.bounding_box.center_y]  # type: ignore
            for el in elements_with_bbox
        ])

        # Normalize positions
        positions_normalized = (positions - positions.min(axis=0)) / (
            positions.max(axis=0) - positions.min(axis=0) + 1e-10
        )

        # Apply DBSCAN clustering
        try:
            clustering = DBSCAN(eps=0.15, min_samples=2).fit(positions_normalized)
            labels = clustering.labels_

            # Create relationships for elements in same cluster
            for cluster_id in set(labels):
                if cluster_id == -1:  # Skip noise
                    continue

                cluster_elements = [
                    elements_with_bbox[i]
                    for i, label in enumerate(labels)
                    if label == cluster_id
                ]

                # Create pairwise relationships within cluster
                for i, el1 in enumerate(cluster_elements):
                    for el2 in cluster_elements[i + 1:]:
                        relationships.append(
                            ElementRelationship(
                                source_selector=el1.selector,
                                target_selector=el2.selector,
                                relationship_type=RelationshipType.VISUALLY_GROUPED,
                                confidence=0.7,
                                metadata={"cluster_id": int(cluster_id)},
                            )
                        )
        except Exception as e:
            self._log.debug("Visual grouping failed", error=str(e))

        return relationships

    def _detect_semantic_relationships(
        self, elements: list[InteractiveElement]
    ) -> list[ElementRelationship]:
        """Detect semantically related elements using text similarity."""
        relationships: list[ElementRelationship] = []

        if len(elements) < 2:
            return relationships

        # Create text representations for each element
        texts = []
        valid_elements = []
        for el in elements:
            text = " ".join(filter(None, [
                el.text_content,
                el.placeholder,
                el.name,
                el.element_id,
                el.aria_label,
            ]))
            if text.strip():
                texts.append(text.lower())
                valid_elements.append(el)

        if len(texts) < 2:
            return relationships

        try:
            # Compute TF-IDF vectors
            tfidf_matrix = self._vectorizer.fit_transform(texts)

            # Compute pairwise similarities
            similarities = cosine_similarity(tfidf_matrix)

            # Find high similarity pairs
            for i in range(len(valid_elements)):
                for j in range(i + 1, len(valid_elements)):
                    similarity = similarities[i, j]
                    if similarity > 0.5:  # Threshold for semantic relationship
                        relationships.append(
                            ElementRelationship(
                                source_selector=valid_elements[i].selector,
                                target_selector=valid_elements[j].selector,
                                relationship_type=RelationshipType.SEMANTICALLY_RELATED,
                                confidence=float(similarity),
                                metadata={"similarity_score": float(similarity)},
                            )
                        )
        except Exception as e:
            self._log.debug("Semantic relationship detection failed", error=str(e))

        return relationships

    def detect_user_journeys(
        self, classifications: list[ClassificationResult]
    ) -> list[UserJourney]:
        """
        Detect user journey patterns from classified elements.

        Args:
            classifications: List of element classifications

        Returns:
            List of detected user journeys
        """
        journeys: list[UserJourney] = []

        # Index classifications by purpose
        purpose_map: dict[ElementPurpose, list[ClassificationResult]] = {}
        for classification in classifications:
            purpose = classification.purpose
            if purpose not in purpose_map:
                purpose_map[purpose] = []
            purpose_map[purpose].append(classification)

        # Check for each journey pattern
        for journey_name, required_purposes in self.JOURNEY_PATTERNS.items():
            # Check if all required purposes are present
            journey_steps: list[ClassificationResult] = []
            missing_purposes: list[ElementPurpose] = []

            for purpose in required_purposes:
                if purpose in purpose_map and purpose_map[purpose]:
                    # Take the highest confidence classification for this purpose
                    best = max(purpose_map[purpose], key=lambda c: c.confidence)
                    journey_steps.append(best)
                else:
                    missing_purposes.append(purpose)

            # Calculate journey confidence
            if not missing_purposes and journey_steps:
                avg_confidence = sum(s.confidence for s in journey_steps) / len(journey_steps)
                completeness = len(journey_steps) / len(required_purposes)
                confidence = avg_confidence * completeness

                journeys.append(
                    UserJourney(
                        journey_name=journey_name,
                        journey_type=journey_name,
                        steps=journey_steps,
                        confidence=confidence,
                        entry_point=journey_steps[0].element_selector,
                        exit_point=journey_steps[-1].element_selector if len(journey_steps) > 1 else None,
                    )
                )
            elif len(missing_purposes) < len(required_purposes) / 2:
                # Partial journey detected
                avg_confidence = sum(s.confidence for s in journey_steps) / len(journey_steps) if journey_steps else 0
                completeness = len(journey_steps) / len(required_purposes)
                confidence = avg_confidence * completeness * 0.5  # Reduce confidence for partial

                if journey_steps and confidence > 0.3:
                    journeys.append(
                        UserJourney(
                            journey_name=f"partial_{journey_name}",
                            journey_type=journey_name,
                            steps=journey_steps,
                            confidence=confidence,
                            entry_point=journey_steps[0].element_selector,
                            exit_point=journey_steps[-1].element_selector if len(journey_steps) > 1 else None,
                        )
                    )

        return sorted(journeys, key=lambda j: j.confidence, reverse=True)

    def get_critical_elements(
        self,
        classifications: list[ClassificationResult],
        threshold: float = 0.5,
    ) -> list[ClassificationResult]:
        """
        Get elements that are critical for user journeys.

        Args:
            classifications: All element classifications
            threshold: Minimum confidence threshold

        Returns:
            List of critical elements
        """
        critical_purposes = {
            ElementPurpose.LOGIN_SUBMIT,
            ElementPurpose.REGISTER_SUBMIT,
            ElementPurpose.CHECKOUT,
            ElementPurpose.ADD_TO_CART,
            ElementPurpose.SEARCH_SUBMIT,
            ElementPurpose.FORM_SUBMIT,
            ElementPurpose.ACTION_SAVE,
            ElementPurpose.ACTION_DELETE,
        }

        return [
            c for c in classifications
            if c.purpose in critical_purposes and c.confidence >= threshold
        ]
