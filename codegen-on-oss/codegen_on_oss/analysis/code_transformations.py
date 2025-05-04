"""
Code Transformation Module for Codegen-on-OSS

This module provides functions for transforming code in various ways, such as
converting positional arguments to keyword arguments in function calls.
"""

from typing import Dict, List, Optional, Union

from codegen import Codebase
from codegen.sdk.core.function import Function
from codegen.sdk.core.function_call import FunctionCall
from codegen.shared.logging.get_logger import get_logger

logger = get_logger(__name__)


def convert_call_to_kwargs(
    function_call: FunctionCall, 
    function_def: Optional[Function] = None
) -> bool:
    """
    Convert a function call's positional arguments to keyword arguments.

    This function attempts to convert positional arguments in a function call to
    keyword arguments. If the function definition is provided, it uses the parameter
    names from the definition. Otherwise, it cannot perform the conversion.

    Args:
        function_call: The function call to convert
        function_def: The function definition, if available

    Returns:
        True if the conversion was successful, False otherwise
    """
    try:
        # Skip if there are no positional arguments
        if not function_call.args:
            return True

        # Skip if all arguments are already keyword arguments
        if all(arg.keyword for arg in function_call.args):
            return True

        # If we have the function definition, use it to get parameter names
        if function_def is not None:
            param_names = [param.name for param in function_def.parameters]

            # Check if we have enough parameter names for the positional arguments
            positional_args = [arg for arg in function_call.args if not arg.keyword]
            if len(positional_args) > len(param_names):
                logger.warning(
                    f"Cannot convert all positional arguments to kwargs for {function_call.name}: "
                    f"Not enough parameter names ({len(param_names)}) for positional arguments ({len(positional_args)})"
                )
                return False

            # Convert positional arguments to keyword arguments
            for i, arg in enumerate(function_call.args):
                if not arg.keyword and i < len(param_names):
                    arg.keyword = param_names[i]

            return True

        # If we don't have the function definition, we can't convert
        logger.warning(
            f"Cannot convert call to {function_call.name} to kwargs: function definition not available"
        )
        return False
    except Exception as e:
        logger.error(f"Error converting call to {function_call.name} to kwargs: {str(e)}")
        return False


def convert_all_calls_to_kwargs(
    codebase: Codebase, target_functions: Optional[List[str]] = None, ignore_errors: bool = False
) -> Dict[str, Union[int, List[str]]]:
    """
    Convert all function calls in the codebase to use keyword arguments.

    This function iterates through all function calls in the codebase and attempts
    to convert positional arguments to keyword arguments. It can be restricted to
    specific target functions.

    Args:
        codebase: The codebase to transform
        target_functions: Optional list of function names to target (if None, converts all calls)
        ignore_errors: Whether to continue processing if errors occur (default: False)

    Returns:
        A dictionary with conversion statistics:
        - 'converted_count': The number of function calls successfully converted
        - 'failed_conversions': List of function calls that could not be converted
        - 'skipped_count': The number of function calls skipped (already using kwargs)
    """
    converted_count = 0
    skipped_count = 0
    failed_conversions = []

    try:
        # Build a dictionary of function definitions for quick lookup
        function_defs = {func.name: func for func in codebase.functions}

        # Process all function calls in the codebase
        for file in codebase.files:
            for function in file.functions:
                for statement in function.code_block.statements:
                    for call in statement.function_calls:
                        try:
                            # Skip if we're only targeting specific functions and this isn't one of them
                            if target_functions and call.name not in target_functions:
                                skipped_count += 1
                                continue

                            # Get the function definition if available
                            function_def = function_defs.get(call.name)

                            # Skip if all arguments are already keyword arguments
                            if all(arg.keyword for arg in call.args):
                                skipped_count += 1
                                continue

                            # Convert the call
                            if convert_call_to_kwargs(call, function_def):
                                converted_count += 1
                            else:
                                failed_conversions.append(
                                    f"{call.name} at {file.path}:{function.start_line}"
                                )
                        except Exception as e:
                            error_msg = (
                                f"Error processing call to {call.name} in {file.path}: {str(e)}"
                            )
                            logger.error(error_msg)
                            failed_conversions.append(error_msg)
                            if not ignore_errors:
                                raise

        logger.info(f"Converted {converted_count} function calls to use keyword arguments")
        logger.info(
            f"Skipped {skipped_count} function calls (already using kwargs or not in target list)"
        )
        if failed_conversions:
            logger.warning(f"Failed to convert {len(failed_conversions)} function calls")

        return {
            "converted_count": converted_count,
            "failed_conversions": failed_conversions,
            "skipped_count": skipped_count,
        }
    except Exception as e:
        logger.error(f"Error in convert_all_calls_to_kwargs: {str(e)}")
        return {
            "converted_count": converted_count,
            "failed_conversions": failed_conversions + [f"Global error: {str(e)}"],
            "skipped_count": skipped_count,
        }
