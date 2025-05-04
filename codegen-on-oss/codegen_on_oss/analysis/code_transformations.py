"""
Code Transformation Module for Codegen-on-OSS

This module provides functions for transforming code in various ways, such as
converting positional arguments to keyword arguments in function calls.
"""

from typing import List, Optional

from codegen import Codebase
from codegen.sdk.core.function import Function
from codegen.sdk.core.function_call import FunctionCall
from codegen.sdk.core.parameter import Parameter
from codegen.shared.logging.get_logger import get_logger

logger = get_logger(__name__)


def convert_call_to_kwargs(function_call: FunctionCall, function_def: Optional[Function] = None) -> bool:
    """
    Convert a function call's positional arguments to keyword arguments.

    Args:
        function_call: The function call to convert
        function_def: The function definition, if available

    Returns:
        True if the conversion was successful, False otherwise
    """
    # Skip if there are no positional arguments
    if not function_call.args:
        return True

    # Skip if all arguments are already keyword arguments
    if all(arg.keyword for arg in function_call.args):
        return True

    # If we have the function definition, use it to get parameter names
    if function_def is not None:
        param_names = [param.name for param in function_def.parameters]
        
        # Convert positional arguments to keyword arguments
        for i, arg in enumerate(function_call.args):
            if not arg.keyword and i < len(param_names):
                arg.keyword = param_names[i]
        
        return True
    
    # If we don't have the function definition, we can't convert
    logger.warning(f"Cannot convert call to {function_call.name} to kwargs: function definition not available")
    return False


def convert_all_calls_to_kwargs(codebase: Codebase, target_functions: Optional[List[str]] = None) -> int:
    """
    Convert all function calls in the codebase to use keyword arguments.

    Args:
        codebase: The codebase to transform
        target_functions: Optional list of function names to target (if None, converts all calls)

    Returns:
        The number of function calls converted
    """
    converted_count = 0
    
    # Build a dictionary of function definitions for quick lookup
    function_defs = {func.name: func for func in codebase.functions}
    
    # Process all function calls in the codebase
    for file in codebase.files:
        for function in file.functions:
            for statement in function.code_block.statements:
                for call in statement.function_calls:
                    # Skip if we're only targeting specific functions and this isn't one of them
                    if target_functions and call.name not in target_functions:
                        continue
                    
                    # Get the function definition if available
                    function_def = function_defs.get(call.name)
                    
                    # Convert the call
                    if convert_call_to_kwargs(call, function_def):
                        converted_count += 1
    
    logger.info(f"Converted {converted_count} function calls to use keyword arguments")
    return converted_count
"""

