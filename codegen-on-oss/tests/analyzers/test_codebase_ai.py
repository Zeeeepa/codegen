#!/usr/bin/env python3
"""
Tests for the codebase_ai module.
"""

import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Add the parent directory to the path so we can import the module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from codegen_on_oss.analyzers.codebase_ai import (
    generate_system_prompt,
    generate_flag_system_prompt,
    generate_context,
    generate_tools,
    generate_flag_tools,
    CodebaseAI
)


class MockEditable:
    """Mock Editable class for testing."""
    
    @property
    def extended_source(self):
        return "def test_function():\n    return 'test'"


class MockFile:
    """Mock File class for testing."""
    
    @property
    def source(self):
        return "def test_function():\n    return 'test'"


class TestCodebaseAI(unittest.TestCase):
    """Test cases for the codebase_ai module."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.editable = MockEditable()
        self.file = MockFile()
        self.codebase_ai = CodebaseAI()
    
    def test_generate_system_prompt_no_target_no_context(self):
        """Test generating a system prompt with no target and no context."""
        prompt = generate_system_prompt()
        self.assertIn("Hey CodegenBot!", prompt)
        self.assertIn("Your job is to follow the instructions of the user.", prompt)
        self.assertNotIn("The user has provided some additional context", prompt)
    
    def test_generate_system_prompt_with_target(self):
        """Test generating a system prompt with a target."""
        prompt = generate_system_prompt(self.editable)
        self.assertIn("Hey CodegenBot!", prompt)
        self.assertIn("The user has just requested a response on the following code snippet:", prompt)
        self.assertIn("def test_function():", prompt)
        self.assertIn("return 'test'", prompt)
    
    def test_generate_system_prompt_with_context(self):
        """Test generating a system prompt with context."""
        prompt = generate_system_prompt(context="Test context")
        self.assertIn("Hey CodegenBot!", prompt)
        self.assertIn("The user has provided some additional context", prompt)
        self.assertIn("Test context", prompt)
    
    def test_generate_flag_system_prompt(self):
        """Test generating a flag system prompt."""
        prompt = generate_flag_system_prompt(self.editable)
        self.assertIn("You are now tasked with determining whether to flag the symbol", prompt)
        self.assertIn("def test_function():", prompt)
        self.assertIn("return 'test'", prompt)
    
    def test_generate_context_string(self):
        """Test generating context from a string."""
        context = generate_context("Test context")
        self.assertIn("====== Context ======", context)
        self.assertIn("Test context", context)
        self.assertIn("====================", context)
    
    def test_generate_context_editable(self):
        """Test generating context from an Editable."""
        context = generate_context(self.editable)
        self.assertIn("====== MockEditable ======", context)
        self.assertIn("def test_function():", context)
        self.assertIn("return 'test'", context)
    
    def test_generate_context_file(self):
        """Test generating context from a File."""
        context = generate_context(self.file)
        self.assertIn("====== MockFile======", context)
        self.assertIn("def test_function():", context)
        self.assertIn("return 'test'", context)
    
    def test_generate_context_list(self):
        """Test generating context from a list."""
        context = generate_context(["Test context 1", "Test context 2"])
        self.assertIn("Test context 1", context)
        self.assertIn("Test context 2", context)
    
    def test_generate_context_dict(self):
        """Test generating context from a dict."""
        context = generate_context({"key1": "value1", "key2": "value2"})
        self.assertIn("[[[ key1 ]]]", context)
        self.assertIn("value1", context)
        self.assertIn("[[[ key2 ]]]", context)
        self.assertIn("value2", context)
    
    def test_generate_tools(self):
        """Test generating tools."""
        tools = generate_tools()
        self.assertEqual(len(tools), 1)
        self.assertEqual(tools[0]["function"]["name"], "set_answer")
    
    def test_generate_flag_tools(self):
        """Test generating flag tools."""
        tools = generate_flag_tools()
        self.assertEqual(len(tools), 1)
        self.assertEqual(tools[0]["function"]["name"], "should_flag")
    
    def test_codebase_ai_class_methods(self):
        """Test CodebaseAI class methods."""
        # Test generate_system_prompt
        prompt = self.codebase_ai.generate_system_prompt(self.editable)
        self.assertIn("Hey CodegenBot!", prompt)
        self.assertIn("def test_function():", prompt)
        
        # Test generate_flag_system_prompt
        flag_prompt = self.codebase_ai.generate_flag_system_prompt(self.editable)
        self.assertIn("You are now tasked with determining whether to flag the symbol", flag_prompt)
        
        # Test generate_context
        context = self.codebase_ai.generate_context("Test context")
        self.assertIn("Test context", context)
        
        # Test generate_tools
        tools = self.codebase_ai.generate_tools()
        self.assertEqual(len(tools), 1)
        self.assertEqual(tools[0]["function"]["name"], "set_answer")
        
        # Test generate_flag_tools
        flag_tools = self.codebase_ai.generate_flag_tools()
        self.assertEqual(len(flag_tools), 1)
        self.assertEqual(flag_tools[0]["function"]["name"], "should_flag")


if __name__ == '__main__':
    unittest.main()

