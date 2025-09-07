"""
Integrated Documentation Generator using all available tools.

This module integrates documentation generation tools from the extensions/tools
directory to provide comprehensive documentation generation capabilities.
"""

import logging
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from pathlib import Path
import json
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor

from .config import DocGenConfig

# Import tools from extensions/tools
from ..tools.document_functions import document_functions
from ..tools.generate_docs_json import generate_docs_json
from ..tools.mdx_docs_generation import generate_mdx_docs
from ..tools.reveal_symbol import reveal_symbol
from ..tools.reflection import reflect_on_code
from ..tools.view_file import view_file
from ..tools.list_directory import list_directory

logger = logging.getLogger(__name__)


@dataclass
class DocumentationResult:
    """Result of documentation generation"""
    success: bool
    output_path: str
    files_generated: List[str] = field(default_factory=list)
    symbols_documented: int = 0
    duration_seconds: float = 0.0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


@dataclass
class SymbolDocumentation:
    """Documentation for a single symbol"""
    symbol_name: str
    symbol_type: str
    file_path: str
    line_number: int
    signature: Optional[str] = None
    docstring: Optional[str] = None
    parameters: List[Dict[str, Any]] = field(default_factory=list)
    return_type: Optional[str] = None
    examples: List[str] = field(default_factory=list)
    related_symbols: List[str] = field(default_factory=list)
    source_code: Optional[str] = None


