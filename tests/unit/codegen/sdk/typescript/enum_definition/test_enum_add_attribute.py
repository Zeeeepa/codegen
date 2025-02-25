from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.sdk.enums import SymbolType
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_enum_definition_add_attribute_from_source(tmpdir) -> None:
    # language=typescript
    src_content = """
enum Color {
    Red,
    Green
}
"""

    with get_codebase_session(tmpdir=tmpdir, files={"src.ts": src_content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        src_file = codebase.get_file("src.ts")
        color_enum = next(s for s in src_file.symbols if s.symbol_type == SymbolType.Enum and s.name == "Color")
        color_enum.add_attribute_from_source("Blue")
    # language=typescript
    assert (
        src_file.content
        == """
enum Color {
    Red,
    Green,
    Blue,
}
"""
    )


def test_enum_definition_add_attribute_adds_source(tmpdir) -> None:
    # language=typescript
    content = """
enum Color {
    Red,
    Green
}

enum Size {
    Small = "small",
    Medium = "medium"
}
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("test.ts")

        color_enum = next(s for s in file.symbols if s.symbol_type == SymbolType.Enum and s.name == "Color")
        size_enum = next(s for s in file.symbols if s.symbol_type == SymbolType.Enum and s.name == "Size")
        color_enum.add_attribute(size_enum.get_attribute("Small"))
    # language=typescript
    assert (
        file.content
        == """
enum Color {
    Red,
    Green,
    Small = "small",
}

enum Size {
    Small = "small",
    Medium = "medium"
}
"""
    )


def test_enum_definition_add_attribute_include_deps(tmpdir) -> None:
    # language=typescript
    src_content = """
import { SizeType } from './types';

enum Size {
    Small = SizeType.Small,
    Medium = SizeType.Medium
}
"""
    # language=typescript
    dest_content = """
enum Color {
    Red,
    Green
}
"""
    with get_codebase_session(tmpdir=tmpdir, files={"src.ts": src_content, "dest.ts": dest_content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        src_file = codebase.get_file("src.ts")
        dest_file = codebase.get_file("dest.ts")

        color_enum = next(s for s in dest_file.symbols if s.symbol_type == SymbolType.Enum and s.name == "Color")
        size_enum = next(s for s in src_file.symbols if s.symbol_type == SymbolType.Enum and s.name == "Size")
        color_enum.add_attribute(size_enum.get_attribute("Small"), include_dependencies=True)

    # language=typescript
    assert (
        dest_file.content
        == """import { SizeType } from './types';

enum Color {
    Red,
    Green,
    Small = SizeType.Small,
}
"""
    )
