import os
import re
from pathlib import Path
from typing import TYPE_CHECKING, Dict, List, Optional

if TYPE_CHECKING:
    from codegen import Codebase

from codegen.sdk.code_generation.doc_utils.schemas import (
    ClassDoc,
    MethodDoc,
    ParameterDoc,
)
from codegen.sdk.code_generation.doc_utils.utils import (
    sanitize_html_for_mdx,
    sanitize_mdx_mintlify_description,
)
from codegen.sdk.core.class_definition import Class
from codegen.shared.logging.get_logger import get_logger

logger = get_logger(__name__)


def render_mdx_page_for_class(cls_doc: ClassDoc) -> str:
    """Renders the MDX for a single class"""
    return f"""{render_mdx_page_title(cls_doc)}
{render_mdx_inheritence_section(cls_doc)}
{render_mdx_attributes_section(cls_doc)}
{render_mdx_methods_section(cls_doc)}
"""


def render_mdx_page_title(cls_doc: ClassDoc, icon: str | None = None) -> str:
    """Renders the MDX for the page title"""
    page_desc = cls_doc.description if hasattr(cls_doc, "description") else ""

    return f"""---
title: "{cls_doc.title}"
sidebarTitle: "{cls_doc.title}"
icon: "{icon if icon else ""}"
description: "{sanitize_mdx_mintlify_description(page_desc)}"
---
import {{Parameter}} from '/snippets/Parameter.mdx';
import {{ParameterWrapper}} from '/snippets/ParameterWrapper.mdx';
import {{Return}} from '/snippets/Return.mdx';
import {{HorizontalDivider}} from '/snippets/HorizontalDivider.mdx';
import {{GithubLinkNote}} from '/snippets/GithubLinkNote.mdx';
import {{Attribute}} from '/snippets/Attribute.mdx';

<GithubLinkNote link="{cls_doc.github_url}" />
"""


def render_mdx_inheritence_section(cls_doc: ClassDoc) -> str:
    """Renders the MDX for the inheritence section"""
    # Filter on parents who we have docs for
    parents = cls_doc.inherits_from
    if not parents:
        return ""
    parents_string = ", ".join([parse_link(parent) for parent in parents])
    return f"""### Inherits from
{parents_string}
"""


def render_mdx_attributes_section(cls_doc: ClassDoc) -> str:
    """Renders the MDX for the attributes section"""
    sorted_attributes = sorted(
        cls_doc.attributes
        + [method for method in cls_doc.methods if method.method_type == "property"],
        key=lambda x: x.name,
    )
    if len(sorted_attributes) <= 0:
        return ""
    attributes_mdx_string = "\n".join(
        [render_mdx_for_attribute(attribute) for attribute in sorted_attributes]
    )

    return f"""## Attributes
<HorizontalDivider />
{attributes_mdx_string}
"""


def render_mdx_methods_section(cls_doc: ClassDoc) -> str:
    """Renders the MDX for the methods section"""
    sorted_methods = sorted(cls_doc.methods, key=lambda x: x.name)
    if len(sorted_methods) <= 0:
        return ""
    methods_mdx_string = "\n".join(
        [
            render_mdx_for_method(method)
            for method in sorted_methods
            if method.method_type == "method"
        ]
    )

    return f"""## Methods
<HorizontalDivider />
{methods_mdx_string}
"""


def render_mdx_for_attribute(attribute: MethodDoc) -> str:
    """Renders the MDX for a single attribute"""
    attribute_docstring = sanitize_mdx_mintlify_description(attribute.description)
    if len(attribute.return_type) > 0:
        return_type = f"{resolve_type_string(attribute.return_type[0])}"
    else:
        return_type = ""
    if not attribute_docstring:
        attribute_docstring = "\n"
    return f"""### <span className="text-primary">{attribute.name}</span>
<HorizontalDivider light={{true}} />
<Attribute type={{ {return_type if return_type else "<span></span>"} }} description="{attribute_docstring}" />
"""


########################################################################################################################
# METHODS
########################################################################################################################


def format_parameter_for_mdx(parameter: ParameterDoc) -> str:
    type_string = resolve_type_string(parameter.type)
    return f"""
<Parameter
    name="{parameter.name}"
    type={{ {type_string} }}
    description="{sanitize_html_for_mdx(parameter.description)}"
    defaultValue="{sanitize_html_for_mdx(parameter.default)}"
/>
""".strip()


def format_parameters_for_mdx(parameters: list[ParameterDoc]) -> str:
    return "\n".join([format_parameter_for_mdx(parameter) for parameter in parameters])


def format_return_for_mdx(return_type: list[str], return_description: str) -> str:
    description = sanitize_html_for_mdx(return_description) if return_description else ""
    return_type_str = resolve_type_string(return_type[0])

    return f"""
<Return return_type={{ {return_type_str} }} description="{description}"/>
"""


