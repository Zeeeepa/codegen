import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

docs = Path("./docs")
mint: Dict[str, Any] = json.load(open(docs / "mint.json"))


def render_page(page_str: str) -> str:
    """Render a single page from the docs"""
    return open(docs / (page_str + ".mdx")).read()


def render_group(page_strs: List[str]) -> str:
    """Render a group of pages from the docs"""
    return "\n\n".join([render_page(x) for x in page_strs])


def get_group(name: str) -> Optional[List[str]]:
    """Get a group of pages by name from the mint.json file"""
    group = next((x for x in mint["navigation"] if x.get("group") == name), None)
    if group:
        return group["pages"]
    return None


def render_groups(group_names: List[str]) -> str:
    """Render multiple groups of pages from the docs"""
    groups = [get_group(x) for x in group_names]
    # Filter out None values
    filtered_groups = [g for g in groups if g is not None]
    return "\n\n".join([render_group(g) for g in filtered_groups])


def get_system_prompt() -> str:
    """Generates a string system prompt based on the docs"""
    return render_groups(["Introduction", "Building with Codegen", "Tutorials"])
