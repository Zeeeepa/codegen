#!/usr/bin/env python3
"""
Tests for the analyzers.parser module.
"""

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add the parent directory to the path so we can import the module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from codegen_on_oss.analyzers.parser import (
    ASTNode,
    BaseParser,
    CodegenParser,
    PythonParser,
    JavaScriptParser,
    TypeScriptParser,
    create_parser,
    parse_file,
    parse_code,
    ParseError
)

class TestASTNode(unittest.TestCase):
    """Tests for the ASTNode class."""
    
    def test_init(self):
        """Test initialization of ASTNode."""
        node = ASTNode(
            node_type="function",
            value="test_func",
            start_position=(1, 1),
            end_position=(10, 10),
            metadata={"test": "value"}
        )
        
        self.assertEqual(node.node_type, "function")
        self.assertEqual(node.value, "test_func")
        self.assertEqual(node.start_position, (1, 1))
        self.assertEqual(node.end_position, (10, 10))
        self.assertEqual(node.metadata, {"test": "value"})
        self.assertEqual(node.children, [])
        self.assertIsNone(node.parent)
    
    def test_add_child(self):
        """Test adding a child to a node."""
        parent = ASTNode(node_type="class", value="TestClass")
        child = ASTNode(node_type="method", value="test_method")
        
        parent.add_child(child)
        
        self.assertEqual(len(parent.children), 1)
        self.assertEqual(parent.children[0], child)
        self.assertEqual(child.parent, parent)
    
    def test_find_nodes_by_type(self):
        """Test finding nodes by type."""
        root = ASTNode(node_type="file", value="test.py")
        class_node = ASTNode(node_type="class", value="TestClass")
        method1 = ASTNode(node_type="method", value="test_method1")
        method2 = ASTNode(node_type="method", value="test_method2")
        
        root.add_child(class_node)
        class_node.add_child(method1)
        class_node.add_child(method2)
        
        # Find all method nodes
        methods = root.find_nodes_by_type("method")
        self.assertEqual(len(methods), 2)
        self.assertEqual(methods[0].value, "test_method1")
        self.assertEqual(methods[1].value, "test_method2")
        
        # Find all class nodes
        classes = root.find_nodes_by_type("class")
        self.assertEqual(len(classes), 1)
        self.assertEqual(classes[0].value, "TestClass")
    
    def test_to_dict(self):
        """Test converting a node to a dictionary."""
        node = ASTNode(
            node_type="function",
            value="test_func",
            start_position=(1, 1),
            end_position=(10, 10),
            metadata={"test": "value"}
        )
        
        node_dict = node.to_dict()
        
        self.assertEqual(node_dict["type"], "function")
        self.assertEqual(node_dict["value"], "test_func")
        self.assertEqual(node_dict["start_position"], (1, 1))
        self.assertEqual(node_dict["end_position"], (10, 10))
        self.assertEqual(node_dict["metadata"], {"test": "value"})
        self.assertEqual(node_dict["children"], [])

class TestCodegenParser(unittest.TestCase):
    """Tests for the CodegenParser class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_codebase = MagicMock()
        self.parser = CodegenParser(language="python", codebase=self.mock_codebase)
    
    @patch('builtins.open', new_callable=unittest.mock.mock_open, read_data="def test_func():\n    pass\n")
    def test_parse_file(self, mock_open):
        """Test parsing a file."""
        # Mock the parse_code method to avoid actual parsing
        self.parser.parse_code = MagicMock(return_value=ASTNode(node_type="file", value="test.py"))
        
        result = self.parser.parse_file("test.py")
        
        # Verify that parse_code was called with the file content
        self.parser.parse_code.assert_called_once()
        self.assertEqual(result.node_type, "file")
        self.assertEqual(result.value, "test.py")
    
    def test_parse_code_simple(self):
        """Test parsing a simple code snippet."""
        code = """
def test_func():
    x = 1
    return x

class TestClass:
    def __init__(self):
        self.value = 0
    
    def test_method(self):
        return self.value
