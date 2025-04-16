"""
MCP Protocol Handler
This module defines the protocol handler for the MCP server, which is responsible
for receiving requests, routing them to the appropriate controllers, and returning
responses.
"""
import json
from typing import Dict, List, Any, Optional, Union, Callable
from .models import Codebase, File, Symbol, Function, Class, Import, CallGraph
from .controllers import (
    SymbolController, 
    FileSymbolController, 
    SymbolOperationsController,
    FunctionController,
    ClassController,
    ImportController
)
from .editing_tools import (
    SemanticEditController,
    PatternReplacementController,
    RelaceEditController
)
from .analysis_tools import (
    CodeAnalysisController,
    CodebaseAnalysisController
)

class MCPRequest:
    """Represents a request to the MCP server."""
    
    def __init__(self, operation: str, params: Dict[str, Any] = None):
        """Initialize with operation and parameters."""
        self.operation = operation
        self.params = params or {}
    
    @classmethod
    def from_json(cls, json_str: str) -> 'MCPRequest':
        """Create a request from a JSON string."""
        data = json.loads(json_str)
        return cls(
            operation=data.get('operation', ''),
            params=data.get('params', {})
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'operation': self.operation,
            'params': self.params
        }

class MCPResponse:
    """Represents a response from the MCP server."""
    
    def __init__(self, success: bool, data: Any = None, error: str = None):
        """Initialize with success status, data, and error message."""
        self.success = success
        self.data = data
        self.error = error
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps({
            'success': self.success,
            'data': self.data,
            'error': self.error
        })
    
    @classmethod
    def success(cls, data: Any = None) -> 'MCPResponse':
        """Create a success response."""
        return cls(success=True, data=data)
    
    @classmethod
    def error(cls, message: str) -> 'MCPResponse':
        """Create an error response."""
        return cls(success=False, error=message)

