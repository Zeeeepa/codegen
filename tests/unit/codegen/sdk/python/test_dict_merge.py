from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_dict_merge(tmpdir) -> None:
    content = """
dict1 = {'a': 1, 'b': 2}
dict2 = {'b': 3, 'c': 4, **extra_props}
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": content}, programming_language=ProgrammingLanguage.PYTHON) as codebase:
        file = codebase.get_file("test.py")

        dict1 = file.get_symbol("dict1").value
        dict2 = file.get_symbol("dict2").value

        # Merge the dictionaries
        merged_dict = dict1.merge(dict2)

        # Check that the merged dictionary has all keys
        assert "a" in merged_dict
        assert "b" in merged_dict
        assert "c" in merged_dict

        # Check that values from dict2 take precedence
        assert merged_dict["a"] == "1"
        assert merged_dict["b"] == "3"
        assert merged_dict["c"] == "4"

        # Check that spread elements are included
        assert len(merged_dict.spread_elements) == 1
        assert merged_dict.spread_elements[0] == "**extra_props"