"""
        
        result = self.parser.parse_code(code, "test.py")
        
        # Verify the basic structure
        self.assertEqual(result.node_type, "file")
        self.assertEqual(result.value, "test.py")
        
        # Find all functions
        functions = result.find_nodes_by_type("function")
        self.assertEqual(len(functions), 1)
        self.assertEqual(functions[0].value, "test_func")
        
        # Find all classes
        classes = result.find_nodes_by_type("class")
        self.assertEqual(len(classes), 1)
        self.assertEqual(classes[0].value, "TestClass")
        
        # Find all methods
        methods = result.find_nodes_by_type("method")
        self.assertEqual(len(methods), 2)
        self.assertEqual(methods[0].value, "__init__")
        self.assertEqual(methods[1].value, "test_method")
    
    def test_get_symbols(self):
        """Test extracting symbols from an AST."""
        # Create a simple AST
        root = ASTNode(node_type="file", value="test.py")
        
        class_node = ASTNode(
            node_type="class",
            value="TestClass",
            start_position=(5, 1),
            end_position=(15, 1),
            metadata={"indentation": 0}
        )
        
        method_node = ASTNode(
            node_type="method",
            value="test_method",
            start_position=(7, 5),
            end_position=(9, 5),
            metadata={"indentation": 4, "class": "TestClass"}
        )
        
        func_node = ASTNode(
            node_type="function",
            value="test_func",
            start_position=(1, 1),
            end_position=(3, 1),
            metadata={"indentation": 0}
        )
        
        var_node = ASTNode(
            node_type="variable",
            value="test_var",
            start_position=(17, 1),
            end_position=(17, 10),
            metadata={}
        )
        
        root.add_child(func_node)
        root.add_child(class_node)
        class_node.add_child(method_node)
        root.add_child(var_node)
        
        # Get symbols
        symbols = self.parser.get_symbols(root)
        
        # Verify symbols
        self.assertEqual(len(symbols), 3)  # 1 class, 1 function, 1 variable
        
        # Check class symbol
        class_symbol = next(s for s in symbols if s["type"] == "class")
        self.assertEqual(class_symbol["name"], "TestClass")
        self.assertEqual(class_symbol["start_line"], 5)
        self.assertEqual(class_symbol["end_line"], 15)
        self.assertEqual(class_symbol["methods"], ["test_method"])
        
        # Check function symbol
        func_symbol = next(s for s in symbols if s["type"] == "function")
        self.assertEqual(func_symbol["name"], "test_func")
        self.assertEqual(func_symbol["start_line"], 1)
        self.assertEqual(func_symbol["end_line"], 3)
        
        # Check variable symbol
        var_symbol = next(s for s in symbols if s["type"] == "variable")
        self.assertEqual(var_symbol["name"], "test_var")
        self.assertEqual(var_symbol["line"], 17)
    
    def test_get_dependencies(self):
        """Test extracting dependencies from an AST."""
        # Create a simple AST with imports
        root = ASTNode(node_type="file", value="test.py")
        
        import1 = ASTNode(
            node_type="import",
            value="import os",
            start_position=(1, 1),
            end_position=(1, 9),
            metadata={}
        )
        
        import2 = ASTNode(
            node_type="import",
            value="import sys as system",
            start_position=(2, 1),
            end_position=(2, 20),
            metadata={}
        )
        
        import3 = ASTNode(
            node_type="import",
            value="from pathlib import Path",
            start_position=(3, 1),
            end_position=(3, 25),
            metadata={}
        )
        
        root.add_child(import1)
        root.add_child(import2)
        root.add_child(import3)
        
        # Get dependencies
        dependencies = self.parser.get_dependencies(root)
        
        # Verify dependencies
        self.assertEqual(len(dependencies), 3)
        
        # Check simple import
        os_import = next(d for d in dependencies if d.get("module") == "os")
        self.assertEqual(os_import["type"], "import")
        self.assertEqual(os_import["line"], 1)
        
        # Check import with alias
        sys_import = next(d for d in dependencies if d.get("module") == "sys")
        self.assertEqual(sys_import["type"], "import")
        self.assertEqual(sys_import["alias"], "system")
        self.assertEqual(sys_import["line"], 2)
        
        # Check from import
        path_import = next(d for d in dependencies if d.get("module") == "pathlib")
        self.assertEqual(path_import["type"], "from_import")
        self.assertEqual(path_import["name"], "Path")
        self.assertEqual(path_import["line"], 3)

class TestLanguageSpecificParsers(unittest.TestCase):
    """Tests for language-specific parsers."""
    
    def test_python_parser(self):
        """Test PythonParser initialization."""
        parser = PythonParser()
        self.assertEqual(parser.language, "python")
    
    def test_javascript_parser(self):
        """Test JavaScriptParser initialization."""
        parser = JavaScriptParser()
        self.assertEqual(parser.language, "javascript")
    
    def test_typescript_parser(self):
        """Test TypeScriptParser initialization."""
        parser = TypeScriptParser()
        self.assertEqual(parser.language, "typescript")
    
    def test_create_parser(self):
        """Test create_parser factory function."""
        python_parser = create_parser("python")
        self.assertIsInstance(python_parser, PythonParser)
        
        js_parser = create_parser("javascript")
        self.assertIsInstance(js_parser, JavaScriptParser)
        
        ts_parser = create_parser("typescript")
        self.assertIsInstance(ts_parser, TypeScriptParser)
        
        # Test case insensitivity
        py_parser = create_parser("PYTHON")
        self.assertIsInstance(py_parser, PythonParser)
        
        # Test unknown language
        generic_parser = create_parser("unknown")
        self.assertIsInstance(generic_parser, CodegenParser)
        self.assertEqual(generic_parser.language, "unknown")

class TestParserUtilityFunctions(unittest.TestCase):
    """Tests for parser utility functions."""
    
    @patch('codegen_on_oss.analyzers.parser.create_parser')
    def test_parse_file(self, mock_create_parser):
        """Test parse_file utility function."""
        # Setup mock parser
        mock_parser = MagicMock()
        mock_parser.parse_file.return_value = ASTNode(node_type="file", value="test.py")
        mock_create_parser.return_value = mock_parser
        
        # Call parse_file
        result = parse_file("test.py", "python")
        
        # Verify parser creation and method calls
        mock_create_parser.assert_called_once_with("python", None, None)
        mock_parser.parse_file.assert_called_once()
        self.assertEqual(result.node_type, "file")
        self.assertEqual(result.value, "test.py")
    
    @patch('codegen_on_oss.analyzers.parser.create_parser')
    def test_parse_code(self, mock_create_parser):
        """Test parse_code utility function."""
        # Setup mock parser
        mock_parser = MagicMock()
        mock_parser.parse_code.return_value = ASTNode(node_type="file", value="test.py")
        mock_create_parser.return_value = mock_parser
        
        # Call parse_code
        code = "def test(): pass"
        result = parse_code(code, "python", "test.py")
        
        # Verify parser creation and method calls
        mock_create_parser.assert_called_once_with("python", None, None)
        mock_parser.parse_code.assert_called_once_with(code, "test.py")
        self.assertEqual(result.node_type, "file")
        self.assertEqual(result.value, "test.py")
    
    @patch('codegen_on_oss.analyzers.parser.create_parser')
    def test_parse_file_auto_language_detection(self, mock_create_parser):
        """Test auto language detection in parse_file."""
        # Setup mock parser
        mock_parser = MagicMock()
        mock_parser.parse_file.return_value = ASTNode(node_type="file", value="test.py")
        mock_create_parser.return_value = mock_parser
        
        # Call parse_file with no language specified
        result = parse_file("test.py")
        
        # Verify parser creation with auto-detected language
        mock_create_parser.assert_called_once_with("python", None, None)
        mock_parser.parse_file.assert_called_once()

if __name__ == '__main__':
    unittest.main()

