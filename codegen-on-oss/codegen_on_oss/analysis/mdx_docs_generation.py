"""
MDX Documentation Generation Module

This module provides functions for generating MDX documentation from code.
"""

from typing import Any, Dict, List, Optional

from codegen import Codebase
from codegen.sdk.core.class_def import Class
from codegen.sdk.core.function import Function
from codegen.sdk.core.parameter import Parameter
from codegen.shared.logging.get_logger import get_logger

logger = get_logger(__name__)


class ClassDocumentation:
    """Class for storing documentation about a class."""
    
    def __init__(self, cls: Class, codebase: Codebase):
        """
        Initialize a ClassDocumentation object.
        
        Args:
            cls: The class to document
            codebase: The codebase containing the class
        """
        self.cls = cls
        self.codebase = codebase
        self.name = cls.name
        self.docstring = cls.docstring or ""
        self.methods = []
        self.properties = []
        self.base_classes = []
        
        # Extract methods and properties
        for method in cls.methods:
            self.methods.append({
                "name": method.name,
                "docstring": method.docstring or "",
                "parameters": [
                    {
                        "name": param.name,
                        "type": param.type_annotation or "Any",
                        "default": param.default_value,
                        "description": _extract_param_description(method.docstring or "", param.name)
                    }
                    for param in method.parameters
                ],
                "return_type": method.return_type or "None",
                "return_description": _extract_return_description(method.docstring or "")
            })
        
        # Extract properties
        for prop in cls.properties:
            self.properties.append({
                "name": prop.name,
                "type": prop.type_annotation or "Any",
                "docstring": prop.docstring or ""
            })
        
        # Extract base classes
        for base in cls.base_classes:
            self.base_classes.append(base.name)


def _extract_param_description(docstring: str, param_name: str) -> str:
    """
    Extract the description of a parameter from a docstring.
    
    Args:
        docstring: The docstring to extract from
        param_name: The name of the parameter
        
    Returns:
        The description of the parameter, or an empty string if not found
    """
    import re
    
    # Look for param in Args section
    args_pattern = r"Args:.*?(?:Parameters:|Returns:|Raises:|Yields:|Examples:|Notes:|Attributes:|Warnings:|Todo:|References:|See Also:|\Z)"
    args_match = re.search(args_pattern, docstring, re.DOTALL)
    
    if args_match:
        args_section = args_match.group(0)
        param_pattern = rf"{param_name}:\s*(.*?)(?:\n\s*\w+:|$)"
        param_match = re.search(param_pattern, args_section, re.DOTALL)
        
        if param_match:
            return param_match.group(1).strip()
    
    return ""


def _extract_return_description(docstring: str) -> str:
    """
    Extract the description of the return value from a docstring.
    
    Args:
        docstring: The docstring to extract from
        
    Returns:
        The description of the return value, or an empty string if not found
    """
    import re
    
    # Look for Returns section
    returns_pattern = r"Returns:\s*(.*?)(?:Raises:|Yields:|Examples:|Notes:|Attributes:|Warnings:|Todo:|References:|See Also:|\Z)"
    returns_match = re.search(returns_pattern, docstring, re.DOTALL)
    
    if returns_match:
        return returns_match.group(1).strip()
    
    return ""


def create_class_doc(cls: Class, codebase: Codebase) -> ClassDocumentation:
    """
    Create a ClassDocumentation object for a class.
    
    Args:
        cls: The class to document
        codebase: The codebase containing the class
        
    Returns:
        A ClassDocumentation object
    """
    return ClassDocumentation(cls, codebase)


def render_mdx_page_for_class(class_doc: ClassDocumentation) -> str:
    """
    Render an MDX page for a class.
    
    Args:
        class_doc: The ClassDocumentation object to render
        
    Returns:
        An MDX string
    """
    mdx = f"# {class_doc.name}\n\n"
    
    # Add docstring
    if class_doc.docstring:
        mdx += f"{class_doc.docstring}\n\n"
    
    # Add inheritance
    if class_doc.base_classes:
        mdx += "## Inheritance\n\n"
        mdx += f"Inherits from: {', '.join(class_doc.base_classes)}\n\n"
    
    # Add properties
    if class_doc.properties:
        mdx += "## Properties\n\n"
        for prop in class_doc.properties:
            mdx += f"### {prop['name']}\n\n"
            mdx += f"**Type:** `{prop['type']}`\n\n"
            if prop['docstring']:
                mdx += f"{prop['docstring']}\n\n"
    
    # Add methods
    if class_doc.methods:
        mdx += "## Methods\n\n"
        for method in class_doc.methods:
            # Format parameters
            params = []
            for param in method['parameters']:
                default = f" = {param['default']}" if param['default'] else ""
                params.append(f"{param['name']}: {param['type']}{default}")
            
            # Method signature
            mdx += f"### {method['name']}({', '.join(params)}) -> {method['return_type']}\n\n"
            
            # Method docstring
            if method['docstring']:
                mdx += f"{method['docstring']}\n\n"
            
            # Parameters table
            if method['parameters']:
                mdx += "#### Parameters\n\n"
                mdx += "| Name | Type | Description |\n"
                mdx += "| ---- | ---- | ----------- |\n"
                for param in method['parameters']:
                    mdx += f"| `{param['name']}` | `{param['type']}` | {param['description']} |\n"
                mdx += "\n"
            
            # Return value
            if method['return_type'] != "None":
                mdx += "#### Returns\n\n"
                mdx += f"**Type:** `{method['return_type']}`\n\n"
                if method['return_description']:
                    mdx += f"{method['return_description']}\n\n"
    
    return mdx

