from typing import TYPE_CHECKING, Optional, Any

if TYPE_CHECKING:
    pass

from codegen.sdk.code_generation.doc_utils.schemas import (
    ClassDoc,
)
from codegen.sdk.code_generation.doc_utils.utils import (
    sanitize_mdx_mintlify_description,
)
from codegen.shared.logging.get_logger import get_logger

logger = get_logger(__name__)


def render_mdx_page_for_class(cls_name: str, cls_obj: Any) -> str:
    """Render an MDX page for a class."""
    doc = cls_obj.__doc__ or ""
    
    # Render the class documentation
    mdx = f"# {cls_name}\n\n{doc}\n\n"
    
    # Add inheritance, attributes, and methods sections
    mdx += render_mdx_inheritance_section(cls_obj)
    mdx += render_mdx_attributes_section(cls_obj)
    mdx += render_mdx_methods_section(cls_obj)
    
    return mdx

def render_mdx_inheritance_section(cls_obj: Any) -> str:
    """Render the inheritance section of an MDX page."""
    bases = cls_obj.__bases__
    if bases == (object,):
        return ""
    
    base_names = [base.__name__ for base in bases]
    return f"## Inheritance\n\n{cls_obj.__name__} inherits from: {', '.join(base_names)}\n\n"

def render_mdx_attributes_section(cls_obj: Any) -> str:
    """Render the attributes section of an MDX page."""
    # Get all attributes that don't start with underscore
    attrs = [attr for attr in dir(cls_obj) if not attr.startswith('_') and not callable(getattr(cls_obj, attr))]
    
    if not attrs:
        return ""
    
    mdx = "## Attributes\n\n"
    for attr in attrs:
        mdx += f"### {attr}\n\n"
        # Try to get the type and docstring
        try:
            attr_value = getattr(cls_obj, attr)
            attr_type = type(attr_value).__name__
            mdx += f"Type: `{attr_type}`\n\n"
        except Exception:
            pass
    
    return mdx

def render_mdx_methods_section(cls_obj: Any) -> str:
    """Render the methods section of an MDX page."""
    # Get all methods that don't start with underscore
    methods = [method for method in dir(cls_obj) if not method.startswith('_') and callable(getattr(cls_obj, method))]
    
    if not methods:
        return ""
    
    mdx = "## Methods\n\n"
    for method in methods:
        method_obj = getattr(cls_obj, method)
        doc = method_obj.__doc__ or ""
        mdx += f"### {method}\n\n{doc}\n\n"
    
    return mdx
