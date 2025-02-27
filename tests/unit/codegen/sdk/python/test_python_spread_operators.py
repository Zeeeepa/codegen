from codegen.sdk.codebase.factory.get_session import get_codebase_graph_session
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_python_spread_operators(tmpdir) -> None:
    file = """
def function():
    extra_props = {'color': 'blue', 'size': 'large'}
    params = {'a': 1, 'b': 2, **extra_props}
    return params
"""
    with get_codebase_graph_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.PYTHON, files={"test.py": file}) as G:
        file = G.get_file("test.py")
        function = file.get_function("function")

        # Get the params assignment
        params_assignment = function.get_assignment("params")
        assert params_assignment is not None

        # Get the statement (PyDict) from the params assignment
        params_dict = params_assignment.value

        # Check that we can access the regular key-value pairs
        assert params_dict["a"] == "1"
        assert params_dict["b"] == "2"

        # Check that we can access the spread operator
        assert len(params_dict.spread_elements) == 1
        assert params_dict.spread_elements[0] == "**extra_props"
