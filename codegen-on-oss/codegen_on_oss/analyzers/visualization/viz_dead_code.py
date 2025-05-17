from abc import ABC
from typing import Any, Dict, List, Optional, Set, Union

import networkx as nx
from codegen.sdk.core.codebase import CodebaseType
from codegen.sdk.core.function import Function
from codegen.sdk.core.import_resolution import Import
from codegen.sdk.core.symbol import Symbol
from codegen.shared.enums.programming_language import ProgrammingLanguage

from tests.shared.skills.decorators import skill, skill_impl
from tests.shared.skills.skill import Skill
from tests.shared.skills.skill_test import SkillTestCase, SkillTestCasePyFile

PyDeadCodeTest = SkillTestCase(
    [
        SkillTestCasePyFile(
            input="""
# Live code
def used_function():
    return "I'm used!"

class UsedClass:
    def used_method(self):
        return "I'm a used method!"

# Dead code
def unused_function():
    return "I'm never called!"

class UnusedClass:
    def unused_method(self):
        return "I'm never used!"

# Second-order dead code
def second_order_dead():
    unused_function()
    UnusedClass().unused_method()

# More live code
def another_used_function():
    return used_function()

# Main execution
def main():
    print(used_function())
    print(UsedClass().used_method())
    print(another_used_function())

if __name__ == "__main__":
    main()
""",
            filepath="example.py",
        ),
        SkillTestCasePyFile(
            input="""
# This file should be ignored by the DeadCode skill

from example import used_function, UsedClass

def test_used_function():
    assert used_function() == "I'm used!"

def test_used_class():
    assert UsedClass().used_method() == "I'm a used method!"
""",
            filepath="test_example.py",
        ),
        SkillTestCasePyFile(
            input="""
# This file contains a decorated function that should be ignored

from functools import lru_cache

@lru_cache
def cached_function():
    return "I'm cached!"

# This function is dead code but should be ignored due to decoration
@deprecated
def old_function():
    return "I'm old but decorated!"

# This function is dead code and should be detected
def real_dead_code():
    return "I'm really dead!"
""",
            filepath="decorated_functions.py",
        ),
    ],
    graph=True,
)


@skill(
    eval_skill=False,
    prompt="Show me a visualization of the call graph from my_class and filter out test files and include only the methods that have the name post, get, patch, delete",
    uid="ec5e98c9-b57f-43f8-8b3c-af1b30bb91e6",
)
class DeadCode(Skill, ABC):
    """This skill shows a visualization of the dead code in the codebase.
    It iterates through all functions in the codebase, identifying those
    that have no usages and are not in test files or decorated. These functions
    are considered 'dead code' and are added to a directed graph. The skill
    then explores the dependencies of these dead code functions, adding them to
    the graph as well. This process helps to identify not only directly unused code
    but also code that might only be used by other dead code (second-order dead code).
    The resulting visualization provides a clear picture of potentially removable code,
    helping developers to clean up and optimize their codebase.
    """

    @staticmethod
    @skill_impl(test_cases=[PyDeadCodeTest], language=ProgrammingLanguage.PYTHON)
    @skill_impl(test_cases=[], skip_test=True, language=ProgrammingLanguage.TYPESCRIPT)
    def skill_func(codebase: CodebaseType) -> None:
        # Create a directed graph
        G = nx.DiGraph()

        # Get all functions in the codebase
        all_functions = codebase.get_all_functions()

        # Create a set to track used functions
        used_functions: Set[Function] = set()

        # Find the entry point function (e.g., main function or any function that's called from outside)
        entry_points = []
        for func in all_functions:
            # Check if the function is imported elsewhere
            if func.usages:
                entry_points.append(func)
                used_functions.add(func)

        # Recursively mark all functions that are called from entry points
        def mark_used_functions(func: Function) -> None:
            for call in func.function_calls:
                called_func = call.function_definition
                if isinstance(called_func, Function) and called_func not in used_functions:
                    used_functions.add(called_func)
                    mark_used_functions(called_func)

        # Mark all functions that are called from entry points
        for entry_point in entry_points:
            mark_used_functions(entry_point)

        # Find dead code (functions that are not used)
        dead_functions = [func for func in all_functions if func not in used_functions]

        # Add all functions to the graph
        for func in all_functions:
            if func in used_functions:
                G.add_node(func, color="green", status="used")
            else:
                G.add_node(func, color="red", status="unused")

        # Add edges for function calls
        for func in all_functions:
            for call in func.function_calls:
                called_func = call.function_definition
                if isinstance(called_func, Function):
                    G.add_edge(func, called_func)

        # Visualize the graph
        codebase.visualize(G)

    @staticmethod
    def _process_dependencies(dead_code: List[Function], graph: nx.DiGraph) -> None:
        """Process dependencies of dead code functions.

        Args:
            dead_code: List of functions identified as dead code
            graph: NetworkX graph to visualize the dead code
        """
        # Identify second-order dead code (functions only called by dead code)
        second_order_dead: Set[Function] = set()

        # Check each dead function's calls
        for dead_func in dead_code:
            for call in dead_func.function_calls:
                called_func = call.function_definition
                if isinstance(called_func, Function):
                    # Check if this function is only called by dead code
                    is_second_order = True
                    for usage in called_func.symbol_usages:
                        # If used by a function not in dead_code, it's not second-order dead
                        if usage.parent_function not in dead_code:
                            is_second_order = False
                            break

                    if is_second_order and called_func not in dead_code:
                        second_order_dead.add(called_func)
                        # Add to graph as second-order dead code
                        graph.add_node(called_func, color="orange")

                    # Add edge to show the call relationship
                    graph.add_edge(dead_func, called_func)
