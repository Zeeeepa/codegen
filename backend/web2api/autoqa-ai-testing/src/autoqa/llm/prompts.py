"""
Tool-specific prompts for LLM integration.

Provides carefully crafted prompts for each AutoQA tool:
- Test Builder: Generate test names, descriptions, step descriptions
- Step Transformer: Natural language to action translation
- Assertions: Semantic validation prompts
- Self-Healing: Selector recovery assistance
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any


class PromptType(StrEnum):
    """Types of prompts available."""

    # Test Builder prompts
    GENERATE_TEST_NAME = "generate_test_name"
    GENERATE_TEST_DESCRIPTION = "generate_test_description"
    GENERATE_STEP_DESCRIPTION = "generate_step_description"
    GENERATE_STEP_NAME = "generate_step_name"
    SUGGEST_ASSERTIONS = "suggest_assertions"

    # Step Transformer prompts
    NATURAL_LANGUAGE_TO_ACTION = "natural_language_to_action"
    ENHANCE_SELECTOR = "enhance_selector"

    # Assertion prompts
    SEMANTIC_VALIDATION = "semantic_validation"
    VISUAL_DESCRIPTION = "visual_description"
    CONTENT_ANALYSIS = "content_analysis"

    # Self-Healing prompts
    SELECTOR_RECOVERY = "selector_recovery"
    ELEMENT_IDENTIFICATION = "element_identification"


@dataclass(frozen=True)
class PromptTemplate:
    """A prompt template with system and user prompt components."""

    system_prompt: str
    user_prompt_template: str
    expected_format: str | None = None
    max_tokens: int = 512
    temperature: float = 0.3


# =============================================================================
# Test Builder Prompts
# =============================================================================

TEST_BUILDER_SYSTEM_PROMPT = """You are an expert QA engineer specializing in test automation. Your task is to generate clear, descriptive names and descriptions for automated tests.

Guidelines:
- Be concise but descriptive
- Use action verbs (Verify, Test, Check, Validate)
- Include the feature or functionality being tested
- Make names readable and self-documenting
- Follow naming conventions: "Test [Feature] [Scenario]" or "[Feature] - [Scenario]"
- Descriptions should explain the test's purpose and expected behavior

Output only the requested text, no explanations or formatting."""

GENERATE_TEST_NAME = PromptTemplate(
    system_prompt=TEST_BUILDER_SYSTEM_PROMPT,
    user_prompt_template="""Generate a clear, descriptive test name for a test that:
- URL: {url}
- Page Title: {page_title}
- Main Elements Found: {elements_summary}
- Has Login Form: {has_login}
- Number of Forms: {form_count}

Output only the test name, nothing else.""",
    max_tokens=64,
    temperature=0.2,
)

GENERATE_TEST_DESCRIPTION = PromptTemplate(
    system_prompt=TEST_BUILDER_SYSTEM_PROMPT,
    user_prompt_template="""Generate a concise test description (1-2 sentences) for a test with:
- Test Name: {test_name}
- URL: {url}
- Page Title: {page_title}
- Elements: {elements_summary}
- Forms: {forms_summary}
- Steps Count: {steps_count}

The description should explain what the test validates and why it's important.
Output only the description, nothing else.""",
    max_tokens=128,
    temperature=0.3,
)

GENERATE_STEP_NAME = PromptTemplate(
    system_prompt=TEST_BUILDER_SYSTEM_PROMPT,
    user_prompt_template="""Generate a clear, action-oriented step name for:
- Action: {action}
- Selector/Target: {selector}
- Text/Value: {text}
- Element Description: {element_description}
- Context: {context}

The name should start with an action verb and clearly describe what the step does.
Output only the step name, nothing else.""",
    max_tokens=48,
    temperature=0.2,
)

GENERATE_STEP_DESCRIPTION = PromptTemplate(
    system_prompt=TEST_BUILDER_SYSTEM_PROMPT,
    user_prompt_template="""Generate a brief description for this test step:
- Step Name: {step_name}
- Action: {action}
- Target: {selector}
- Input: {text}
- Previous Step: {previous_step}
- Next Step: {next_step}

Explain the purpose of this step in the test flow.
Output only the description, nothing else.""",
    max_tokens=96,
    temperature=0.3,
)

SUGGEST_ASSERTIONS = PromptTemplate(
    system_prompt="""You are an expert QA engineer. Given information about a web page and test context, suggest relevant assertions to validate the page state.

Output format: JSON array of assertion objects with fields:
- type: "visibility" | "text" | "attribute" | "url" | "element_count"
- selector: CSS selector or element description
- operator: "is_visible" | "contains" | "equals" | "exists" | "greater_than" | "less_than"
- expected: expected value (if applicable)
- message: human-readable assertion message

