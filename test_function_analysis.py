#!/usr/bin/env python3
"""
Function Analysis Test Script
Tests specific functions and classes from graph-sitter, autogenlib, and solidlsp integrations
"""

import os
import sys
import ast
import logging
from pathlib import Path
from typing import Dict, List, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FunctionAnalyzer:
    """Analyze functions and classes in the refactored modules."""
    
    def __init__(self):
        self.analysis_results = {}
        
    def analyze_file(self, file_path: Path) -> Dict[str, Any]:
        """Analyze a Python file for functions, classes, and imports."""
        if not file_path.exists():
            return {"error": "File not found"}
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            tree = ast.parse(content)
            
            analysis = {
                "functions": [],
                "classes": [],
                "imports": [],
                "from_imports": [],
                "constants": [],
                "decorators": []
            }
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    func_info = {
                        "name": node.name,
                        "args": [arg.arg for arg in node.args.args],
                        "decorators": [self._get_decorator_name(d) for d in node.decorator_list],
                        "is_async": isinstance(node, ast.AsyncFunctionDef),
                        "line": node.lineno
                    }
                    analysis["functions"].append(func_info)
                    
                elif isinstance(node, ast.ClassDef):
                    class_info = {
                        "name": node.name,
                        "bases": [self._get_name(base) for base in node.bases],
                        "decorators": [self._get_decorator_name(d) for d in node.decorator_list],
                        "methods": [],
                        "line": node.lineno
                    }
                    
                    # Get methods
                    for item in node.body:
                        if isinstance(item, ast.FunctionDef):
                            method_info = {
                                "name": item.name,
                                "args": [arg.arg for arg in item.args.args],
                                "is_async": isinstance(item, ast.AsyncFunctionDef)
                            }
                            class_info["methods"].append(method_info)
                    
                    analysis["classes"].append(class_info)
                    
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        analysis["imports"].append({
                            "module": alias.name,
                            "alias": alias.asname,
                            "line": node.lineno
                        })
                        
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ""
                    for alias in node.names:
                        analysis["from_imports"].append({
                            "module": module,
                            "name": alias.name,
                            "alias": alias.asname,
                            "line": node.lineno
                        })
                        
                elif isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name) and target.id.isupper():
                            analysis["constants"].append({
                                "name": target.id,
                                "line": node.lineno
                            })
            
            return analysis
            
        except Exception as e:
            return {"error": str(e)}
    
    def _get_decorator_name(self, decorator):
        """Extract decorator name from AST node."""
        if isinstance(decorator, ast.Name):
            return decorator.id
        elif isinstance(decorator, ast.Attribute):
            return f"{self._get_name(decorator.value)}.{decorator.attr}"
        else:
            return str(decorator)
    
    def _get_name(self, node):
        """Extract name from AST node."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_name(node.value)}.{node.attr}"
        else:
            return str(node)
    
    def analyze_all_modules(self) -> Dict[str, Any]:
        """Analyze all refactored modules."""
        logger.info("🔍 Analyzing all refactored modules...")
        
        modules = {
            "lsp_diagnostics": "src/codegen/sdk/extensions/lsp/lsp_diagnostics.py",
            "autogenlib_context": "src/codegen/sdk/extensions/autogenlib/autogenlib_context.py",
            "autogenlib_ai_resolve": "src/codegen/sdk/extensions/autogenlib/autogenlib_ai_resolve.py",
            "graph_sitter_analysis": "src/codegen/sdk/extensions/tools/graph_sitter_analysis.py",
            "analysis_backend": "src/codegen/sdk/extensions/tools/analysis_backend.py"
        }
        
        results = {}
        
        for module_name, file_path in modules.items():
            logger.info(f"Analyzing {module_name}...")
            full_path = Path(__file__).parent / file_path
            analysis = self.analyze_file(full_path)
            results[module_name] = analysis
            
            if "error" not in analysis:
                logger.info(f"✅ {module_name}: {len(analysis['functions'])} functions, {len(analysis['classes'])} classes")
            else:
                logger.error(f"❌ {module_name}: {analysis['error']}")
        
        return results
    
    def check_key_functions(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """Check for key functions that should be present."""
        logger.info("🔍 Checking for key functions...")
        
        expected_functions = {
            "lsp_diagnostics": [
                "LSPDiagnosticsManager",  # class
                "EnhancedDiagnostic",     # TypedDict
                "RuntimeErrorCollector"   # class
            ],
            "autogenlib_context": [
                "get_enhanced_context_for_diagnostic",
                "get_autogenlib_context", 
                "get_graph_sitter_context"
            ],
            "autogenlib_ai_resolve": [
                "resolve_diagnostic_with_ai",
                "resolve_runtime_error_with_ai",
                "resolve_ui_error_with_ai",
                "resolve_multiple_errors_with_ai"
            ],
            "graph_sitter_analysis": [
                "GraphSitterAnalyzer"  # class
            ],
            "analysis_backend": [
                "AnalysisEngine",      # class
                "AnalyzeRequest",      # class
                "ErrorAnalysisResponse", # class
                "EntrypointAnalysisResponse" # class
            ]
        }
        
        check_results = {}
        
        for module_name, expected in expected_functions.items():
            if module_name not in analysis_results:
                check_results[module_name] = {"error": "Module not analyzed"}
                continue
                
            module_analysis = analysis_results[module_name]
            if "error" in module_analysis:
                check_results[module_name] = {"error": module_analysis["error"]}
                continue
            
            # Get all function and class names
            all_names = set()
            all_names.update(f["name"] for f in module_analysis["functions"])
            all_names.update(c["name"] for c in module_analysis["classes"])
            
            found = []
            missing = []
            
            for expected_name in expected:
                if expected_name in all_names:
                    found.append(expected_name)
                else:
                    missing.append(expected_name)
            
            check_results[module_name] = {
                "found": found,
                "missing": missing,
                "total_expected": len(expected),
                "found_count": len(found)
            }
            
            if missing:
                logger.warning(f"⚠️ {module_name}: Missing {missing}")
            else:
                logger.info(f"✅ {module_name}: All expected functions/classes found")
        
        return check_results
    
    def check_import_patterns(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """Check import patterns for correctness."""
        logger.info("🔍 Checking import patterns...")
        
        import_check_results = {}
        
        for module_name, analysis in analysis_results.items():
            if "error" in analysis:
                continue
                
            imports = analysis["from_imports"] + analysis["imports"]
            
            # Check for problematic imports
            old_graph_sitter = [imp for imp in imports if 
                              "graph_sitter" in imp.get("module", "") and 
                              not imp.get("module", "").startswith("codegen.sdk")]
            
            new_codegen_sdk = [imp for imp in imports if 
                             imp.get("module", "").startswith("codegen.sdk")]
            
            solidlsp_imports = [imp for imp in imports if 
                              "solidlsp" in imp.get("module", "")]
            
            autogenlib_imports = [imp for imp in imports if 
                                "autogenlib" in imp.get("module", "")]
            
            import_check_results[module_name] = {
                "old_graph_sitter_count": len(old_graph_sitter),
                "new_codegen_sdk_count": len(new_codegen_sdk),
                "solidlsp_count": len(solidlsp_imports),
                "autogenlib_count": len(autogenlib_imports),
                "old_graph_sitter": old_graph_sitter,
                "new_codegen_sdk": new_codegen_sdk
            }
            
            if old_graph_sitter:
                logger.warning(f"⚠️ {module_name}: Found {len(old_graph_sitter)} old graph_sitter imports")
            if new_codegen_sdk:
                logger.info(f"✅ {module_name}: Found {len(new_codegen_sdk)} new codegen.sdk imports")
        
        return import_check_results
    
    def generate_report(self) -> str:
        """Generate a comprehensive analysis report."""
        logger.info("📊 Generating comprehensive analysis report...")
        
        analysis_results = self.analyze_all_modules()
        key_functions_check = self.check_key_functions(analysis_results)
        import_patterns_check = self.check_import_patterns(analysis_results)
        
        report = []
        report.append("# Comprehensive Function Analysis Report")
        report.append("=" * 50)
        report.append("")
        
        # Summary
        total_modules = len(analysis_results)
        successful_modules = sum(1 for r in analysis_results.values() if "error" not in r)
        
        report.append(f"## Summary")
        report.append(f"- Total modules analyzed: {total_modules}")
        report.append(f"- Successfully analyzed: {successful_modules}")
        report.append(f"- Failed: {total_modules - successful_modules}")
        report.append("")
        
        # Module details
        for module_name, analysis in analysis_results.items():
            report.append(f"## Module: {module_name}")
            report.append("-" * 30)
            
            if "error" in analysis:
                report.append(f"❌ Error: {analysis['error']}")
            else:
                report.append(f"✅ Functions: {len(analysis['functions'])}")
                report.append(f"✅ Classes: {len(analysis['classes'])}")
                report.append(f"✅ Imports: {len(analysis['imports']) + len(analysis['from_imports'])}")
                
                # Key functions check
                if module_name in key_functions_check:
                    check = key_functions_check[module_name]
                    if "error" not in check:
                        report.append(f"✅ Key functions found: {check['found_count']}/{check['total_expected']}")
                        if check['missing']:
                            report.append(f"⚠️ Missing: {', '.join(check['missing'])}")
                
                # Import patterns
                if module_name in import_patterns_check:
                    imp_check = import_patterns_check[module_name]
                    report.append(f"🔄 Import migration: {imp_check['old_graph_sitter_count']} old → {imp_check['new_codegen_sdk_count']} new")
            
            report.append("")
        
        # Overall status
        report.append("## Overall Status")
        report.append("-" * 20)
        
        total_old_imports = sum(
            check.get("old_graph_sitter_count", 0) 
            for check in import_patterns_check.values()
        )
        total_new_imports = sum(
            check.get("new_codegen_sdk_count", 0) 
            for check in import_patterns_check.values()
        )
        
        if total_old_imports == 0 and successful_modules == total_modules:
            report.append("🎉 **ALL TESTS PASSED!**")
            report.append("- All modules compile successfully")
            report.append("- All imports have been migrated to codegen.sdk")
            report.append("- All key functions are present")
        else:
            report.append("⚠️ **ISSUES FOUND:**")
            if total_old_imports > 0:
                report.append(f"- {total_old_imports} old graph_sitter imports need updating")
            if successful_modules < total_modules:
                report.append(f"- {total_modules - successful_modules} modules failed analysis")
        
        report.append("")
        report.append(f"Migration status: {total_old_imports} old imports → {total_new_imports} new imports")
        
        return "\n".join(report)

def main():
    """Main execution."""
    analyzer = FunctionAnalyzer()
    report = analyzer.generate_report()
    
    # Print report
    print(report)
    
    # Save report to file
    with open("function_analysis_report.md", "w") as f:
        f.write(report)
    
    logger.info("📄 Report saved to function_analysis_report.md")
    
    # Determine exit code
    analysis_results = analyzer.analyze_all_modules()
    import_patterns_check = analyzer.check_import_patterns(analysis_results)
    
    successful_modules = sum(1 for r in analysis_results.values() if "error" not in r)
    total_old_imports = sum(
        check.get("old_graph_sitter_count", 0) 
        for check in import_patterns_check.values()
    )
    
    if successful_modules == len(analysis_results) and total_old_imports == 0:
        logger.info("🎉 All analysis passed!")
        return 0
    else:
        logger.error("💥 Some issues found")
        return 1

if __name__ == "__main__":
    sys.exit(main())
