"""
MCP client implementation.

This module provides a client for interacting with the MCP server.
"""

import json
import logging
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional, Union

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class MCPClient:
    """Client for interacting with the MCP server."""

    def __init__(self, host: str = "localhost", port: int = 8000):
        """Initialize the MCP client.

        Args:
            host (str, optional): Host of the MCP server. Defaults to "localhost".
            port (int, optional): Port of the MCP server. Defaults to 8000.
        """
        self.host = host
        self.port = port
        self.base_url = f"http://{host}:{port}"

    def _send_request(
        self, operation: str, params: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Send a request to the MCP server.

        Args:
            operation (str): Operation to perform.
            params (Dict[str, Any], optional): Parameters for the operation.
                Defaults to None.

        Returns:
            Dict[str, Any]: Response from the server.

        Raises:
            Exception: If the request fails.
        """
        if params is None:
            params = {}

        request = {"operation": operation, "params": params}
        data = json.dumps(request).encode("utf-8")

        url = f"{self.base_url}"
        headers = {"Content-Type": "application/json"}

        try:
            req = urllib.request.Request(url, data=data, headers=headers)
            with urllib.request.urlopen(req) as response:
                response_data = response.read().decode("utf-8")
                return json.loads(response_data)
        except urllib.error.HTTPError as e:
            error_message = e.read().decode("utf-8")
            try:
                error_data = json.loads(error_message)
                error_message = error_data.get("error", error_message)
            except json.JSONDecodeError:
                pass
            raise Exception(f"HTTP error {e.code}: {error_message}")
        except urllib.error.URLError as e:
            raise Exception(f"URL error: {str(e)}")
        except Exception as e:
            raise Exception(f"Error sending request: {str(e)}")

    # Symbol operations

    def get_symbol(self, name: str, optional: bool = False) -> Dict[str, Any]:
        """Get a symbol by name.

        Args:
            name (str): Name of the symbol.
            optional (bool, optional): Whether the symbol is optional.
                Defaults to False.

        Returns:
            Dict[str, Any]: Symbol data.
        """
        response = self._send_request(
            "codebase.get_symbol", {"name": name, "optional": optional}
        )
        return response.get("data")

    def get_symbols(self, name: str) -> List[Dict[str, Any]]:
        """Get all symbols matching a name pattern.

        Args:
            name (str): Name pattern to match.

        Returns:
            List[Dict[str, Any]]: List of symbols.
        """
        response = self._send_request("codebase.get_symbols", {"name": name})
        return response.get("data", [])

    def has_symbol(self, symbol_name: str) -> bool:
        """Check if a symbol exists.

        Args:
            symbol_name (str): Name of the symbol.

        Returns:
            bool: True if the symbol exists, False otherwise.
        """
        response = self._send_request("codebase.has_symbol", {"symbol_name": symbol_name})
        return response.get("data", False)

    def symbols(self) -> List[Dict[str, Any]]:
        """Get all symbols in the codebase.

        Returns:
            List[Dict[str, Any]]: List of symbols.
        """
        response = self._send_request("codebase.symbols")
        return response.get("data", [])

    def functions(self) -> List[Dict[str, Any]]:
        """Get all functions in the codebase.

        Returns:
            List[Dict[str, Any]]: List of functions.
        """
        response = self._send_request("codebase.functions")
        return response.get("data", [])

    def classes(self) -> List[Dict[str, Any]]:
        """Get all classes in the codebase.

        Returns:
            List[Dict[str, Any]]: List of classes.
        """
        response = self._send_request("codebase.classes")
        return response.get("data", [])

    def imports(self) -> List[Dict[str, Any]]:
        """Get all imports in the codebase.

        Returns:
            List[Dict[str, Any]]: List of imports.
        """
        response = self._send_request("codebase.imports")
        return response.get("data", [])

    def exports(self) -> List[Dict[str, Any]]:
        """Get all exports in the codebase.

        Returns:
            List[Dict[str, Any]]: List of exports.
        """
        response = self._send_request("codebase.exports")
        return response.get("data", [])

    def interfaces(self) -> List[Dict[str, Any]]:
        """Get all interfaces in the codebase.

        Returns:
            List[Dict[str, Any]]: List of interfaces.
        """
        response = self._send_request("codebase.interfaces")
        return response.get("data", [])

    def types(self) -> List[Dict[str, Any]]:
        """Get all types in the codebase.

        Returns:
            List[Dict[str, Any]]: List of types.
        """
        response = self._send_request("codebase.types")
        return response.get("data", [])

    def global_vars(self) -> List[Dict[str, Any]]:
        """Get all global variables in the codebase.

        Returns:
            List[Dict[str, Any]]: List of global variables.
        """
        response = self._send_request("codebase.global_vars")
        return response.get("data", [])

    # File-level symbol operations

    def file_get_symbol(self, file_path: str, name: str) -> Dict[str, Any]:
        """Get a symbol from a file.

        Args:
            file_path (str): Path to the file.
            name (str): Name of the symbol.

        Returns:
            Dict[str, Any]: Symbol data.
        """
        response = self._send_request(
            "file.get_symbol", {"file_path": file_path, "name": name}
        )
        return response.get("data")

    def file_symbols(self, file_path: str) -> List[Dict[str, Any]]:
        """Get all symbols in a file.

        Args:
            file_path (str): Path to the file.

        Returns:
            List[Dict[str, Any]]: List of symbols.
        """
        response = self._send_request("file.symbols", {"file_path": file_path})
        return response.get("data", [])

    def file_functions(self, file_path: str) -> List[Dict[str, Any]]:
        """Get all functions in a file.

        Args:
            file_path (str): Path to the file.

        Returns:
            List[Dict[str, Any]]: List of functions.
        """
        response = self._send_request("file.functions", {"file_path": file_path})
        return response.get("data", [])

    def file_classes(self, file_path: str) -> List[Dict[str, Any]]:
        """Get all classes in a file.

        Args:
            file_path (str): Path to the file.

        Returns:
            List[Dict[str, Any]]: List of classes.
        """
        response = self._send_request("file.classes", {"file_path": file_path})
        return response.get("data", [])

    def file_imports(self, file_path: str) -> List[Dict[str, Any]]:
        """Get all imports in a file.

        Args:
            file_path (str): Path to the file.

        Returns:
            List[Dict[str, Any]]: List of imports.
        """
        response = self._send_request("file.imports", {"file_path": file_path})
        return response.get("data", [])

    def file_exports(self, file_path: str) -> List[Dict[str, Any]]:
        """Get all exports in a file.

        Args:
            file_path (str): Path to the file.

        Returns:
            List[Dict[str, Any]]: List of exports.
        """
        response = self._send_request("file.exports", {"file_path": file_path})
        return response.get("data", [])

    def file_interfaces(self, file_path: str) -> List[Dict[str, Any]]:
        """Get all interfaces in a file.

        Args:
            file_path (str): Path to the file.

        Returns:
            List[Dict[str, Any]]: List of interfaces.
        """
        response = self._send_request("file.interfaces", {"file_path": file_path})
        return response.get("data", [])

    def file_types(self, file_path: str) -> List[Dict[str, Any]]:
        """Get all types in a file.

        Args:
            file_path (str): Path to the file.

        Returns:
            List[Dict[str, Any]]: List of types.
        """
        response = self._send_request("file.types", {"file_path": file_path})
        return response.get("data", [])

    def file_global_vars(self, file_path: str) -> List[Dict[str, Any]]:
        """Get all global variables in a file.

        Args:
            file_path (str): Path to the file.

        Returns:
            List[Dict[str, Any]]: List of global variables.
        """
        response = self._send_request("file.global_vars", {"file_path": file_path})
        return response.get("data", [])

    # Symbol operations

    def symbol_name(self, name: str) -> str:
        """Get the name of a symbol.

        Args:
            name (str): Name of the symbol.

        Returns:
            str: Symbol name.
        """
        response = self._send_request("symbol.name", {"name": name})
        return response.get("data", {}).get("name")

    def symbol_usages(
        self, name: str, usage_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get usages of a symbol.

        Args:
            name (str): Name of the symbol.
            usage_type (Optional[str], optional): Type of usage to filter by.
                Defaults to None.

        Returns:
            List[Dict[str, Any]]: List of usages.
        """
        params = {"name": name}
        if usage_type:
            params["usage_type"] = usage_type
        response = self._send_request("symbol.usages", params)
        return response.get("data", [])

    def symbol_move_to_file(
        self,
        name: str,
        target_file: str,
        include_dependencies: bool = True,
        strategy: str = "update_all_imports",
    ) -> bool:
        """Move a symbol to another file.

        Args:
            name (str): Name of the symbol.
            target_file (str): Path to the target file.
            include_dependencies (bool, optional): Whether to include dependencies.
                Defaults to True.
            strategy (str, optional): Import update strategy.
                Defaults to "update_all_imports".

        Returns:
            bool: True if successful, False otherwise.
        """
        response = self._send_request(
            "symbol.move_to_file",
            {
                "name": name,
                "target_file": target_file,
                "include_dependencies": include_dependencies,
                "strategy": strategy,
            },
        )
        return response.get("data", {}).get("moved", False)

    def symbol_rename(self, name: str, new_name: str, priority: int = 0) -> bool:
        """Rename a symbol.

        Args:
            name (str): Current name of the symbol.
            new_name (str): New name for the symbol.
            priority (int, optional): Priority of the rename operation.
                Defaults to 0.

        Returns:
            bool: True if successful, False otherwise.
        """
        response = self._send_request(
            "symbol.rename", {"name": name, "new_name": new_name, "priority": priority}
        )
        return response.get("data", {}).get("renamed", False)

    def symbol_remove(self, name: str) -> bool:
        """Remove a symbol from the codebase.

        Args:
            name (str): Name of the symbol to remove.

        Returns:
            bool: True if successful, False otherwise.
        """
        response = self._send_request("symbol.remove", {"name": name})
        return response.get("data", {}).get("removed", False)

    # Function operations

    def function_return_type(self, name: str) -> Optional[str]:
        """Get the return type of a function.

        Args:
            name (str): Name of the function.

        Returns:
            Optional[str]: Return type or None.
        """
        response = self._send_request("function.return_type", {"name": name})
        return response.get("data", {}).get("return_type")

    def function_parameters(self, name: str) -> List[Dict[str, Any]]:
        """Get the parameters of a function.

        Args:
            name (str): Name of the function.

        Returns:
            List[Dict[str, Any]]: List of parameters.
        """
        response = self._send_request("function.parameters", {"name": name})
        return response.get("data", {}).get("parameters", [])

    def function_is_async(self, name: str) -> bool:
        """Check if a function is async.

        Args:
            name (str): Name of the function.

        Returns:
            bool: True if async, False otherwise.
        """
        response = self._send_request("function.is_async", {"name": name})
        return response.get("data", {}).get("is_async", False)

    def function_decorators(self, name: str) -> List[str]:
        """Get the decorators of a function.

        Args:
            name (str): Name of the function.

        Returns:
            List[str]: List of decorators.
        """
        response = self._send_request("function.decorators", {"name": name})
        return response.get("data", {}).get("decorators", [])

    def function_function_calls(self, name: str) -> List[Dict[str, Any]]:
        """Get the function calls made by a function.

        Args:
            name (str): Name of the function.

        Returns:
            List[Dict[str, Any]]: List of function calls.
        """
        response = self._send_request("function.function_calls", {"name": name})
        return response.get("data", {}).get("function_calls", [])

    def function_set_return_type(self, name: str, type_str: str) -> bool:
        """Set the return type of a function.

        Args:
            name (str): Name of the function.
            type_str (str): New return type.

        Returns:
            bool: True if successful, False otherwise.
        """
        response = self._send_request(
            "function.set_return_type", {"name": name, "type": type_str}
        )
        return response.get("data", {}).get("updated", False)

    def function_add_parameter(
        self, name: str, param_name: str, param_type: Optional[str] = None
    ) -> bool:
        """Add a parameter to a function.

        Args:
            name (str): Name of the function.
            param_name (str): Name of the parameter to add.
            param_type (Optional[str], optional): Type of the parameter.
                Defaults to None.

        Returns:
            bool: True if successful, False otherwise.
        """
        params = {"name": name, "param_name": param_name}
        if param_type:
            params["param_type"] = param_type
        response = self._send_request("function.add_parameter", params)
        return response.get("data", {}).get("added", False)

    def function_remove_parameter(self, name: str, param_name: str) -> bool:
        """Remove a parameter from a function.

        Args:
            name (str): Name of the function.
            param_name (str): Name of the parameter to remove.

        Returns:
            bool: True if successful, False otherwise.
        """
        response = self._send_request(
            "function.remove_parameter", {"name": name, "param_name": param_name}
        )
        return response.get("data", {}).get("removed", False)

    def function_add_decorator(self, name: str, decorator: str) -> bool:
        """Add a decorator to a function.

        Args:
            name (str): Name of the function.
            decorator (str): Decorator to add.

        Returns:
            bool: True if successful, False otherwise.
        """
        response = self._send_request(
            "function.add_decorator", {"name": name, "decorator": decorator}
        )
        return response.get("data", {}).get("added", False)

    def function_set_docstring(self, name: str, docstring: str) -> bool:
        """Set the docstring of a function.

        Args:
            name (str): Name of the function.
            docstring (str): New docstring.

        Returns:
            bool: True if successful, False otherwise.
        """
        response = self._send_request(
            "function.set_docstring", {"name": name, "docstring": docstring}
        )
        return response.get("data", {}).get("updated", False)

    def function_generate_docstring(self, name: str) -> str:
        """Generate a docstring for a function.

        Args:
            name (str): Name of the function.

        Returns:
            str: Generated docstring.
        """
        response = self._send_request("function.generate_docstring", {"name": name})
        return response.get("data", {}).get("docstring", "")

    def function_rename_local_variable(
        self, name: str, old_var_name: str, new_var_name: str, fuzzy_match: bool = False
    ) -> bool:
        """Rename a local variable in a function.

        Args:
            name (str): Name of the function.
            old_var_name (str): Current variable name.
            new_var_name (str): New variable name.
            fuzzy_match (bool, optional): Whether to use fuzzy matching.
                Defaults to False.

        Returns:
            bool: True if successful, False otherwise.
        """
        response = self._send_request(
            "function.rename_local_variable",
            {
                "name": name,
                "old_var_name": old_var_name,
                "new_var_name": new_var_name,
                "fuzzy_match": fuzzy_match,
            },
        )
        return response.get("data", {}).get("renamed", False)

    def function_call_sites(self, name: str) -> List[Dict[str, Any]]:
        """Get the call sites of a function.

        Args:
            name (str): Name of the function.

        Returns:
            List[Dict[str, Any]]: List of call sites.
        """
        response = self._send_request("function.call_sites", {"name": name})
        return response.get("data", {}).get("call_sites", [])

    def function_dependencies(self, name: str) -> List[Dict[str, Any]]:
        """Get the dependencies of a function.

        Args:
            name (str): Name of the function.

        Returns:
            List[Dict[str, Any]]: List of dependencies.
        """
        response = self._send_request("function.dependencies", {"name": name})
        return response.get("data", {}).get("dependencies", [])

    # Class operations

    def class_methods(self, name: str) -> List[Dict[str, Any]]:
        """Get the methods of a class.

        Args:
            name (str): Name of the class.

        Returns:
            List[Dict[str, Any]]: List of methods.
        """
        response = self._send_request("class.methods", {"name": name})
        return response.get("data", {}).get("methods", [])

    def class_properties(self, name: str) -> List[Dict[str, Any]]:
        """Get the properties of a class.

        Args:
            name (str): Name of the class.

        Returns:
            List[Dict[str, Any]]: List of properties.
        """
        response = self._send_request("class.properties", {"name": name})
        return response.get("data", {}).get("properties", [])

    def class_attributes(self, name: str) -> List[Dict[str, Any]]:
        """Get the attributes of a class.

        Args:
            name (str): Name of the class.

        Returns:
            List[Dict[str, Any]]: List of attributes.
        """
        response = self._send_request("class.attributes", {"name": name})
        return response.get("data", {}).get("attributes", [])

    def class_is_abstract(self, name: str) -> bool:
        """Check if a class is abstract.

        Args:
            name (str): Name of the class.

        Returns:
            bool: True if abstract, False otherwise.
        """
        response = self._send_request("class.is_abstract", {"name": name})
        return response.get("data", {}).get("is_abstract", False)

    def class_parent_class_names(self, name: str) -> List[str]:
        """Get the parent class names of a class.

        Args:
            name (str): Name of the class.

        Returns:
            List[str]: List of parent class names.
        """
        response = self._send_request("class.parent_class_names", {"name": name})
        return response.get("data", {}).get("parent_class_names", [])

    def class_is_subclass_of(self, name: str, parent: str) -> bool:
        """Check if a class is a subclass of a specific parent.

        Args:
            name (str): Name of the class.
            parent (str): Name of the parent class.

        Returns:
            bool: True if subclass, False otherwise.
        """
        response = self._send_request(
            "class.is_subclass_of", {"name": name, "parent": parent}
        )
        return response.get("data", {}).get("is_subclass", False)

    def class_add_method(self, name: str, method: Dict[str, Any]) -> bool:
        """Add a method to a class.

        Args:
            name (str): Name of the class.
            method (Dict[str, Any]): Method to add.

        Returns:
            bool: True if successful, False otherwise.
        """
        response = self._send_request(
            "class.add_method", {"name": name, "method": method}
        )
        return response.get("data", {}).get("added", False)

    def class_remove_method(self, name: str, method_name: str) -> bool:
        """Remove a method from a class.

        Args:
            name (str): Name of the class.
            method_name (str): Name of the method to remove.

        Returns:
            bool: True if successful, False otherwise.
        """
        response = self._send_request(
            "class.remove_method", {"name": name, "method_name": method_name}
        )
        return response.get("data", {}).get("removed", False)

    def class_add_attribute(
        self,
        name: str,
        attr_name: str,
        attr_type: Optional[str] = None,
        attr_value: Optional[str] = None,
    ) -> bool:
        """Add an attribute to a class.

        Args:
            name (str): Name of the class.
            attr_name (str): Name of the attribute to add.
            attr_type (Optional[str], optional): Type of the attribute.
                Defaults to None.
            attr_value (Optional[str], optional): Value of the attribute.
                Defaults to None.

        Returns:
            bool: True if successful, False otherwise.
        """
        params = {"name": name, "attr_name": attr_name}
        if attr_type:
            params["attr_type"] = attr_type
        if attr_value:
            params["attr_value"] = attr_value
        response = self._send_request("class.add_attribute", params)
        return response.get("data", {}).get("added", False)

    def class_remove_attribute(self, name: str, attr_name: str) -> bool:
        """Remove an attribute from a class.

        Args:
            name (str): Name of the class.
            attr_name (str): Name of the attribute to remove.

        Returns:
            bool: True if successful, False otherwise.
        """
        response = self._send_request(
            "class.remove_attribute", {"name": name, "attr_name": attr_name}
        )
        return response.get("data", {}).get("removed", False)

    def class_convert_to_protocol(self, name: str) -> bool:
        """Convert a class to a protocol.

        Args:
            name (str): Name of the class.

        Returns:
            bool: True if successful, False otherwise.
        """
        response = self._send_request("class.convert_to_protocol", {"name": name})
        return response.get("data", {}).get("converted", False)

    def class_decorators(self, name: str) -> List[str]:
        """Get the decorators of a class.

        Args:
            name (str): Name of the class.

        Returns:
            List[str]: List of decorators.
        """
        response = self._send_request("class.decorators", {"name": name})
        return response.get("data", {}).get("decorators", [])

    # Import operations

    def import_source(self, name: str) -> str:
        """Get the source of an import.

        Args:
            name (str): Name of the import.

        Returns:
            str: Import source.
        """
        response = self._send_request("import.source", {"name": name})
        return response.get("data", {}).get("source", "")

    def import_update_source(self, name: str, new_source: str) -> bool:
        """Update the source of an import.

        Args:
            name (str): Name of the import.
            new_source (str): New import source.

        Returns:
            bool: True if successful, False otherwise.
        """
        response = self._send_request(
            "import.update_source", {"name": name, "new_source": new_source}
        )
        return response.get("data", {}).get("updated", False)

    def import_remove(self, name: str) -> bool:
        """Remove an import from the codebase.

        Args:
            name (str): Name of the import to remove.

        Returns:
            bool: True if successful, False otherwise.
        """
        response = self._send_request("import.remove", {"name": name})
        return response.get("data", {}).get("removed", False)

    def import_rename(self, name: str, new_name: str, priority: int = 0) -> bool:
        """Rename an import.

        Args:
            name (str): Current name of the import.
            new_name (str): New name for the import.
            priority (int, optional): Priority of the rename operation.
                Defaults to 0.

        Returns:
            bool: True if successful, False otherwise.
        """
        response = self._send_request(
            "import.rename", {"name": name, "new_name": new_name, "priority": priority}
        )
        return response.get("data", {}).get("renamed", False)

    # AI operations

    def set_ai_key(self, api_key: str) -> bool:
        """Set the API key for AI operations.

        Args:
            api_key (str): API key for the AI service.

        Returns:
            bool: True if successful, False otherwise.
        """
        response = self._send_request("codebase.set_ai_key", {"api_key": api_key})
        return response.get("data", {}).get("set", False)

    def set_session_options(self, max_ai_requests: int = 10) -> bool:
        """Set session options for AI operations.

        Args:
            max_ai_requests (int, optional): Maximum number of AI requests per session.
                Defaults to 10.

        Returns:
            bool: True if successful, False otherwise.
        """
        response = self._send_request(
            "codebase.set_session_options", {"max_ai_requests": max_ai_requests}
        )
        return response.get("data", {}).get("set", False)

    def ai(
        self,
        prompt: str,
        target: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Call the AI with a prompt and optional target and context.

        Args:
            prompt (str): Prompt for the AI.
            target (Optional[Dict[str, Any]], optional): Target to modify.
                Defaults to None.
            context (Optional[Dict[str, Any]], optional): Additional context.
                Defaults to None.

        Returns:
            str: AI response.
        """
        params = {"prompt": prompt}
        if target:
            params["target"] = target
        if context:
            params["context"] = context
        response = self._send_request("codebase.ai", params)
        return response.get("data", {}).get("response", "")

    def ai_client(self) -> Dict[str, Any]:
        """Get the AI client configuration.

        Returns:
            Dict[str, Any]: AI client configuration.
        """
        response = self._send_request("codebase.ai_client")
        return response.get("data", {})

    # Search operations

    def ripgrep_search(
        self,
        query: str,
        file_extensions: Optional[List[str]] = None,
        files_per_page: int = 10,
        page: int = 1,
        use_regex: bool = False,
    ) -> Dict[str, Any]:
        """Search the codebase using ripgrep or regex pattern matching.

        Args:
            query (str): The search query to find in the codebase.
            file_extensions (Optional[List[str]], optional): Optional list of file extensions to search.
            files_per_page (int, optional): Number of files to return per page. Defaults to 10.
            page (int, optional): Page number to return (1-based). Defaults to 1.
            use_regex (bool, optional): Whether to treat query as a regex pattern. Defaults to False.

        Returns:
            Dict[str, Any]: Search results.
        """
        response = self._send_request(
            "ripgrep_search",
            {
                "query": query,
                "file_extensions": file_extensions,
                "files_per_page": files_per_page,
                "page": page,
                "use_regex": use_regex,
            },
        )
        return response.get("data")

    def search_files_by_name(
        self,
        pattern: str,
        directory: Optional[str] = None,
        recursive: bool = True,
    ) -> Dict[str, Any]:
        """Find files by name pattern.

        Args:
            pattern (str): Pattern to search for in file names.
            directory (Optional[str], optional): Directory to search in. Defaults to None (root).
            recursive (bool, optional): Whether to search recursively. Defaults to True.

        Returns:
            Dict[str, Any]: Search results.
        """
        response = self._send_request(
            "search_files_by_name",
            {
                "pattern": pattern,
                "directory": directory,
                "recursive": recursive,
            },
        )
        return response.get("data")

    def semantic_search(
        self,
        query: str,
        limit: int = 10,
        threshold: float = 0.7,
    ) -> Dict[str, Any]:
        """Search for code semantically using embeddings.

        Args:
            query (str): Semantic query to search for.
            limit (int, optional): Maximum number of results to return. Defaults to 10.
            threshold (float, optional): Similarity threshold. Defaults to 0.7.

        Returns:
            Dict[str, Any]: Search results.
        """
        response = self._send_request(
            "semantic_search",
            {
                "query": query,
                "limit": limit,
                "threshold": threshold,
            },
        )
        return response.get("data")

    # File operations

    def view_file(self, filepath: str) -> Dict[str, Any]:
        """View the content of a file.

        Args:
            filepath (str): Path to the file to view.

        Returns:
            Dict[str, Any]: File content and metadata.
        """
        response = self._send_request(
            "view_file",
            {
                "filepath": filepath,
            },
        )
        return response.get("data")

    def edit_file(self, filepath: str, edit_snippet: str) -> Dict[str, Any]:
        """Edit a file using the Relace Instant Apply API.

        Args:
            filepath (str): Path to the file to edit.
            edit_snippet (str): Edit snippet to apply to the file.

        Returns:
            Dict[str, Any]: Result of the edit operation.
        """
        response = self._send_request(
            "edit_file",
            {
                "filepath": filepath,
                "edit_snippet": edit_snippet,
            },
        )
        return response.get("data")

    def create_file(self, filepath: str, content: str = "") -> Dict[str, Any]:
        """Create a new file.

        Args:
            filepath (str): Path for the new file.
            content (str, optional): Initial content for the file. Defaults to "".

        Returns:
            Dict[str, Any]: Result of the file creation.
        """
        response = self._send_request(
            "create_file",
            {
                "filepath": filepath,
                "content": content,
            },
        )
        return response.get("data")

    def delete_file(self, filepath: str) -> Dict[str, Any]:
        """Delete a file.

        Args:
            filepath (str): Path to the file to delete.

        Returns:
            Dict[str, Any]: Result of the file deletion.
        """
        response = self._send_request(
            "delete_file",
            {
                "filepath": filepath,
            },
        )
        return response.get("data")

    def rename_file(self, filepath: str, new_filepath: str) -> Dict[str, Any]:
        """Rename a file and update all references.

        Args:
            filepath (str): Path to the file to rename.
            new_filepath (str): New path for the file.

        Returns:
            Dict[str, Any]: Result of the file renaming.
        """
        response = self._send_request(
            "rename_file",
            {
                "filepath": filepath,
                "new_filepath": new_filepath,
            },
        )
        return response.get("data")
