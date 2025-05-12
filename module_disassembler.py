#!/usr/bin/env python3
"""
Module Disassembler and Restructurer

This tool analyzes a codebase, identifies duplicate and redundant code,
and restructures modules based on their functionality.

It builds on the existing CodebaseAnalyzer from codegen-on-oss to provide
additional functionality for deduplication and module restructuring.
"""

import os
import sys
import json
import time
import logging
import argparse
import tempfile
import re
import hashlib
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any, Optional, Union, Callable
from collections import Counter, defaultdict
import networkx as nx
import matplotlib.pyplot as plt
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn

try:
    from codegen.sdk.core.codebase import Codebase
    from codegen.configs.models.codebase import CodebaseConfig
    from codegen.configs.models.secrets import SecretsConfig
    from codegen.shared.enums.programming_language import ProgrammingLanguage
    # Import the CodebaseAnalyzer if available
    try:
        from codegen_on_oss.error_analyzer import CodebaseAnalyzer
        HAS_ANALYZER = True
    except ImportError:
        HAS_ANALYZER = False
except ImportError:
    print("Codegen SDK not found. Please install it first.")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Rich console for pretty output
console = Console()

class FunctionSignature:
    """Represents a function signature for comparison purposes."""
    
    def __init__(self, name: str, params: List[str], body: str, file_path: str, start_line: int, end_line: int):
        self.name = name
        self.params = params
        self.body = self._normalize_body(body)
        self.file_path = file_path
        self.start_line = start_line
        self.end_line = end_line
        self.hash = self._compute_hash()
        
    def _normalize_body(self, body: str) -> str:
        """Normalize function body for comparison by removing whitespace and comments."""
        # Remove comments
        body = re.sub(r'#.*$', '', body, flags=re.MULTILINE)
        # Remove docstrings (simple approach)
        body = re.sub(r'""".*?"""', '', body, flags=re.DOTALL)
        body = re.sub(r"'''.*?'''", '', body, flags=re.DOTALL)
        # Normalize whitespace
        body = re.sub(r'\s+', ' ', body).strip()
        return body
    
    def _compute_hash(self) -> str:
        """Compute a hash of the normalized function body for quick comparison."""
        return hashlib.md5(self.body.encode()).hexdigest()
    
    def is_similar_to(self, other: 'FunctionSignature', threshold: float = 0.8) -> bool:
        """Check if this function is similar to another function."""
        # Quick check using hash
        if self.hash == other.hash:
            return True
        
        # More detailed comparison for near-duplicates
        # This is a simple implementation - could be improved with more sophisticated
        # code similarity algorithms
        
        # Simple approach: count common substrings
        common_chars = sum(1 for a, b in zip(self.body, other.body) if a == b)
        max_length = max(len(self.body), len(other.body))
        if max_length == 0:
            return False
        
        similarity = common_chars / max_length
        return similarity >= threshold

