from codegen.cli.utils.types import DecoratedFunction
import ast
import dataclasses
import importlib
import importlib.util
from dataclasses import dataclass
from pathlib import Path


class CodegenFunctionVisitor(ast.NodeVisitor):
    def __init__(self):
        self.functions: list[DecoratedFunction] = []

    def get_function_body(self, node: ast.FunctionDef) -> str:
        """Extract and unindent the function body."""
        # Get the start and end positions of the function body
        first_stmt = node.body[0]
        last_stmt = node.body[-1]

        # Get the line numbers (1-based in source lines)
        start_line = first_stmt.lineno - 1  # Convert to 0-based
        end_line = last_stmt.end_lineno if hasattr(last_stmt, "end_lineno") else last_stmt.lineno

        # Get the raw source lines for the entire body
        source_lines = self.source.splitlines()[start_line:end_line]

        # Find the minimum indentation of non-empty lines
        indents = [len(line) - len(line.lstrip()) for line in source_lines if line.strip()]
        if not indents:
            return ""

        min_indent = min(indents)

        # Remove the minimum indentation from each line
        unindented_lines = []
        for line in source_lines:
            if line.strip():  # Non-empty line
                unindented_lines.append(line[min_indent:])
            else:  # Empty line
                unindented_lines.append("")

        return "\n".join(unindented_lines)

    def _get_annotation(self, annotation) -> str:
        """Helper function to retrieve the string representation of an annotation.

        Args:
            annotation: The annotation node.

        Returns:
            str: The string representation of the annotation.

        """
        if isinstance(annotation, ast.Name):
            return annotation.id
        elif isinstance(annotation, ast.Subscript):
            return f"{self._get_annotation(annotation.value)}[{self._get_annotation(annotation.slice)}]"
        elif isinstance(annotation, ast.Attribute):
            return f"{self._get_annotation(annotation.value)}.{annotation.attr}"
        elif isinstance(annotation, ast.Tuple):
            return ", ".join(self._get_annotation(elt) for elt in annotation.elts)
        else:
            return "Any"

    def get_function_parameters(self, node: ast.FunctionDef) -> list[tuple[str, str | None]]:
        """Extracts the parameters and their types from an AST FunctionDef node.

        Args:
            node (ast.FunctionDef): The AST node of the function.

        Returns:
            List[Tuple[str, Optional[str]]]: A list of tuples containing parameter names and their type annotations.
                                            The type is `None` if no annotation is present.

        """
        parameters = []
        for arg in node.args.args:
            param_name = arg.arg
            if arg.annotation:
                param_type = ast.unparse(arg.annotation) if hasattr(ast, "unparse") else self._get_annotation(arg.annotation)
            else:
                param_type = None
            parameters.append((param_name, param_type))

        # Handle *args
        if node.args.vararg:
            param_name = f"*{node.args.vararg.arg}"
            if node.args.vararg.annotation:
                param_type = ast.unparse(node.args.vararg.annotation) if hasattr(ast, "unparse") else self._get_annotation(node.args.vararg)
            else:
                param_type = None
            parameters.append((param_name, param_type))

        # Handle **kwargs
        if node.args.kwarg:
            param_name = f"**{node.args.kwarg.arg}"
            if node.args.kwarg.annotation:
                param_type = ast.unparse(node.args.kwarg.annotation) if hasattr(ast, "unparse") else self._get_annotation(node.args.kwarg)
            else:
                param_type = None
            parameters.append((param_name, param_type))

        return parameters

    def visit_FunctionDef(self, node):
        for decorator in node.decorator_list:
            if (
                isinstance(decorator, ast.Call)
                and len(decorator.args) >= 1
                and (
                    # Check if it's a direct codegen.X call
                    (isinstance(decorator.func, ast.Attribute) and isinstance(decorator.func.value, ast.Name) and decorator.func.value.id == "codegen")
                    or
                    # Check if it starts with codegen.anything.anything...
                    (isinstance(decorator.func, ast.Attribute) and isinstance(decorator.func.value, ast.Attribute) and self._has_codegen_root(decorator.func.value))
                )
            ):
                # Get the function name from the decorator argument
                func_name = ast.literal_eval(decorator.args[0])

                # Get additional metadata for webhook
                lint_mode = decorator.func.attr == "webhook"
                lint_user_whitelist = []
                if lint_mode and len(decorator.keywords) > 0:
                    for keyword in decorator.keywords:
                        if keyword.arg == "users" and isinstance(keyword.value, ast.List):
                            lint_user_whitelist = [ast.literal_eval(elt).lstrip("@") for elt in keyword.value.elts]

                # Get just the function body, unindented
                body_source = self.get_function_body(node)
                parameters = self.get_function_parameters(node)
                self.functions.append(DecoratedFunction(name=func_name, source=body_source, lint_mode=lint_mode, lint_user_whitelist=lint_user_whitelist, parameters=parameters))

    def _has_codegen_root(self, node):
        """Recursively check if an AST node chain starts with codegen."""
        if isinstance(node, ast.Name):
            return node.id == "codegen"
        elif isinstance(node, ast.Attribute):
            return self._has_codegen_root(node.value)
        return False

    def _get_decorator_attrs(self, node):
        """Get all attribute names in a decorator chain."""
        attrs = []
        while isinstance(node, ast.Attribute):
            attrs.append(node.attr)
            node = node.value
        return attrs

    def visit_Module(self, node):
        # Store the full source code for later use
        self.source = self.file_content
        self.generic_visit(node)


def _extract_arguments_type_schema(func: DecoratedFunction) -> dict | None:
    """Extracts the arguments type schema from a DecoratedFunction object."""
    try:
        spec = importlib.util.spec_from_file_location("module", func.filepath)
        module = importlib.util.module_from_spec(spec)

        fn_arguments_param_type = None
        for p in func.parameters:
            if p[0] == "arguments":
                fn_arguments_param_type = p[1]

        if fn_arguments_param_type is not None:
            spec.loader.exec_module(module)

            schema = getattr(module, fn_arguments_param_type).model_json_schema()
            return schema
        return None
    except Exception as e:
        print(f"Error parsing {func.filepath}, could not introspect for arguments parameter")
        print(e)
        return None


def find_codegen_functions(filepath: Path) -> list[DecoratedFunction]:
    """Find all codegen functions in a Python file.

    Args:
        filepath: Path to the Python file to search

    Returns:
        List of DecoratedFunction objects found in the file

    Raises:
        Exception: If the file cannot be parsed

    """
    # Read and parse the file
    with open(filepath) as f:
        file_content = f.read()
        tree = ast.parse(file_content)

    # Find all codegen.function decorators
    visitor = CodegenFunctionVisitor()
    visitor.file_content = file_content
    visitor.visit(tree)

    # Add filepath to each function
    for func in visitor.functions:
        func.filepath = filepath
        func.arguments_type_schema = _extract_arguments_type_schema(func)

    return visitor.functions