def render_mdx_for_method(method: MethodDoc) -> str:
    description = sanitize_mdx_mintlify_description(method.description)
    
    # Add inheritance information if available
    inheritance_info = ""
    if hasattr(method, "inherited_from") and method.inherited_from:
        inheritance_info = f"\n\n*Inherited from {parse_link(method.inherited_from)}*"
    
    # Add links to related methods or classes if available
    related_links = ""
    if hasattr(method, "related_methods") and method.related_methods:
        related_methods = ", ".join([parse_link(rel) for rel in method.related_methods])
        related_links = f"\n\n*Related methods: {related_methods}*"
    
    mdx_string = f"""### <span className="text-primary">{method.name}</span>
{description}{inheritance_info}{related_links}
<GithubLinkNote link="{method.github_url}" />
"""
    if method.parameters:
        mdx_string += f"""
<ParameterWrapper>
{format_parameters_for_mdx(method.parameters)}
</ParameterWrapper>
"""
    if method.return_type:
        mdx_string += f"""
{format_return_for_mdx(method.return_type, method.return_description)}
"""

    return mdx_string


def get_mdx_route_for_class(cls_doc: ClassDoc) -> str:
    """Get the expected MDX route for a class
    split by /core, /python, and /typescript
    """
    lower_class_name = cls_doc.title.lower()
    if lower_class_name.startswith("py"):
        return f"codebase-sdk/python/{cls_doc.title}"
    elif lower_class_name.startswith(("ts", "jsx")):
        return f"codebase-sdk/typescript/{cls_doc.title}"
    else:
        return f"codebase-sdk/core/{cls_doc.title}"


def format_type_string(type_string: str) -> str:
    type_strings = type_string.split("|")
    return " | ".join([type_str.strip() for type_str in type_strings])


def resolve_type_string(type_string: str) -> str:
    if "<" in type_string:
        return f"<>{parse_link(type_string, href=True)}</>"
    else:
        return f'<code className="text-sm bg-gray-100 px-2 py-0.5 rounded">{format_type_string(type_string)}</code>'


def format_builtin_type_string(type_string: str) -> str:
    if "|" in type_string:
        type_strings = type_string.split("|")
        return " | ".join([type_str.strip() for type_str in type_strings])
    return type_string


def span_type_string_by_pipe(type_string: str) -> str:
    if "|" in type_string:
        type_strings = type_string.split("|")
        return " | ".join([f"<span>{type_str.strip()}</span>" for type_str in type_strings])
    return type_string


def parse_link(type_string: str, href: bool = False) -> str:
    # Match components with angle brackets, handling nested structures

    parts = [p for p in re.split(r"(<[^>]+>)", type_string) if p]

    result = []
    for part in parts:
        if part.startswith("<") and part.endswith(">"):
            # Extract the path from between angle brackets
            path = part[1:-1]
            symbol = path.split("/")[-1]

            # Create a Link object
            link = (
                f'<a href="/{path}" style={{ {{fontWeight: "inherit", fontSize: "inherit"}} }}>{symbol}</a>'
                if href
                else f"[{symbol}](/{path})"
            )
            result.append(link)
        else:
            part = format_builtin_type_string(part)
            if href:
                result.append(f"<span>{part.strip()}</span>")
            else:
                result.append(part.strip())

    return " ".join(result)


def generate_mdx_docs(
    codebase: "Codebase",
    output_dir: str,
    include_patterns: Optional[List[str]] = None,
    exclude_patterns: Optional[List[str]] = None,
) -> Dict[str, int]:
    """
    Generate MDX documentation for a codebase.

    Args:
        codebase: The codebase to generate documentation for
        output_dir: The directory to write the documentation to
        include_patterns: Optional list of patterns to include
        exclude_patterns: Optional list of patterns to exclude

    Returns:
        A dictionary with statistics about the generated documentation:
        - 'classes_count': Number of classes documented
        - 'files_count': Number of files generated
        - 'errors_count': Number of errors encountered
    """
    # Create output directory if it doesn't exist
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Statistics to return
    stats = {
        'classes_count': 0,
        'files_count': 0,
        'errors_count': 0
    }
    
    try:
        # Get all classes in the codebase
        classes = codebase.classes
        
        # Filter classes based on include/exclude patterns
        if include_patterns:
            classes = [cls for cls in classes if any(re.search(pattern, cls.name) for pattern in include_patterns)]
        
        if exclude_patterns:
            classes = [cls for cls in classes if not any(re.search(pattern, cls.name) for pattern in exclude_patterns)]
        
        # Generate documentation for each class
        for cls in classes:
            try:
                # Create ClassDoc object
                cls_doc = create_class_doc(cls, codebase)
                
                # Generate MDX content
                mdx_content = render_mdx_page_for_class(cls_doc)
                
                # Determine output file path
                route = get_mdx_route_for_class(cls_doc)
                file_path = output_path / f"{cls.name}.mdx"
                
                # Write MDX content to file
                with open(file_path, "w") as f:
                    f.write(mdx_content)
                
                logger.info(f"Generated MDX documentation for {cls.name} at {file_path}")
                stats['classes_count'] += 1
                stats['files_count'] += 1
            except Exception as e:
                logger.error(f"Error generating documentation for class {cls.name}: {str(e)}")
                stats['errors_count'] += 1
        
        # Generate index file
        try:
            generate_index_file(classes, output_path)
            stats['files_count'] += 1
            logger.info(f"Generated index file at {output_path / 'index.mdx'}")
        except Exception as e:
            logger.error(f"Error generating index file: {str(e)}")
            stats['errors_count'] += 1
        
        logger.info(f"Generated MDX documentation for {stats['classes_count']} classes in {output_dir}")
        return stats
    except Exception as e:
        logger.error(f"Error in generate_mdx_docs: {str(e)}")
        stats['errors_count'] += 1
        return stats


