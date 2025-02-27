from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.shared.enums.programming_language import ProgrammingLanguage
from codegen.sdk.python.symbol_groups.dict import PyDict


def test_dict_merge(tmpdir) -> None:
    content = """
extra_props = {'extra1': 'value1'}
dict1 = {'a': 1, 'b': 2}
dict2 = {'b': 3, 'c': 4, **extra_props}
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": content}, programming_language=ProgrammingLanguage.PYTHON) as codebase:
        file = codebase.get_file("test.py")
        
        dict1_symbol = file.get_symbol("dict1")
        dict2_symbol = file.get_symbol("dict2")
        
        dict1 = dict1_symbol.value
        dict2 = dict2_symbol.value
        
        # Verify we have PyDict instances
        assert isinstance(dict1, PyDict)
        assert isinstance(dict2, PyDict)
        
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
