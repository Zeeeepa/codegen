"""Tests for the mdx_docs_generation module."""

import unittest

from codegen_on_oss.analyzers.doc_utils.schemas import ClassDoc, MethodDoc, ParameterDoc
from codegen_on_oss.analyzers.mdx_docs_generation import (
    format_parameter_for_mdx,
    format_parameters_for_mdx,
    format_return_for_mdx,
    get_mdx_route_for_class,
    render_mdx_for_attribute,
    render_mdx_for_method,
    render_mdx_inheritence_section,
    render_mdx_page_for_class,
    render_mdx_page_title,
    resolve_type_string,
)


class TestMdxDocsGeneration(unittest.TestCase):
    """Test cases for the mdx_docs_generation module."""

    def setUp(self):
        """Set up test fixtures."""
        self.parameter_doc = ParameterDoc(
            name="test_param",
            description="A test parameter",
            type="str",
            default="'default'"
        )
        
        self.method_doc = MethodDoc(
            name="test_method",
            description="A test method",
            parameters=[self.parameter_doc],
            return_type=["bool"],
            return_description="Returns a boolean",
            method_type="method",
            code="def test_method(test_param: str = 'default') -> bool:",
            path="python/TestClass/test_method",
            raises=[],
            metainfo={},
            version="abc123",
            github_url="https://github.com/example/repo/blob/main/test.py"
        )
        
        self.attribute_doc = MethodDoc(
            name="test_attribute",
            description="A test attribute",
            parameters=[],
            return_type=["str"],
            return_description=None,
            method_type="attribute",
            code="test_attribute: str",
            path="python/TestClass/test_attribute",
            raises=[],
            metainfo={},
            version="abc123",
            github_url="https://github.com/example/repo/blob/main/test.py"
        )
        
        self.class_doc = ClassDoc(
            title="TestClass",
            description="A test class",
            content="class TestClass:\n    \"\"\"A test class\"\"\"\n    pass",
            path="python/TestClass",
            inherits_from=["BaseClass"],
            version="abc123",
            methods=[self.method_doc],
            attributes=[self.attribute_doc],
            github_url="https://github.com/example/repo/blob/main/test.py"
        )

    def test_render_mdx_page_title(self):
        """Test rendering MDX page title."""
        result = render_mdx_page_title(self.class_doc)
        self.assertIn('title: "TestClass"', result)
        self.assertIn('description: "A test class"', result)

    def test_render_mdx_inheritence_section(self):
        """Test rendering MDX inheritance section."""
        result = render_mdx_inheritence_section(self.class_doc)
        self.assertIn("### Inherits from", result)
        self.assertIn("BaseClass", result)

    def test_render_mdx_for_attribute(self):
        """Test rendering MDX for an attribute."""
        result = render_mdx_for_attribute(self.attribute_doc)
        self.assertIn('### <span className="text-primary">test_attribute</span>', result)
        self.assertIn('<Attribute type=', result)

    def test_render_mdx_for_method(self):
        """Test rendering MDX for a method."""
        result = render_mdx_for_method(self.method_doc)
        self.assertIn('### <span className="text-primary">test_method</span>', result)
        self.assertIn('<ParameterWrapper>', result)
        self.assertIn('<Return return_type=', result)

    def test_format_parameter_for_mdx(self):
        """Test formatting a parameter for MDX."""
        result = format_parameter_for_mdx(self.parameter_doc)
        self.assertIn('name="test_param"', result)
        self.assertIn('description="A test parameter"', result)
        self.assertIn('defaultValue="\'default\'"', result)

    def test_format_parameters_for_mdx(self):
        """Test formatting parameters for MDX."""
        result = format_parameters_for_mdx([self.parameter_doc])
        self.assertIn('<Parameter', result)
        self.assertIn('name="test_param"', result)

    def test_format_return_for_mdx(self):
        """Test formatting a return type for MDX."""
        result = format_return_for_mdx(["bool"], "Returns a boolean")
        self.assertIn('<Return return_type=', result)
        self.assertIn('description="Returns a boolean"', result)

    def test_get_mdx_route_for_class(self):
        """Test getting the MDX route for a class."""
        # Test Python class
        py_class_doc = ClassDoc(
            title="PyClass",
            description="A Python class",
            content="",
            path="",
            inherits_from=[],
            version="",
            github_url=""
        )
        self.assertEqual(get_mdx_route_for_class(py_class_doc), "codebase-sdk/python/PyClass")
        
        # Test TypeScript class
        ts_class_doc = ClassDoc(
            title="TsClass",
            description="A TypeScript class",
            content="",
            path="",
            inherits_from=[],
            version="",
            github_url=""
        )
        self.assertEqual(get_mdx_route_for_class(ts_class_doc), "codebase-sdk/typescript/TsClass")
        
        # Test core class
        core_class_doc = ClassDoc(
            title="CoreClass",
            description="A core class",
            content="",
            path="",
            inherits_from=[],
            version="",
            github_url=""
        )
        self.assertEqual(get_mdx_route_for_class(core_class_doc), "codebase-sdk/core/CoreClass")

    def test_resolve_type_string(self):
        """Test resolving a type string."""
        # Test simple type
        simple_result = resolve_type_string("str")
        self.assertIn('<code className="text-sm bg-gray-100 px-2 py-0.5 rounded">str</code>', simple_result)
        
        # Test complex type with link
        complex_result = resolve_type_string("<api-reference/core/Symbol>")
        self.assertIn("<>", complex_result)
        self.assertIn("[Symbol](/api-reference/core/Symbol)", complex_result)

    def test_render_mdx_page_for_class(self):
        """Test rendering a complete MDX page for a class."""
        result = render_mdx_page_for_class(self.class_doc)
        # Check that all sections are included
        self.assertIn('title: "TestClass"', result)
        self.assertIn("### Inherits from", result)
        self.assertIn("## Attributes", result)
        self.assertIn("## Methods", result)
        self.assertIn('test_attribute', result)
        self.assertIn('test_method', result)


if __name__ == "__main__":
    unittest.main()