class ModuleDisassembler:
    """
    Analyzes a codebase, identifies duplicate and redundant code,
    and restructures modules based on their functionality.
    """
    
    def __init__(self, repo_path: str, output_dir: Optional[str] = None):
        self.repo_path = Path(repo_path).resolve()
        self.output_dir = Path(output_dir) if output_dir else self.repo_path / "restructured"
        self.functions: List[FunctionSignature] = []
        self.modules: Dict[str, List[FunctionSignature]] = defaultdict(list)
        self.duplicates: List[Tuple[FunctionSignature, FunctionSignature]] = []
        self.function_groups: Dict[str, List[FunctionSignature]] = {}
        
        # Initialize the codebase
        self.codebase_config = CodebaseConfig(
            path=str(self.repo_path),
            languages=[ProgrammingLanguage.PYTHON],  # Can be extended for other languages
        )
        self.codebase = Codebase(self.codebase_config)
        
        # Use the existing analyzer if available
        if HAS_ANALYZER:
            self.analyzer = CodebaseAnalyzer(
                repo_path=str(self.repo_path),
                languages=["python"],  # Can be extended
                categories=["codebase_structure", "code_quality", "dependencies"]
            )
        else:
            self.analyzer = None
            logger.warning("CodebaseAnalyzer not available. Some functionality will be limited.")
    
    def analyze(self) -> Dict[str, Any]:
        """
        Analyze the codebase and return the results.
        """
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TimeElapsedColumn(),
        ) as progress:
            # Step 1: Extract all functions from the codebase
            task1 = progress.add_task("[green]Extracting functions...", total=1)
            self._extract_functions()
            progress.update(task1, completed=1)
            
            # Step 2: Identify duplicate functions
            task2 = progress.add_task("[yellow]Identifying duplicates...", total=1)
            self._identify_duplicates()
            progress.update(task2, completed=1)
            
            # Step 3: Group functions by functionality
            task3 = progress.add_task("[blue]Grouping functions...", total=1)
            self._group_functions_by_functionality()
            progress.update(task3, completed=1)
            
            # Step 4: Generate restructured modules
            task4 = progress.add_task("[magenta]Generating restructured modules...", total=1)
            self._generate_restructured_modules()
            progress.update(task4, completed=1)
        
        # Return the analysis results
        return {
            "total_functions": len(self.functions),
            "total_modules": len(self.modules),
            "duplicate_functions": len(self.duplicates),
            "function_groups": {name: len(funcs) for name, funcs in self.function_groups.items()},
            "restructured_modules": len(self.function_groups)
        }
    
    def _extract_functions(self):
        """Extract all functions from the codebase."""
        logger.info("Extracting functions from codebase...")
        
        # Use the codebase to get all Python files
        python_files = [f for f in self.repo_path.glob("**/*.py") 
                       if not any(part.startswith('.') for part in f.parts)]
        
        for file_path in python_files:
            rel_path = file_path.relative_to(self.repo_path)
            module_name = str(rel_path).replace('/', '.').replace('\\', '.').replace('.py', '')
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Simple function extraction using regex
                # This is a basic implementation - the real implementation would use AST parsing
                function_matches = re.finditer(
                    r'def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\((.*?)\)(?:\s*->.*?)?\s*:(?:\s*""".*?""")?(?:\s*\'\'\'.*?\'\'\')?(.+?)(?=\n\S|$)',
                    content,
                    re.DOTALL
                )
                
                for match in function_matches:
                    name = match.group(1)
                    params = [p.strip() for p in match.group(2).split(',') if p.strip()]
                    body = match.group(3)
                    
                    # Calculate line numbers
                    start_pos = match.start()
                    end_pos = match.end()
                    start_line = content[:start_pos].count('\n') + 1
                    end_line = start_line + content[start_pos:end_pos].count('\n')
                    
                    func_sig = FunctionSignature(
                        name=name,
                        params=params,
                        body=body,
                        file_path=str(rel_path),
                        start_line=start_line,
                        end_line=end_line
                    )
                    
                    self.functions.append(func_sig)
                    self.modules[module_name].append(func_sig)
            
            except Exception as e:
                logger.error(f"Error processing file {file_path}: {e}")
        
        logger.info(f"Extracted {len(self.functions)} functions from {len(self.modules)} modules")
    
    def _identify_duplicates(self):
        """Identify duplicate functions in the codebase."""
        logger.info("Identifying duplicate functions...")
        
        # Group functions by hash for quick exact duplicate detection
        functions_by_hash = defaultdict(list)
        for func in self.functions:
            functions_by_hash[func.hash].append(func)
        
        # Find exact duplicates
        exact_duplicates = []
        for hash_val, funcs in functions_by_hash.items():
            if len(funcs) > 1:
                for i in range(len(funcs)):
                    for j in range(i + 1, len(funcs)):
                        exact_duplicates.append((funcs[i], funcs[j]))
        
        # Find near-duplicates (more computationally expensive)
        near_duplicates = []
        for i in range(len(self.functions)):
            for j in range(i + 1, len(self.functions)):
                func1 = self.functions[i]
                func2 = self.functions[j]
                
                # Skip if they're already identified as exact duplicates
                if any((func1 == pair[0] and func2 == pair[1]) or 
                       (func1 == pair[1] and func2 == pair[0]) for pair in exact_duplicates):
                    continue
                
                if func1.is_similar_to(func2, threshold=0.8):
                    near_duplicates.append((func1, func2))
        
        self.duplicates = exact_duplicates + near_duplicates
        logger.info(f"Found {len(exact_duplicates)} exact duplicates and {len(near_duplicates)} near-duplicates")
    
    def _group_functions_by_functionality(self):
        """Group functions by their functionality."""
        logger.info("Grouping functions by functionality...")
        
        # This is a simplified implementation
        # A more sophisticated approach would use NLP or other techniques to identify function purpose
        
        # Group by name patterns
        name_patterns = {
            "validation": r"(validate|check|verify|is_valid|assert)",
            "data_processing": r"(process|transform|convert|parse|format)",
            "io_operations": r"(read|write|load|save|open|close|import|export)",
            "api_calls": r"(api|request|fetch|get|post|put|delete|http)",
            "authentication": r"(auth|login|logout|register|password|user)",
            "database": r"(db|database|query|sql|table|record|row|column)",
            "utility": r"(util|helper|common|shared)",
            "configuration": r"(config|setting|option|preference|env)",
            "logging": r"(log|debug|info|warning|error|exception)",
            "testing": r"(test|assert|mock|stub|fixture)",
        }
        
        # Initialize groups
        for group_name in name_patterns:
            self.function_groups[group_name] = []
        
        # Assign functions to groups based on name patterns
        for func in self.functions:
            assigned = False
            for group_name, pattern in name_patterns.items():
                if re.search(pattern, func.name, re.IGNORECASE):
                    self.function_groups[group_name].append(func)
                    assigned = True
                    break
            
            if not assigned:
                # Default group for unmatched functions
                if "misc" not in self.function_groups:
                    self.function_groups["misc"] = []
                self.function_groups["misc"].append(func)
        
        # Log the results
        for group_name, funcs in self.function_groups.items():
            logger.info(f"Group '{group_name}': {len(funcs)} functions")
    
    def _generate_restructured_modules(self):
        """Generate restructured modules based on function groups."""
        logger.info("Generating restructured modules...")
        
        # Create output directory if it doesn't exist
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create a module for each function group
        for group_name, funcs in self.function_groups.items():
            if not funcs:
                continue
            
            module_path = self.output_dir / f"{group_name}.py"
            
            with open(module_path, 'w', encoding='utf-8') as f:
                # Write module header
                f.write(f'"""\n{group_name.replace("_", " ").title()} Module\n\n')
                f.write(f'This module contains functions related to {group_name.replace("_", " ")}.\n')
                f.write('Generated by Module Disassembler.\n"""\n\n')
                
                # Write imports (simplified)
                f.write('import os\nimport sys\nimport re\n')
                f.write('from typing import Any, Dict, List, Optional, Tuple, Union\n\n')
                
                # Write functions
                for func in funcs:
                    # Add original location as a comment
                    f.write(f'# Original location: {func.file_path}:{func.start_line}-{func.end_line}\n')
                    
                    # Extract the function definition from the original file
                    try:
                        with open(self.repo_path / func.file_path, 'r', encoding='utf-8') as src_file:
                            lines = src_file.readlines()
                            func_lines = lines[func.start_line - 1:func.end_line]
                            func_text = ''.join(func_lines)
                            
                            # Write the function
                            f.write(func_text)
                            f.write('\n\n')
                    except Exception as e:
                        logger.error(f"Error extracting function {func.name} from {func.file_path}: {e}")
                        # Fallback: write a placeholder
                        f.write(f'def {func.name}({", ".join(func.params)}):\n')
                        f.write('    """Function could not be extracted properly."""\n')
                        f.write('    pass\n\n')
        
        # Generate an __init__.py file that imports all modules
        init_path = self.output_dir / "__init__.py"
        with open(init_path, 'w', encoding='utf-8') as f:
            f.write('"""\nRestructured modules package\n\n')
            f.write('This package contains restructured modules based on functionality.\n')
            f.write('Generated by Module Disassembler.\n"""\n\n')
            
            for group_name in self.function_groups:
                if self.function_groups[group_name]:
                    f.write(f'from . import {group_name}\n')
        
        logger.info(f"Generated {len(self.function_groups)} restructured modules in {self.output_dir}")
    
    def generate_report(self, output_format: str = "console", output_file: Optional[str] = None):
        """Generate a report of the analysis results."""
        logger.info(f"Generating {output_format} report...")
        
        if output_format == "json":
            report = {
                "analysis_timestamp": datetime.datetime.now().isoformat(),
                "repo_path": str(self.repo_path),
                "output_dir": str(self.output_dir),
                "total_functions": len(self.functions),
                "total_modules": len(self.modules),
                "modules": {name: len(funcs) for name, funcs in self.modules.items()},
                "duplicates": [
                    {
                        "function1": {
                            "name": dup[0].name,
                            "file": dup[0].file_path,
                            "lines": f"{dup[0].start_line}-{dup[0].end_line}"
                        },
                        "function2": {
                            "name": dup[1].name,
                            "file": dup[1].file_path,
                            "lines": f"{dup[1].start_line}-{dup[1].end_line}"
                        }
                    }
                    for dup in self.duplicates
                ],
                "function_groups": {
                    name: [
                        {
                            "name": func.name,
                            "file": func.file_path,
                            "lines": f"{func.start_line}-{func.end_line}"
                        }
                        for func in funcs
                    ]
                    for name, funcs in self.function_groups.items()
                }
            }
            
            if output_file:
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(report, f, indent=2)
            else:
                print(json.dumps(report, indent=2))
        
        elif output_format == "console":
            console.print("\n[bold green]Module Disassembler Report[/bold green]")
            console.print(f"Repository: [cyan]{self.repo_path}[/cyan]")
            console.print(f"Output directory: [cyan]{self.output_dir}[/cyan]")
            console.print(f"Total functions: [cyan]{len(self.functions)}[/cyan]")
            console.print(f"Total modules: [cyan]{len(self.modules)}[/cyan]")
            console.print(f"Duplicate functions: [cyan]{len(self.duplicates)}[/cyan]")
            
            # Show duplicates
            if self.duplicates:
                console.print("\n[bold yellow]Duplicate Functions:[/bold yellow]")
                table = Table(show_header=True, header_style="bold magenta")
                table.add_column("Function 1")
                table.add_column("Location 1")
                table.add_column("Function 2")
                table.add_column("Location 2")
                
                for dup in self.duplicates[:20]:  # Limit to 20 for readability
                    table.add_row(
                        dup[0].name,
                        f"{dup[0].file_path}:{dup[0].start_line}-{dup[0].end_line}",
                        dup[1].name,
                        f"{dup[1].file_path}:{dup[1].start_line}-{dup[1].end_line}"
                    )
                
                console.print(table)
                if len(self.duplicates) > 20:
                    console.print(f"... and {len(self.duplicates) - 20} more duplicates")
            
            # Show function groups
            console.print("\n[bold blue]Function Groups:[/bold blue]")
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("Group")
            table.add_column("Count")
            
            for name, funcs in self.function_groups.items():
                table.add_row(name, str(len(funcs)))
            
            console.print(table)
            
            console.print("\n[bold green]Restructured modules generated successfully![/bold green]")
        
        else:
            logger.error(f"Unsupported output format: {output_format}")

def main():
    """Main entry point for the module disassembler."""
    parser = argparse.ArgumentParser(description="Module Disassembler and Restructurer")
    parser.add_argument("--repo-path", required=True, help="Path to the repository to analyze")
    parser.add_argument("--output-dir", help="Directory to output restructured modules")
    parser.add_argument("--output-format", choices=["console", "json"], default="console", help="Output format for the report")
    parser.add_argument("--output-file", help="File to write the report to (for JSON format)")
    
    args = parser.parse_args()
    
    # Initialize the disassembler
    disassembler = ModuleDisassembler(
        repo_path=args.repo_path,
        output_dir=args.output_dir
    )
    
    # Run the analysis
    disassembler.analyze()
    
    # Generate the report
    disassembler.generate_report(
        output_format=args.output_format,
        output_file=args.output_file
    )

if __name__ == "__main__":
    main()