class IntegratedDocumentationGenerator:
    """Comprehensive documentation generator using all available tools"""
    
    def __init__(self, 
                 config: DocGenConfig,
                 codebase=None,
                 serena_agent=None):
        self.config = config
        self.codebase = codebase
        self.serena_agent = serena_agent
        self.logger = logging.getLogger(__name__)
        
        # Thread pool for parallel processing
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # Documentation cache
        self._doc_cache: Dict[str, SymbolDocumentation] = {}
        self._cache_timestamps: Dict[str, float] = {}
    
    def generate_comprehensive_docs(self, output_path: Optional[str] = None) -> DocumentationResult:
        """Generate comprehensive documentation for the entire codebase"""
        start_time = time.time()
        
        if not self.config.enabled:
            return DocumentationResult(
                success=False,
                output_path="",
                errors=["Documentation generation is disabled"]
            )
        
        output_path = output_path or self.config.output_directory
        output_dir = Path(output_path)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger.info(f"Starting comprehensive documentation generation to {output_path}")
        
        files_generated = []
        errors = []
        warnings = []
        symbols_documented = 0
        
        try:
            # Generate API documentation
            if self.config.generate_api_docs:
                try:
                    api_result = self._generate_api_documentation(output_dir)
                    files_generated.extend(api_result.get('files', []))
                    symbols_documented += api_result.get('symbols_count', 0)
                except Exception as e:
                    error_msg = f"API documentation generation failed: {e}"
                    self.logger.error(error_msg)
                    errors.append(error_msg)
            
            # Generate symbol documentation
            if self.config.generate_symbol_docs:
                try:
                    symbol_result = self._generate_symbol_documentation(output_dir)
                    files_generated.extend(symbol_result.get('files', []))
                    symbols_documented += symbol_result.get('symbols_count', 0)
                except Exception as e:
                    error_msg = f"Symbol documentation generation failed: {e}"
                    self.logger.error(error_msg)
                    errors.append(error_msg)
            
            # Generate usage examples
            if self.config.generate_usage_examples:
                try:
                    examples_result = self._generate_usage_examples(output_dir)
                    files_generated.extend(examples_result.get('files', []))
                except Exception as e:
                    error_msg = f"Usage examples generation failed: {e}"
                    self.logger.error(error_msg)
                    errors.append(error_msg)
            
            # Generate type documentation
            if self.config.generate_type_docs:
                try:
                    types_result = self._generate_type_documentation(output_dir)
                    files_generated.extend(types_result.get('files', []))
                except Exception as e:
                    error_msg = f"Type documentation generation failed: {e}"
                    self.logger.error(error_msg)
                    errors.append(error_msg)
            
            # Generate cross-references if enabled
            if self.config.generate_cross_references:
                try:
                    cross_ref_result = self._generate_cross_references(output_dir)
                    files_generated.extend(cross_ref_result.get('files', []))
                except Exception as e:
                    warning_msg = f"Cross-reference generation failed: {e}"
                    self.logger.warning(warning_msg)
                    warnings.append(warning_msg)
            
            # Generate dependency graphs if enabled
            if self.config.include_dependency_graphs:
                try:
                    deps_result = self._generate_dependency_graphs(output_dir)
                    files_generated.extend(deps_result.get('files', []))
                except Exception as e:
                    warning_msg = f"Dependency graph generation failed: {e}"
                    self.logger.warning(warning_msg)
                    warnings.append(warning_msg)
            
            duration = time.time() - start_time
            success = len(errors) == 0
            
            self.logger.info(f"Documentation generation completed in {duration:.2f}s: "
                           f"{len(files_generated)} files, {symbols_documented} symbols")
            
            return DocumentationResult(
                success=success,
                output_path=str(output_dir),
                files_generated=files_generated,
                symbols_documented=symbols_documented,
                duration_seconds=duration,
                errors=errors,
                warnings=warnings
            )
            
        except Exception as e:
            duration = time.time() - start_time
            error_msg = f"Documentation generation failed: {e}"
            self.logger.error(error_msg)
            
            return DocumentationResult(
                success=False,
                output_path=str(output_dir),
                files_generated=files_generated,
                symbols_documented=symbols_documented,
                duration_seconds=duration,
                errors=[error_msg] + errors,
                warnings=warnings
            )
    
    def _generate_api_documentation(self, output_dir: Path) -> Dict[str, Any]:
        """Generate API documentation using generate_docs_json tool"""
        self.logger.info("Generating API documentation...")
        
        files_generated = []
        symbols_count = 0
        
        # Use generate_docs_json tool
        if self.config.use_generate_docs_json:
            try:
                # This would call the actual generate_docs_json function
                # For now, create a placeholder
                api_docs = self._collect_api_symbols()
                
                # Generate JSON documentation
                if 'json' in self.config.output_formats:
                    json_file = output_dir / 'api_documentation.json'
                    with open(json_file, 'w', encoding='utf-8') as f:
                        json.dump(api_docs, f, indent=2)
                    files_generated.append(str(json_file))
                
                # Generate MDX documentation
                if 'mdx' in self.config.output_formats and self.config.use_mdx_generation:
                    mdx_file = output_dir / 'api_documentation.mdx'
                    mdx_content = self._convert_to_mdx(api_docs)
                    with open(mdx_file, 'w', encoding='utf-8') as f:
                        f.write(mdx_content)
                    files_generated.append(str(mdx_file))
                
                symbols_count = len(api_docs.get('symbols', []))
                
            except Exception as e:
                self.logger.error(f"API documentation generation failed: {e}")
                raise
        
        return {
            'files': files_generated,
            'symbols_count': symbols_count
        }
    
    def _generate_symbol_documentation(self, output_dir: Path) -> Dict[str, Any]:
        """Generate symbol documentation using reveal_symbol tool"""
        self.logger.info("Generating symbol documentation...")
        
        files_generated = []
        symbols_count = 0
        
        if self.config.use_reveal_symbol:
            try:
                # Get all symbols from the codebase
                symbols = self._discover_symbols()
                
                symbol_docs = []
                
                # Process symbols in batches
                batch_size = self.config.max_symbols_per_batch
                for i in range(0, len(symbols), batch_size):
                    batch = symbols[i:i + batch_size]
                    batch_docs = self._process_symbol_batch(batch)
                    symbol_docs.extend(batch_docs)
                
                # Generate documentation files
                if 'json' in self.config.output_formats:
                    symbols_file = output_dir / 'symbols.json'
                    with open(symbols_file, 'w', encoding='utf-8') as f:
                        json.dump([doc.__dict__ for doc in symbol_docs], f, indent=2)
                    files_generated.append(str(symbols_file))
                
                if 'mdx' in self.config.output_formats:
                    # Generate individual MDX files for each symbol
                    symbols_dir = output_dir / 'symbols'
                    symbols_dir.mkdir(exist_ok=True)
                    
                    for doc in symbol_docs:
                        mdx_file = symbols_dir / f"{doc.symbol_name}.mdx"
                        mdx_content = self._symbol_to_mdx(doc)
                        with open(mdx_file, 'w', encoding='utf-8') as f:
                            f.write(mdx_content)
                        files_generated.append(str(mdx_file))
                
                symbols_count = len(symbol_docs)
                
            except Exception as e:
                self.logger.error(f"Symbol documentation generation failed: {e}")
                raise
        
        return {
            'files': files_generated,
            'symbols_count': symbols_count
        }
    
    def _generate_usage_examples(self, output_dir: Path) -> Dict[str, Any]:
        """Generate usage examples documentation"""
        self.logger.info("Generating usage examples...")
        
        files_generated = []
        
        try:
            # Collect usage examples from the codebase
            examples = self._collect_usage_examples()
            
            if examples:
                examples_file = output_dir / 'usage_examples.json'
                with open(examples_file, 'w', encoding='utf-8') as f:
                    json.dump(examples, f, indent=2)
                files_generated.append(str(examples_file))
                
                if 'mdx' in self.config.output_formats:
                    mdx_file = output_dir / 'usage_examples.mdx'
                    mdx_content = self._examples_to_mdx(examples)
                    with open(mdx_file, 'w', encoding='utf-8') as f:
                        f.write(mdx_content)
                    files_generated.append(str(mdx_file))
        
        except Exception as e:
            self.logger.error(f"Usage examples generation failed: {e}")
            raise
        
        return {'files': files_generated}
    
    def _generate_type_documentation(self, output_dir: Path) -> Dict[str, Any]:
        """Generate type documentation"""
        self.logger.info("Generating type documentation...")
        
        files_generated = []
        
        if self.config.include_type_annotations:
            try:
                # Collect type information
                types_info = self._collect_type_information()
                
                if types_info:
                    types_file = output_dir / 'types.json'
                    with open(types_file, 'w', encoding='utf-8') as f:
                        json.dump(types_info, f, indent=2)
                    files_generated.append(str(types_file))
                    
                    if 'mdx' in self.config.output_formats:
                        mdx_file = output_dir / 'types.mdx'
                        mdx_content = self._types_to_mdx(types_info)
                        with open(mdx_file, 'w', encoding='utf-8') as f:
                            f.write(mdx_content)
                        files_generated.append(str(mdx_file))
            
            except Exception as e:
                self.logger.error(f"Type documentation generation failed: {e}")
                raise
        
        return {'files': files_generated}
    
    def _generate_cross_references(self, output_dir: Path) -> Dict[str, Any]:
        """Generate cross-reference documentation"""
        self.logger.info("Generating cross-references...")
        
        files_generated = []
        
        try:
            # Build cross-reference map
            cross_refs = self._build_cross_references()
            
            if cross_refs:
                cross_refs_file = output_dir / 'cross_references.json'
                with open(cross_refs_file, 'w', encoding='utf-8') as f:
                    json.dump(cross_refs, f, indent=2)
                files_generated.append(str(cross_refs_file))
        
        except Exception as e:
            self.logger.error(f"Cross-reference generation failed: {e}")
            raise
        
        return {'files': files_generated}
    
    def _generate_dependency_graphs(self, output_dir: Path) -> Dict[str, Any]:
        """Generate dependency graph documentation"""
        self.logger.info("Generating dependency graphs...")
        
        files_generated = []
        
        try:
            # Build dependency graph
            dep_graph = self._build_dependency_graph()
            
            if dep_graph:
                deps_file = output_dir / 'dependencies.json'
                with open(deps_file, 'w', encoding='utf-8') as f:
                    json.dump(dep_graph, f, indent=2)
                files_generated.append(str(deps_file))
                
                # Generate Mermaid diagram if possible
                mermaid_content = self._generate_mermaid_diagram(dep_graph)
                if mermaid_content:
                    mermaid_file = output_dir / 'dependencies.mmd'
                    with open(mermaid_file, 'w', encoding='utf-8') as f:
                        f.write(mermaid_content)
                    files_generated.append(str(mermaid_file))
        
        except Exception as e:
            self.logger.error(f"Dependency graph generation failed: {e}")
            raise
        
        return {'files': files_generated}
    
    def _collect_api_symbols(self) -> Dict[str, Any]:
        """Collect API symbols for documentation"""
        # This would integrate with the actual generate_docs_json tool
        return {
            'symbols': [],
            'metadata': {
                'generated_at': time.time(),
                'generator': 'IntegratedDocumentationGenerator'
            }
        }
    
    def _discover_symbols(self) -> List[str]:
        """Discover all symbols in the codebase"""
        symbols = []
        
        # Use Serena tools if available
        if self.serena_agent:
            try:
                # This would use Serena's symbol discovery tools
                pass
            except Exception as e:
                self.logger.warning(f"Serena symbol discovery failed: {e}")
        
        # Fallback to basic discovery
        # This would scan the codebase for symbols
        
        return symbols
    
    def _process_symbol_batch(self, symbols: List[str]) -> List[SymbolDocumentation]:
        """Process a batch of symbols for documentation"""
        docs = []
        
        for symbol in symbols:
            try:
                # Use reveal_symbol tool
                if self.config.use_reveal_symbol:
                    symbol_info = reveal_symbol(symbol, self.codebase)
                    if symbol_info:
                        doc = self._create_symbol_documentation(symbol, symbol_info)
                        docs.append(doc)
            except Exception as e:
                self.logger.warning(f"Failed to document symbol {symbol}: {e}")
        
        return docs
    
    def _create_symbol_documentation(self, symbol_name: str, symbol_info: Any) -> SymbolDocumentation:
        """Create documentation for a symbol"""
        return SymbolDocumentation(
            symbol_name=symbol_name,
            symbol_type=getattr(symbol_info, 'type', 'unknown'),
            file_path=getattr(symbol_info, 'file_path', ''),
            line_number=getattr(symbol_info, 'line_number', 0),
            signature=getattr(symbol_info, 'signature', None),
            docstring=getattr(symbol_info, 'docstring', None),
            parameters=getattr(symbol_info, 'parameters', []),
            return_type=getattr(symbol_info, 'return_type', None),
            source_code=getattr(symbol_info, 'source_code', None)
        )
    
    def _collect_usage_examples(self) -> List[Dict[str, Any]]:
        """Collect usage examples from the codebase"""
        examples = []
        
        # This would scan for example code, tests, etc.
        
        return examples
    
    def _collect_type_information(self) -> Dict[str, Any]:
        """Collect type information from the codebase"""
        types_info = {}
        
        # This would analyze type annotations, etc.
        
        return types_info
    
    def _build_cross_references(self) -> Dict[str, Any]:
        """Build cross-reference map"""
        cross_refs = {}
        
        # This would analyze symbol relationships
        
        return cross_refs
    
    def _build_dependency_graph(self) -> Dict[str, Any]:
        """Build dependency graph"""
        dep_graph = {
            'nodes': [],
            'edges': []
        }
        
        # This would analyze import dependencies
        
        return dep_graph
    
    def _convert_to_mdx(self, api_docs: Dict[str, Any]) -> str:
        """Convert API docs to MDX format"""
        mdx_content = "# API Documentation\n\n"
        
        # This would generate proper MDX content
        
        return mdx_content
    
    def _symbol_to_mdx(self, doc: SymbolDocumentation) -> str:
        """Convert symbol documentation to MDX"""
        mdx_content = f"# {doc.symbol_name}\n\n"
        
        if doc.docstring:
            mdx_content += f"{doc.docstring}\n\n"
        
        if doc.signature:
            mdx_content += f"## Signature\n\n```python\n{doc.signature}\n```\n\n"
        
        if doc.parameters:
            mdx_content += "## Parameters\n\n"
            for param in doc.parameters:
                mdx_content += f"- **{param.get('name', '')}**: {param.get('description', '')}\n"
            mdx_content += "\n"
        
        if doc.source_code and self.config.include_source_links:
            mdx_content += f"## Source\n\n[View source]({doc.file_path}#L{doc.line_number})\n\n"
        
        return mdx_content
    
    def _examples_to_mdx(self, examples: List[Dict[str, Any]]) -> str:
        """Convert usage examples to MDX"""
        mdx_content = "# Usage Examples\n\n"
        
        for example in examples:
            title = example.get('title', 'Example')
            code = example.get('code', '')
            description = example.get('description', '')
            
            mdx_content += f"## {title}\n\n"
            if description:
                mdx_content += f"{description}\n\n"
            if code:
                mdx_content += f"```python\n{code}\n```\n\n"
        
        return mdx_content
    
    def _types_to_mdx(self, types_info: Dict[str, Any]) -> str:
        """Convert type information to MDX"""
        mdx_content = "# Type Documentation\n\n"
        
        # This would generate proper type documentation
        
        return mdx_content
    
    def _generate_mermaid_diagram(self, dep_graph: Dict[str, Any]) -> str:
        """Generate Mermaid diagram from dependency graph"""
        mermaid_content = "graph TD\n"
        
        # This would generate proper Mermaid syntax
        
        return mermaid_content
    
    def generate_symbol_docs(self, symbol_name: str) -> Optional[SymbolDocumentation]:
        """Generate documentation for a specific symbol"""
        try:
            # Check cache first
            if self.config.cache_generated_docs:
                cached_doc = self._get_cached_doc(symbol_name)
                if cached_doc:
                    return cached_doc
            
            # Generate new documentation
            if self.config.use_reveal_symbol:
                symbol_info = reveal_symbol(symbol_name, self.codebase)
                if symbol_info:
                    doc = self._create_symbol_documentation(symbol_name, symbol_info)
                    
                    # Cache the result
                    if self.config.cache_generated_docs:
                        self._cache_doc(symbol_name, doc)
                    
                    return doc
        
        except Exception as e:
            self.logger.error(f"Failed to generate documentation for {symbol_name}: {e}")
        
        return None
    
    def _get_cached_doc(self, symbol_name: str) -> Optional[SymbolDocumentation]:
        """Get cached documentation for a symbol"""
        if symbol_name in self._doc_cache:
            timestamp = self._cache_timestamps.get(symbol_name, 0)
            # Cache for 1 hour
            if time.time() - timestamp < 3600:
                return self._doc_cache[symbol_name]
            else:
                # Remove expired entry
                del self._doc_cache[symbol_name]
                del self._cache_timestamps[symbol_name]
        
        return None
    
    def _cache_doc(self, symbol_name: str, doc: SymbolDocumentation) -> None:
        """Cache documentation for a symbol"""
        self._doc_cache[symbol_name] = doc
        self._cache_timestamps[symbol_name] = time.time()
    
    def cleanup(self) -> None:
        """Cleanup resources"""
        if self.executor:
            self.executor.shutdown(wait=True)
        
        self._doc_cache.clear()
        self._cache_timestamps.clear()