Suggest 3-5 most important assertions.""",
    user_prompt_template="""Suggest assertions for this page state:
- URL: {url}
- Page Title: {page_title}
- Key Elements: {elements}
- Form Fields: {forms}
- Test Purpose: {test_purpose}
- Previous Actions: {previous_actions}

Output only valid JSON, nothing else.""",
    expected_format="json",
    max_tokens=512,
    temperature=0.4,
)


# =============================================================================
# Step Transformer Prompts
# =============================================================================

STEP_TRANSFORMER_SYSTEM_PROMPT = """You are an expert at translating natural language test instructions into structured browser automation actions.

You understand common test automation patterns and can map user intent to specific actions:
- Navigation: goto, wait_for_url, wait_for_network_idle
- Clicks: click, double_click, right_click, hover
- Forms: type, pick (select), submit, upload
- Assertions: assert visibility, text, attributes
- Extraction: extract_text, screenshot, get_attribute

Output structured JSON with action details."""

NATURAL_LANGUAGE_TO_ACTION = PromptTemplate(
    system_prompt=STEP_TRANSFORMER_SYSTEM_PROMPT,
    user_prompt_template="""Convert this natural language instruction to a browser action:
"{instruction}"

Page context:
- Current URL: {current_url}
- Available Elements: {available_elements}

Output JSON with:
{{
  "action": "action_name",
  "selector": "element selector or description",
  "parameters": {{"key": "value"}},
  "confidence": 0.0-1.0
}}

Output only valid JSON.""",
    expected_format="json",
    max_tokens=256,
    temperature=0.2,
)

ENHANCE_SELECTOR = PromptTemplate(
    system_prompt="""You are an expert at creating robust, semantic CSS selectors for browser automation.

Given an element's attributes, generate the best selector that:
1. Is unique on the page
2. Is resilient to minor UI changes
3. Uses semantic attributes (data-testid, aria-label, role) when available
4. Falls back to stable structural selectors

Priority order:
1. data-testid, data-test, data-cy attributes
2. aria-label, aria-labelledby
3. Unique ID
4. Unique name attribute
5. Role + accessible name
6. Text content (for buttons/links)
7. Structural selector as last resort""",
    user_prompt_template="""Generate the best selector for this element:
- Tag: {tag}
- ID: {id}
- Name: {name}
- Class: {class_name}
- Text: {text}
- Aria-label: {aria_label}
- Data attributes: {data_attributes}
- Parent context: {parent_context}

Output only the selector string, nothing else.""",
    max_tokens=128,
    temperature=0.1,
)


# =============================================================================
# Assertion Prompts
# =============================================================================

ASSERTION_SYSTEM_PROMPT = """You are an expert QA analyst specializing in semantic validation of web application states.

Your task is to analyze screenshots, text content, or page states and determine if they meet expected criteria. You understand:
- UI patterns and their expected states
- Error indicators and success indicators
- Layout and visual consistency
- Content accuracy and completeness

Provide structured validation results with confidence scores."""

SEMANTIC_VALIDATION = PromptTemplate(
    system_prompt=ASSERTION_SYSTEM_PROMPT,
    user_prompt_template="""Validate the following semantic assertion:

Assertion: {assertion_description}

Page Context:
- URL: {url}
- Visible Text: {visible_text}
- Key Elements: {key_elements}

Determine if the assertion passes and explain your reasoning.

Output JSON:
{{
  "passed": true/false,
  "confidence": 0.0-1.0,
  "reason": "explanation",
  "actual_state": "what was observed",
  "suggestions": ["improvement suggestions if failed"]
}}""",
    expected_format="json",
    max_tokens=256,
    temperature=0.2,
)

VISUAL_DESCRIPTION = PromptTemplate(
    system_prompt="""You are an expert at describing visual states of web applications.

Analyze the described visual state and provide a detailed, structured description that can be used for:
- Visual regression comparison
- Accessibility validation
- State documentation""",
    user_prompt_template="""Describe the visual state based on this information:

OCR Text: {ocr_text}
Detected Colors: {colors}
Layout Info: {layout}
Element Positions: {elements}

Provide a structured description of:
1. Overall layout and structure
2. Key visual elements and their states
3. Color scheme and contrast
4. Any potential issues or anomalies

Output as structured JSON.""",
    expected_format="json",
    max_tokens=512,
    temperature=0.3,
)

CONTENT_ANALYSIS = PromptTemplate(
    system_prompt="""You are an expert content analyst. Analyze web page content for:
- Correctness and accuracy
- Completeness
- Consistency with expected patterns
- Potential issues or errors""",
    user_prompt_template="""Analyze this page content:

