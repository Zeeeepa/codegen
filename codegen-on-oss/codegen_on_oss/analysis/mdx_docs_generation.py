from typing import TYPE_CHECKING, Optional

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


def render_mdx_page_for_class(cls_doc: ClassDoc) -> str:
    """Renders the MDX for a single class"""
    return f"""{render_mdx_page_title(cls_doc)}
{render_mdx_inheritence_section(cls_doc)}
{render_mdx_attributes_section(cls_doc)}
{render_mdx_methods_section(cls_doc)}
"""


def render_mdx_page_title(cls_doc: ClassDoc, icon: Optional[str] = None) -> str:
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

<GithubLinkNote link="{cls_doc.github_url}" />"""
