"""
MCP Router

This module defines the router for the MCP server, which is responsible for
routing requests to the appropriate controllers.
"""

import json
import logging
from typing import Dict, List, Any, Optional, Union, Callable

from ..controllers import (
    SymbolController,
    FunctionController,
    ClassController,
    ImportController,
    AIController,
    SearchController,
    FileController,
)
from ..models import MCPRequest, MCPResponse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class Router:
    """Router for MCP requests."""

    def __init__(self, codebase=None):
        """Initialize the router.

        Args:
            codebase: The codebase to operate on.
        """
        self.codebase = codebase
        self.symbol_controller = SymbolController(codebase)
        self.function_controller = FunctionController(codebase)
        self.class_controller = ClassController(codebase)
        self.import_controller = ImportController(codebase)
        self.ai_controller = AIController(codebase)
        self.search_controller = SearchController(codebase)
        self.file_controller = FileController(codebase)

        # Register routes
        self.routes = {
            # Symbol operations
            "codebase.get_symbol": self._handle_get_symbol,
            "codebase.get_symbols": self._handle_get_symbols,
            "codebase.has_symbol": self._handle_has_symbol,
            "codebase.symbols": self._handle_symbols,
            "codebase.functions": self._handle_functions,
            "codebase.classes": self._handle_classes,
            "codebase.imports": self._handle_imports,
            "codebase.exports": self._handle_exports,
            "codebase.interfaces": self._handle_interfaces,
            "codebase.types": self._handle_types,
            "codebase.global_vars": self._handle_global_vars,
            "file.get_symbol": self._handle_file_get_symbol,
            "file.symbols": self._handle_file_symbols,
            "file.functions": self._handle_file_functions,
            "file.classes": self._handle_file_classes,
            "file.imports": self._handle_file_imports,
            "file.exports": self._handle_file_exports,
            "file.interfaces": self._handle_file_interfaces,
            "file.types": self._handle_file_types,
            "file.global_vars": self._handle_file_global_vars,
            "symbol.name": self._handle_symbol_name,
            "symbol.usages": self._handle_symbol_usages,
            "symbol.move_to_file": self._handle_symbol_move_to_file,
            "symbol.rename": self._handle_symbol_rename,
            "symbol.remove": self._handle_symbol_remove,

            # Function operations
            "function.return_type": self._handle_function_return_type,
            "function.parameters": self._handle_function_parameters,
            "function.is_async": self._handle_function_is_async,
            "function.decorators": self._handle_function_decorators,
            "function.function_calls": self._handle_function_function_calls,
            "function.set_return_type": self._handle_function_set_return_type,
            "function.add_parameter": self._handle_function_add_parameter,
            "function.remove_parameter": self._handle_function_remove_parameter,
            "function.add_decorator": self._handle_function_add_decorator,
            "function.set_docstring": self._handle_function_set_docstring,
            "function.generate_docstring": self._handle_function_generate_docstring,
            "function.rename_local_variable": self._handle_function_rename_local_variable,
            "function.call_sites": self._handle_function_call_sites,
            "function.dependencies": self._handle_function_dependencies,

            # Class operations
            "class.methods": self._handle_class_methods,
            "class.properties": self._handle_class_properties,
            "class.attributes": self._handle_class_attributes,
            "class.is_abstract": self._handle_class_is_abstract,
            "class.parent_class_names": self._handle_class_parent_class_names,
            "class.is_subclass_of": self._handle_class_is_subclass_of,
            "class.add_method": self._handle_class_add_method,
            "class.remove_method": self._handle_class_remove_method,
            "class.add_attribute": self._handle_class_add_attribute,
            "class.remove_attribute": self._handle_class_remove_attribute,
            "class.convert_to_protocol": self._handle_class_convert_to_protocol,
            "class.decorators": self._handle_class_decorators,

            # Import operations
            "import.source": self._handle_import_source,
            "import.update_source": self._handle_import_update_source,
            "import.remove": self._handle_import_remove,
            "import.rename": self._handle_import_rename,

            # AI operations
            "codebase.set_ai_key": self._handle_codebase_set_ai_key,
            "codebase.set_session_options": self._handle_codebase_set_session_options,
            "codebase.ai": self._handle_codebase_ai,
            "codebase.ai_client": self._handle_codebase_ai_client,

            # Search operations
            "ripgrep_search": self._handle_ripgrep_search,
            "search_files_by_name": self._handle_search_files_by_name,
            "semantic_search": self._handle_semantic_search,

            # File operations
            "view_file": self._handle_view_file,
            "edit_file": self._handle_edit_file,
            "create_file": self._handle_create_file,
            "delete_file": self._handle_delete_file,
            "rename_file": self._handle_rename_file,

        }

    def route(self, request: MCPRequest) -> MCPResponse:
        """Route a request to the appropriate handler.

        Args:
            request (MCPRequest): The request to route.

        Returns:
            MCPResponse: The response from the handler.
        """
        operation = request.operation
        params = request.params

        if operation not in self.routes:
            return MCPResponse(
                success=False, error=f"Unknown operation: {operation}"
            )

        try:
            handler = self.routes[operation]
            result = handler(params)
            return MCPResponse(success=True, data=result)
        except Exception as e:
            logger.exception(f"Error handling operation {operation}: {str(e)}")
            return MCPResponse(success=False, error=str(e))

    # Search operation handlers

    def _handle_ripgrep_search(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle ripgrep_search operation.

        Args:
            params (Dict[str, Any]): Operation parameters.

        Returns:
            Dict[str, Any]: Operation result.
        """
        query = params.get("query")
        file_extensions = params.get("file_extensions")
        files_per_page = params.get("files_per_page", 10)
        page = params.get("page", 1)
        use_regex = params.get("use_regex", False)

        return self.search_controller.ripgrep_search(
            query, file_extensions, files_per_page, page, use_regex
        )

    def _handle_search_files_by_name(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle search_files_by_name operation.

        Args:
            params (Dict[str, Any]): Operation parameters.

        Returns:
            Dict[str, Any]: Operation result.
        """
        pattern = params.get("pattern")
        directory = params.get("directory")
        recursive = params.get("recursive", True)

        return self.search_controller.search_files_by_name(
            pattern, directory, recursive
        )

    def _handle_semantic_search(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle semantic_search operation.

        Args:
            params (Dict[str, Any]): Operation parameters.

        Returns:
            Dict[str, Any]: Operation result.
        """
        query = params.get("query")
        limit = params.get("limit", 10)
        threshold = params.get("threshold", 0.7)

        if not query:
            return self._error("Missing required parameter: query")

        return self.search_controller.semantic_search(query, limit, threshold)

    # Class operation handlers

    def _handle_class_methods(self, params: Dict[str, Any]) -> Dict[str, Any]:
        name = params.get("name")
        if not name:
            return self._error("Missing required parameter: name")
        return self.class_controller.get_methods(name)

    def _handle_class_properties(self, params: Dict[str, Any]) -> Dict[str, Any]:
        name = params.get("name")
        if not name:
            return self._error("Missing required parameter: name")
        return self.class_controller.get_properties(name)

    def _handle_class_attributes(self, params: Dict[str, Any]) -> Dict[str, Any]:
        name = params.get("name")
        if not name:
            return self._error("Missing required parameter: name")
        return self.class_controller.get_attributes(name)

    def _handle_class_is_abstract(self, params: Dict[str, Any]) -> Dict[str, Any]:
        name = params.get("name")
        if not name:
            return self._error("Missing required parameter: name")
        return self.class_controller.is_abstract(name)

    def _handle_class_parent_class_names(self, params: Dict[str, Any]) -> Dict[str, Any]:
        name = params.get("name")
        if not name:
            return self._error("Missing required parameter: name")
        return self.class_controller.get_parent_class_names(name)

    def _handle_class_is_subclass_of(self, params: Dict[str, Any]) -> Dict[str, Any]:
        name = params.get("name")
        parent = params.get("parent")
        if not name:
            return self._error("Missing required parameter: name")
        if not parent:
            return self._error("Missing required parameter: parent")
        return self.class_controller.is_subclass_of(name, parent)

    def _handle_class_add_method(self, params: Dict[str, Any]) -> Dict[str, Any]:
        name = params.get("name")
        method = params.get("method")
        if not name:
            return self._error("Missing required parameter: name")
        if not method:
            return self._error("Missing required parameter: method")
        return self.class_controller.add_method(name, method)

    def _handle_class_remove_method(self, params: Dict[str, Any]) -> Dict[str, Any]:
        name = params.get("name")
        method_name = params.get("method_name")
        if not name:
            return self._error("Missing required parameter: name")
        if not method_name:
            return self._error("Missing required parameter: method_name")
        return self.class_controller.remove_method(name, method_name)

    def _handle_class_add_attribute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        name = params.get("name")
        attr_name = params.get("attr_name")
        attr_type = params.get("attr_type")
        attr_value = params.get("attr_value")
        if not name:
            return self._error("Missing required parameter: name")
        if not attr_name:
            return self._error("Missing required parameter: attr_name")
        return self.class_controller.add_attribute(name, attr_name, attr_type, attr_value)

    def _handle_class_remove_attribute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        name = params.get("name")
        attr_name = params.get("attr_name")
        if not name:
            return self._error("Missing required parameter: name")
        if not attr_name:
            return self._error("Missing required parameter: attr_name")
        return self.class_controller.remove_attribute(name, attr_name)

    def _handle_class_convert_to_protocol(self, params: Dict[str, Any]) -> Dict[str, Any]:
        name = params.get("name")
        if not name:
            return self._error("Missing required parameter: name")
        return self.class_controller.convert_to_protocol(name)

    def _handle_class_decorators(self, params: Dict[str, Any]) -> Dict[str, Any]:
        name = params.get("name")
        if not name:
            return self._error("Missing required parameter: name")
        return self.class_controller.get_decorators(name)

    # Import operation handlers

    def _handle_import_source(self, params: Dict[str, Any]) -> Dict[str, Any]:
        name = params.get("name")
        if not name:
            return self._error("Missing required parameter: name")
        return self.import_controller.get_source(name)

    def _handle_import_update_source(self, params: Dict[str, Any]) -> Dict[str, Any]:
        name = params.get("name")
        new_source = params.get("new_source")
        if not name:
            return self._error("Missing required parameter: name")
        if not new_source:
            return self._error("Missing required parameter: new_source")
        return self.import_controller.update_source(name, new_source)

    def _handle_import_remove(self, params: Dict[str, Any]) -> Dict[str, Any]:
        name = params.get("name")
        if not name:
            return self._error("Missing required parameter: name")
        return self.import_controller.remove_import(name)

    def _handle_import_rename(self, params: Dict[str, Any]) -> Dict[str, Any]:
        name = params.get("name")
        new_name = params.get("new_name")
        priority = params.get("priority", 0)
        if not name:
            return self._error("Missing required parameter: name")
        if not new_name:
            return self._error("Missing required parameter: new_name")
        return self.import_controller.rename_import(name, new_name, priority)

    # AI operation handlers

    def _handle_codebase_set_ai_key(self, params: Dict[str, Any]) -> Dict[str, Any]:
        api_key = params.get("api_key")
        if not api_key:
            return self._error("Missing required parameter: api_key")
        return self.ai_controller.set_ai_key(api_key)

    def _handle_codebase_set_session_options(self, params: Dict[str, Any]) -> Dict[str, Any]:
        max_ai_requests = params.get("max_ai_requests", 10)
        return self.ai_controller.set_session_options(max_ai_requests)

    def _handle_codebase_ai(self, params: Dict[str, Any]) -> Dict[str, Any]:
        prompt = params.get("prompt")
        target = params.get("target")
        context = params.get("context")
        model = params.get("model")
        if not prompt:
            return self._error("Missing required parameter: prompt")
        return self.ai_controller.ai(prompt, target, context, model)

    def _handle_codebase_ai_client(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return self.ai_controller.ai_client()

    def _handle_reflection(self, params: Dict[str, Any]) -> Dict[str, Any]:
        context_summary = params.get("context_summary")
        findings_so_far = params.get("findings_so_far")
        current_challenges = params.get("current_challenges", "")
        reflection_focus = params.get("reflection_focus")
        
        if not context_summary:
            return self._error("Missing required parameter: context_summary")
        if not findings_so_far:
            return self._error("Missing required parameter: findings_so_far")
            
        return self.ai_controller.reflection(
            context_summary, findings_so_far, current_challenges, reflection_focus
        )

    def _error(self, message: str, code: int = 400) -> Dict[str, Any]:
        """Create an error response.

        Args:
            message (str): Error message.
            code (int, optional): Error code. Defaults to 400.

        Returns:
            Dict[str, Any]: Error response.
        """
        return {
            "error": message,
            "code": code
        }

    # File operation handlers"""

    def _handle_view_file(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle view_file operation.

        Args:
            params (Dict[str, Any]): Operation parameters.

        Returns:
            Dict[str, Any]: Operation result.
        """
        filepath = params.get("filepath")

        return self.file_controller.view_file(filepath)

    def _handle_edit_file(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle edit_file operation.

        Args:
            params (Dict[str, Any]): Operation parameters.

        Returns:
            Dict[str, Any]: Operation result.
        """
        filepath = params.get("filepath")
        edit_snippet = params.get("edit_snippet")

        return self.file_controller.edit_file(filepath, edit_snippet)

    def _handle_create_file(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle create_file operation.

        Args:
            params (Dict[str, Any]): Operation parameters.

        Returns:
            Dict[str, Any]: Operation result.
        """
        filepath = params.get("filepath")
        content = params.get("content", "")

        return self.file_controller.create_file(filepath, content)

    def _handle_delete_file(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle delete_file operation.

        Args:
            params (Dict[str, Any]): Operation parameters.

        Returns:
            Dict[str, Any]: Operation result.
        """
        filepath = params.get("filepath")

        return self.file_controller.delete_file(filepath)

    def _handle_rename_file(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle rename_file operation.

        Args:
            params (Dict[str, Any]): Operation parameters.

        Returns:
            Dict[str, Any]: Operation result.
        """
        filepath = params.get("filepath")
        new_filepath = params.get("new_filepath")

        return self.file_controller.rename_file(filepath, new_filepath)

    def _handle_function_call_sites(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle function.call_sites operation.

        Args:
            params (Dict[str, Any]): Operation parameters.

        Returns:
            Dict[str, Any]: Operation result.
        """
        name = params.get("name")
        if not name:
            return self._error("Missing required parameter: name")
        return self.function_controller.get_call_sites(name)

    def _handle_function_dependencies(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle function.dependencies operation.

        Args:
            params (Dict[str, Any]): Operation parameters.

        Returns:
            Dict[str, Any]: Operation result.
        """
        name = params.get("name")
        if not name:
            return self._error("Missing required parameter: name")
        return self.function_controller.get_dependencies(name)