Expected Content Type: {content_type}
Expected Patterns: {expected_patterns}
Actual Content: {actual_content}

Validate that the content meets expectations.

Output JSON:
{{
  "valid": true/false,
  "matches_expected": true/false,
  "issues": ["list of issues found"],
  "confidence": 0.0-1.0,
  "details": {{}}
}}""",
    expected_format="json",
    max_tokens=384,
    temperature=0.2,
)


# =============================================================================
# Self-Healing Prompts
# =============================================================================

SELF_HEALING_SYSTEM_PROMPT = """You are an expert at recovering broken CSS selectors in browser automation tests.

When a selector fails, analyze the page context and suggest alternative selectors that:
1. Target the same logical element
2. Are resilient to UI changes
3. Use semantic attributes when possible
4. Consider the element's role and purpose

Output multiple alternatives ranked by confidence."""

SELECTOR_RECOVERY = PromptTemplate(
    system_prompt=SELF_HEALING_SYSTEM_PROMPT,
    user_prompt_template="""The selector "{failed_selector}" failed to find an element.

Context:
- Action attempted: {action}
- Element description: {element_description}
- Similar elements on page: {similar_elements}
- Page structure: {page_structure}

Suggest alternative selectors.

Output JSON:
{{
  "alternatives": [
    {{"selector": "...", "confidence": 0.0-1.0, "strategy": "strategy_name"}},
    ...
  ],
  "likely_cause": "why the original selector failed",
  "recommendation": "best approach"
}}""",
    expected_format="json",
    max_tokens=384,
    temperature=0.3,
)

ELEMENT_IDENTIFICATION = PromptTemplate(
    system_prompt="""You are an expert at identifying UI elements based on descriptions.

Given a natural language description of an element, identify:
1. The most likely element type
2. Possible selectors to target it
3. Attributes that distinguish it""",
    user_prompt_template="""Identify the element described as: "{element_description}"

Available elements on page:
{page_elements}

Output JSON:
{{
  "element_type": "button/input/link/etc",
  "best_match": {{"selector": "...", "confidence": 0.0-1.0}},
  "alternatives": [...],
  "distinguishing_features": ["feature1", "feature2"]
}}""",
    expected_format="json",
    max_tokens=256,
    temperature=0.2,
)


# =============================================================================
# Prompt Registry
# =============================================================================

PROMPT_REGISTRY: dict[PromptType, PromptTemplate] = {
    # Test Builder
    PromptType.GENERATE_TEST_NAME: GENERATE_TEST_NAME,
    PromptType.GENERATE_TEST_DESCRIPTION: GENERATE_TEST_DESCRIPTION,
    PromptType.GENERATE_STEP_NAME: GENERATE_STEP_NAME,
    PromptType.GENERATE_STEP_DESCRIPTION: GENERATE_STEP_DESCRIPTION,
    PromptType.SUGGEST_ASSERTIONS: SUGGEST_ASSERTIONS,
    # Step Transformer
    PromptType.NATURAL_LANGUAGE_TO_ACTION: NATURAL_LANGUAGE_TO_ACTION,
    PromptType.ENHANCE_SELECTOR: ENHANCE_SELECTOR,
    # Assertions
    PromptType.SEMANTIC_VALIDATION: SEMANTIC_VALIDATION,
    PromptType.VISUAL_DESCRIPTION: VISUAL_DESCRIPTION,
    PromptType.CONTENT_ANALYSIS: CONTENT_ANALYSIS,
    # Self-Healing
    PromptType.SELECTOR_RECOVERY: SELECTOR_RECOVERY,
    PromptType.ELEMENT_IDENTIFICATION: ELEMENT_IDENTIFICATION,
}


def get_prompt(prompt_type: PromptType) -> PromptTemplate:
    """Get a prompt template by type."""
    if prompt_type not in PROMPT_REGISTRY:
        raise ValueError(f"Unknown prompt type: {prompt_type}")
    return PROMPT_REGISTRY[prompt_type]


def format_prompt(
    prompt_type: PromptType,
    **kwargs: Any,
) -> tuple[str, str]:
    """
    Format a prompt template with the given variables.

    Returns:
        Tuple of (system_prompt, user_prompt)
    """
    template = get_prompt(prompt_type)

    # Format user prompt with provided kwargs
    user_prompt = template.user_prompt_template.format(**kwargs)

    return template.system_prompt, user_prompt


def get_prompt_config(prompt_type: PromptType) -> dict[str, Any]:
    """Get the recommended configuration for a prompt type."""
    template = get_prompt(prompt_type)
    return {
        "max_tokens": template.max_tokens,
        "temperature": template.temperature,
        "expected_format": template.expected_format,
    }