class MCPServer:
    """MCP server that handles requests and routes them to controllers."""
    
    def __init__(self, codebase: Codebase):
        """Initialize with a codebase reference."""
        self.codebase = codebase
        
        # Initialize controllers
        self.symbol_controller = SymbolController(codebase)
        self.symbol_operations_controller = SymbolOperationsController(codebase)
        self.function_controller = FunctionController(codebase)
        self.class_controller = ClassController(codebase)
        self.import_controller = ImportController(codebase)
        
        # Initialize editing tools controllers
        self.semantic_edit_controller = SemanticEditController(codebase)
        self.pattern_replacement_controller = PatternReplacementController(codebase)
        self.relace_edit_controller = RelaceEditController(codebase)
        
        # Initialize analysis tools controllers
        self.code_analysis_controller = CodeAnalysisController(codebase)
        self.codebase_analysis_controller = CodebaseAnalysisController(codebase)
        
        # Map operations to handler methods
        self.operation_handlers = {
            # Codebase-level symbol operations
            'codebase.get_symbol': self._handle_codebase_get_symbol,
            'codebase.get_symbols': self._handle_codebase_get_symbols,
            'codebase.has_symbol': self._handle_codebase_has_symbol,
            'codebase.symbols': self._handle_codebase_symbols,
            'codebase.functions': self._handle_codebase_functions,
            'codebase.classes': self._handle_codebase_classes,
            'codebase.imports': self._handle_codebase_imports,
            'codebase.exports': self._handle_codebase_exports,
            'codebase.interfaces': self._handle_codebase_interfaces,
            'codebase.types': self._handle_codebase_types,
            'codebase.global_vars': self._handle_codebase_global_vars,
            
            # File-level symbol operations
            'file.get_symbol': self._handle_file_get_symbol,
            'file.symbols': self._handle_file_symbols,
            'file.functions': self._handle_file_functions,
            'file.classes': self._handle_file_classes,
            'file.imports': self._handle_file_imports,
            'file.exports': self._handle_file_exports,
            'file.interfaces': self._handle_file_interfaces,
            'file.types': self._handle_file_types,
            'file.global_vars': self._handle_file_global_vars,
            
            # Symbol operations
            'symbol.name': self._handle_symbol_name,
            'symbol.usages': self._handle_symbol_usages,
            'symbol.move_to_file': self._handle_symbol_move_to_file,
            'symbol.rename': self._handle_symbol_rename,
            'symbol.remove': self._handle_symbol_remove,
            
            # Editing tools operations
            'SemanticEditTool': self._handle_semantic_edit_tool,
            'semantic_edit': self._handle_semantic_edit,
            'ReplacementEditTool.apply_pattern': self._handle_apply_pattern,
            'global_replacement_edit': self._handle_global_replacement_edit,
            'relace_edit': self._handle_relace_edit,
            
            # Analysis tools operations
            'codebase.find_calls': self._handle_find_calls,
            'codebase.commit': self._handle_commit,
            'codebase.visualize': self._handle_visualize,
            'create_call_graph': self._handle_create_call_graph,
            'find_dead_code': self._handle_find_dead_code,
            'get_max_call_chain': self._handle_get_max_call_chain,
            'get_codebase_summary': self._handle_get_codebase_summary,
            'get_file_summary': self._handle_get_file_summary,
            'get_class_summary': self._handle_get_class_summary,
            'get_function_summary': self._handle_get_function_summary,
        }
    
    def handle_request(self, request: Union[MCPRequest, str, Dict[str, Any]]) -> MCPResponse:
        """Handle an MCP request and return a response."""
        # Convert request to MCPRequest if needed
        if isinstance(request, str):
            try:
                request = MCPRequest.from_json(request)
            except json.JSONDecodeError:
                return MCPResponse.error("Invalid JSON in request")
        elif isinstance(request, dict):
            request = MCPRequest(
                operation=request.get('operation', ''),
                params=request.get('params', {})
            )
        
        # Get the handler for the operation
        handler = self.operation_handlers.get(request.operation)
        if not handler:
            return MCPResponse.error(f"Unknown operation: {request.operation}")
        
        # Call the handler
        try:
            result = handler(request.params)
            return MCPResponse.success(result)
        except Exception as e:
            return MCPResponse.error(str(e))
    
    # Handler methods for codebase-level symbol operations
    
    def _handle_codebase_get_symbol(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle codebase.get_symbol operation."""
        name = params.get('name')
        optional = params.get('optional', False)
        
        if not name:
            raise ValueError("Missing required parameter: name")
        
        symbol = self.symbol_controller.get_symbol(name, optional)
        return symbol.to_dict() if symbol else None
    
    def _handle_codebase_get_symbols(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Handle codebase.get_symbols operation."""
        name = params.get('name')
        
        if not name:
            raise ValueError("Missing required parameter: name")
        
        symbols = self.symbol_controller.get_symbols(name)
        return [s.to_dict() for s in symbols]
    
    def _handle_codebase_has_symbol(self, params: Dict[str, Any]) -> bool:
        """Handle codebase.has_symbol operation."""
        symbol_name = params.get('symbol_name')
        
        if not symbol_name:
            raise ValueError("Missing required parameter: symbol_name")
        
        return self.symbol_controller.has_symbol(symbol_name)
    
    def _handle_codebase_symbols(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Handle codebase.symbols operation."""
        symbols = self.symbol_controller.symbols()
        return [s.to_dict() for s in symbols]
    
    def _handle_codebase_functions(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Handle codebase.functions operation."""
        functions = self.symbol_controller.functions()
        return [f.to_dict() for f in functions]
    
    def _handle_codebase_classes(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Handle codebase.classes operation."""
        classes = self.symbol_controller.classes()
        return [c.to_dict() for c in classes]
    
    def _handle_codebase_imports(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Handle codebase.imports operation."""
        imports = self.symbol_controller.imports()
        return [i.to_dict() for i in imports]
    
    def _handle_codebase_exports(self, params: Dict[str, Any]) -> List[str]:
        """Handle codebase.exports operation."""
        return self.symbol_controller.exports()
    
    def _handle_codebase_interfaces(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Handle codebase.interfaces operation."""
        return self.symbol_controller.interfaces()
    
    def _handle_codebase_types(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Handle codebase.types operation."""
        return self.symbol_controller.types()
    
    def _handle_codebase_global_vars(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Handle codebase.global_vars operation."""
        return self.symbol_controller.global_vars()
    
    # Handler methods for file-level symbol operations
    
    def _get_file_controller(self, file_path: str) -> FileSymbolController:
        """Get a file controller for a file path."""
        # Implementation would use the actual codebase API to get the file
        # For now, create a dummy file
        file = File(path=file_path, name=file_path.split('/')[-1])
        return FileSymbolController(file)
    
    def _handle_file_get_symbol(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle file.get_symbol operation."""
        file_path = params.get('file_path')
        name = params.get('name')
        
        if not file_path:
            raise ValueError("Missing required parameter: file_path")
        if not name:
            raise ValueError("Missing required parameter: name")
        
        file_controller = self._get_file_controller(file_path)
        symbol = file_controller.get_symbol(name)
        return symbol.to_dict() if symbol else None
    
    def _handle_file_symbols(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Handle file.symbols operation."""
        file_path = params.get('file_path')
        
        if not file_path:
            raise ValueError("Missing required parameter: file_path")
        
        file_controller = self._get_file_controller(file_path)
        return [s.to_dict() for s in file_controller.symbols]
    
    def _handle_file_functions(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Handle file.functions operation."""
        file_path = params.get('file_path')
        
        if not file_path:
            raise ValueError("Missing required parameter: file_path")
        
        file_controller = self._get_file_controller(file_path)
        return [f.to_dict() for f in file_controller.functions]
    
    def _handle_file_classes(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Handle file.classes operation."""
        file_path = params.get('file_path')
        
        if not file_path:
            raise ValueError("Missing required parameter: file_path")
        
        file_controller = self._get_file_controller(file_path)
        return [c.to_dict() for c in file_controller.classes]
    
    def _handle_file_imports(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Handle file.imports operation."""
        file_path = params.get('file_path')
        
        if not file_path:
            raise ValueError("Missing required parameter: file_path")
        
        file_controller = self._get_file_controller(file_path)
        return [i.to_dict() for i in file_controller.imports]
    
    def _handle_file_exports(self, params: Dict[str, Any]) -> List[str]:
        """Handle file.exports operation."""
        file_path = params.get('file_path')
        
        if not file_path:
            raise ValueError("Missing required parameter: file_path")
        
        file_controller = self._get_file_controller(file_path)
        return file_controller.exports
    
    def _handle_file_interfaces(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Handle file.interfaces operation."""
        file_path = params.get('file_path')
        
        if not file_path:
            raise ValueError("Missing required parameter: file_path")
        
        file_controller = self._get_file_controller(file_path)
        return file_controller.interfaces
    
    def _handle_file_types(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Handle file.types operation."""
        file_path = params.get('file_path')
        
        if not file_path:
            raise ValueError("Missing required parameter: file_path")
        
        file_controller = self._get_file_controller(file_path)
        return file_controller.types
    
    def _handle_file_global_vars(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Handle file.global_vars operation."""
        file_path = params.get('file_path')
        
        if not file_path:
            raise ValueError("Missing required parameter: file_path")
        
        file_controller = self._get_file_controller(file_path)
        return file_controller.global_vars
    
    # Handler methods for symbol operations
    
    def _get_symbol(self, symbol_id: str) -> Symbol:
        """Get a symbol by ID."""
        # Implementation would use the actual codebase API to get the symbol
        # For now, raise an error if the symbol is not found
        symbol = self.symbol_controller.get_symbol(symbol_id, optional=True)
        if not symbol:
            raise ValueError(f"Symbol not found: {symbol_id}")
        return symbol
    
    def _handle_symbol_name(self, params: Dict[str, Any]) -> str:
        """Handle symbol.name operation."""
        symbol_id = params.get('symbol_id')
        
        if not symbol_id:
            raise ValueError("Missing required parameter: symbol_id")
        
        symbol = self._get_symbol(symbol_id)
        return symbol.name
    
    def _handle_symbol_usages(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Handle symbol.usages operation."""
        symbol_id = params.get('symbol_id')
        usage_type = params.get('usage_type')
        
        if not symbol_id:
            raise ValueError("Missing required parameter: symbol_id")
        
        symbol = self._get_symbol(symbol_id)
        usages = self.symbol_operations_controller.get_usages(symbol, usage_type)
        return [u.to_dict() for u in usages]
    
    def _handle_symbol_move_to_file(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle symbol.move_to_file operation."""
        symbol_id = params.get('symbol_id')
        target_file_path = params.get('target_file')
        include_dependencies = params.get('include_dependencies', True)
        strategy = params.get('strategy', 'update_all_imports')
        
        if not symbol_id:
            raise ValueError("Missing required parameter: symbol_id")
        if not target_file_path:
            raise ValueError("Missing required parameter: target_file")
        
        symbol = self._get_symbol(symbol_id)
        
        # Implementation would use the actual codebase API to get the target file
        # For now, create a dummy file
        target_file = File(path=target_file_path, name=target_file_path.split('/')[-1])
        
        return self.symbol_operations_controller.move_to_file(
            symbol, target_file, include_dependencies, strategy
        )
    
    def _handle_symbol_rename(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle symbol.rename operation."""
        symbol_id = params.get('symbol_id')
        new_name = params.get('new_name')
        priority = params.get('priority', 0)
        
        if not symbol_id:
            raise ValueError("Missing required parameter: symbol_id")
        if not new_name:
            raise ValueError("Missing required parameter: new_name")
        
        symbol = self._get_symbol(symbol_id)
        return self.symbol_operations_controller.rename(symbol, new_name, priority)
    
    def _handle_symbol_remove(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle symbol.remove operation."""
        symbol_id = params.get('symbol_id')
        
        if not symbol_id:
            raise ValueError("Missing required parameter: symbol_id")
        
        symbol = self._get_symbol(symbol_id)
        return self.symbol_operations_controller.remove(symbol)
    
    # Handler methods for editing tools operations
    
    def _handle_semantic_edit_tool(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle SemanticEditTool operation."""
        file_path = params.get('file_path')
        
        if not file_path:
            raise ValueError("Missing required parameter: file_path")
        
        # Get the file
        file = None
        for f in self.codebase.files:
            if f.path == file_path:
                file = f
                break
        
        if not file:
            raise ValueError(f"File not found: {file_path}")
        
        tool = self.semantic_edit_controller.create_semantic_edit_tool(file)
        return tool.to_dict()
    
    def _handle_semantic_edit(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle semantic_edit operation."""
        filepath = params.get('filepath')
        edit_description = params.get('edit_description')
        context = params.get('context')
        
        if not filepath:
            raise ValueError("Missing required parameter: filepath")
        if not edit_description:
            raise ValueError("Missing required parameter: edit_description")
        
        return self.semantic_edit_controller.semantic_edit(filepath, edit_description, context)
    
    def _handle_apply_pattern(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle ReplacementEditTool.apply_pattern operation."""
        pattern = params.get('pattern')
        replacement = params.get('replacement')
        file_paths = params.get('files', [])
        
        if not pattern:
            raise ValueError("Missing required parameter: pattern")
        if not replacement:
            raise ValueError("Missing required parameter: replacement")
        
        # Get the files
        files = []
        for file_path in file_paths:
            file = None
            for f in self.codebase.files:
                if f.path == file_path:
                    file = f
                    break
            
            if file:
                files.append(file)
        
        return self.pattern_replacement_controller.apply_pattern(pattern, replacement, files)
    
    def _handle_global_replacement_edit(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle global_replacement_edit operation."""
        pattern = params.get('pattern')
        replacement = params.get('replacement')
        file_pattern = params.get('file_pattern')
        
        if not pattern:
            raise ValueError("Missing required parameter: pattern")
        if not replacement:
            raise ValueError("Missing required parameter: replacement")
        
        return self.pattern_replacement_controller.global_replacement_edit(pattern, replacement, file_pattern)
    
    def _handle_relace_edit(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle relace_edit operation."""
        filepath = params.get('filepath')
        edit_snippet = params.get('edit_snippet')
        
        if not filepath:
            raise ValueError("Missing required parameter: filepath")
        if not edit_snippet:
            raise ValueError("Missing required parameter: edit_snippet")
        
        return self.relace_edit_controller.relace_edit(filepath, edit_snippet)
    
    # Handler methods for analysis tools operations
    
    def _handle_find_calls(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Handle codebase.find_calls operation."""
        func_name = params.get('func_name')
        arg_patterns = params.get('arg_patterns')
        
        if not func_name:
            raise ValueError("Missing required parameter: func_name")
        
        return self.code_analysis_controller.find_calls(func_name, arg_patterns)
    
    def _handle_commit(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle codebase.commit operation."""
        message = params.get('message', '')
        
        return self.code_analysis_controller.commit(message)
    
    def _handle_visualize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle codebase.visualize operation."""
        graph_data = params.get('graph')
        
        if not graph_data:
            raise ValueError("Missing required parameter: graph")
        
        # Create a call graph from the data
        graph = CallGraph()
        
        # Add nodes
        for node_data in graph_data.get('nodes', []):
            # Create a function from the node data
            func = Function(name=node_data.get('name', ''))
            graph.nodes.append(func)
        
        # Add edges
        graph.edges = graph_data.get('edges', [])
        
        return self.code_analysis_controller.visualize(graph)
    
    def _handle_create_call_graph(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle create_call_graph operation."""
        start_func_name = params.get('start_func')
        end_func_name = params.get('end_func')
        max_depth = params.get('max_depth', 5)
        
        if not start_func_name:
            raise ValueError("Missing required parameter: start_func")
        
        # Get the start function
        start_func = None
        for func in self.symbol_controller.functions():
            if func.name == start_func_name:
                start_func = func
                break
        
        if not start_func:
            raise ValueError(f"Function not found: {start_func_name}")
        
        # Get the end function if provided
        end_func = None
        if end_func_name:
            for func in self.symbol_controller.functions():
                if func.name == end_func_name:
                    end_func = func
                    break
            
            if not end_func:
                raise ValueError(f"Function not found: {end_func_name}")
        
        graph = self.code_analysis_controller.create_call_graph(start_func, end_func, max_depth)
        return graph.to_dict()
    
    def _handle_find_dead_code(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Handle find_dead_code operation."""
        functions = self.code_analysis_controller.find_dead_code()
        return [f.to_dict() for f in functions]
    
    def _handle_get_max_call_chain(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Handle get_max_call_chain operation."""
        function_name = params.get('function')
        
        if not function_name:
            raise ValueError("Missing required parameter: function")
        
        # Get the function
        function = None
        for func in self.symbol_controller.functions():
            if func.name == function_name:
                function = func
                break
        
        if not function:
            raise ValueError(f"Function not found: {function_name}")
        
        functions = self.code_analysis_controller.get_max_call_chain(function)
        return [f.to_dict() for f in functions]
    
    def _handle_get_codebase_summary(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle get_codebase_summary operation."""
        return self.codebase_analysis_controller.get_codebase_summary()
    
    def _handle_get_file_summary(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle get_file_summary operation."""
        file_path = params.get('file')
        
        if not file_path:
            raise ValueError("Missing required parameter: file")
        
        # Get the file
        file = None
        for f in self.codebase.files:
            if f.path == file_path:
                file = f
                break
        
        if not file:
            raise ValueError(f"File not found: {file_path}")
        
        return self.codebase_analysis_controller.get_file_summary(file)
    
    def _handle_get_class_summary(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle get_class_summary operation."""
        class_name = params.get('cls')
        
        if not class_name:
            raise ValueError("Missing required parameter: cls")
        
        # Get the class
        cls = None
        for c in self.symbol_controller.classes():
            if c.name == class_name:
                cls = c
                break
        
        if not cls:
            raise ValueError(f"Class not found: {class_name}")
        
        return self.codebase_analysis_controller.get_class_summary(cls)
    
    def _handle_get_function_summary(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle get_function_summary operation."""
        function_name = params.get('function')
        
        if not function_name:
            raise ValueError("Missing required parameter: function")
        
        # Get the function
        function = None
        for func in self.symbol_controller.functions():
            if func.name == function_name:
                function = func
                break
        
        if not function:
            raise ValueError(f"Function not found: {function_name}")
        
        return self.codebase_analysis_controller.get_function_summary(function)
