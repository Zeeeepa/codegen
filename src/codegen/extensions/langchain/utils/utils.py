from langchain_core.language_models import LLM


def get_max_model_input_tokens(llm: LLM) -> int:
    """Get the maximum input tokens for the current model.

    Returns:
        int: Maximum number of input tokens supported by the model
    """
    # Get model name - handle both .model and .model_name attributes
    model_name = getattr(llm, 'model', None) or getattr(llm, 'model_name', '')
    model_name_lower = model_name.lower() if model_name else ''
    
    # For Claude models not explicitly listed, if model name contains "claude", use Claude's limit
    if "claude" in model_name_lower:
        return 200000
    # For GPT-4 models
    elif "gpt-4" in model_name_lower:
        return 128000
    # For Grok models
    elif "grok" in model_name_lower:
        return 1000000
    # For GLM models (Z.ai)
    elif "glm" in model_name_lower:
        return 200000  # GLM-4.7 supports 200K context

    # default to gpt as it's lower bound
    return 128000
