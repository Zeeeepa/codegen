from codegen.sdk.codebase.factory.get_session import get_codebase_graph_session
from codegen.shared.enums.programming_language import ProgrammingLanguage
from codegen.sdk.typescript.detached_symbols.jsx.element import JSXElement


def test_jsx_spread_operators(tmpdir) -> None:
    file = """
import React from 'react';

function Component(props) {
  const extraProps = { color: 'blue', size: 'large' };
  return (
    <div params={{ a: 1, b: 2, ...extraProps }} />
  );
}
"""
    with get_codebase_graph_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.tsx": file}) as G:
        file = G.get_file("test.tsx")
        component = file.get_function("Component")
        
        # Get the div element
        div_element = component.jsx_elements[0]
        assert div_element.name == "div"
        
        # Get the params prop
        params_prop = div_element.get_prop("params")
        assert params_prop is not None
        
        # Get the statement (TSDict) from the params prop
        params_dict = params_prop.value.statement
        
        # Check that we can access the regular key-value pairs
        assert params_dict["a"] == "1"
        assert params_dict["b"] == "2"
        
        # Check that we can access the spread operator
        assert len(params_dict.spread_elements) == 1
        assert params_dict.spread_elements[0] == "...extraProps"