def create_class_doc(cls: Class, codebase: "Codebase") -> ClassDoc:
    """
    Create a ClassDoc object from a Class object.
    
    Args:
        cls: The class to create documentation for
        codebase: The codebase containing the class
        
    Returns:
        A ClassDoc object
    """
    # Extract class information
    methods = []
    attributes = []
    
    # Process methods
    for method in cls.methods:
        method_doc = MethodDoc(
            name=method.name,
            description=method.docstring or "",
            parameters=[
                ParameterDoc(
                    name=param.name,
                    type=param.type_annotation or "Any",
                    description=param.description or "",
                    default=param.default_value or "",
                )
                for param in method.parameters
            ],
            return_type=[method.return_type or "None"],
            return_description=method.return_description or "",
            method_type="method",
            github_url=f"https://github.com/{codebase.repo_name}/blob/main/{cls.file.path}#L{method.start_line}",
        )
        methods.append(method_doc)
    
    # Process attributes
    for attr in cls.attributes:
        attr_doc = MethodDoc(
            name=attr.name,
            description=attr.docstring or "",
            parameters=[],
            return_type=[attr.type_annotation or "Any"],
            return_description="",
            method_type="property",
            github_url=f"https://github.com/{codebase.repo_name}/blob/main/{cls.file.path}#L{attr.start_line}",
        )
        attributes.append(attr_doc)
    
    # Create ClassDoc
    return ClassDoc(
        title=cls.name,
        description=cls.docstring or "",
        methods=methods,
        attributes=attributes,
        inherits_from=[f"<{get_mdx_route_for_class(ClassDoc(title=parent.name, description='', methods=[], attributes=[]))}>" for parent in cls.superclasses],
        github_url=f"https://github.com/{codebase.repo_name}/blob/main/{cls.file.path}#L{cls.start_line}",
    )


def generate_index_file(classes: List[Class], output_path: Path) -> None:
    """
    Generate an index file for the MDX documentation.
    
    Args:
        classes: List of classes to include in the index
        output_path: Path to write the index file to
    """
    # Group classes by category
    categories = {
        "Core": [],
        "Python": [],
        "TypeScript": [],
        "Other": [],
    }
    
    for cls in classes:
        if cls.name.startswith("Py"):
            categories["Python"].append(cls)
        elif cls.name.startswith(("TS", "Jsx")):
            categories["TypeScript"].append(cls)
        elif cls.name in ["Codebase", "Symbol", "Function", "Class", "File"]:
            categories["Core"].append(cls)
        else:
            categories["Other"].append(cls)
    
    # Generate index content
    content = """---
title: "API Reference"
sidebarTitle: "API Reference"
description: "Complete API reference for the Codegen SDK"
---

# Codegen SDK API Reference

This is the complete API reference for the Codegen SDK.

"""
    
    # Add categories
    for category, category_classes in categories.items():
        if not category_classes:
            continue
            
        content += f"## {category}\n\n"
        
        # Sort classes by name
        category_classes.sort(key=lambda x: x.name)
        
        # Add links to classes
        for cls in category_classes:
            cls_doc = ClassDoc(title=cls.name, description=cls.docstring or "", methods=[], attributes=[])
            route = get_mdx_route_for_class(cls_doc)
            content += f"- [{cls.name}]({route}): {cls.docstring.split('.')[0] if cls.docstring else ''}\n"
        
        content += "\n"
    
    # Write index file
    with open(output_path / "index.mdx", "w") as f:
        f.write(content)
    
    logger.info(f"Generated index file at {output_path / 'index.mdx'}")
