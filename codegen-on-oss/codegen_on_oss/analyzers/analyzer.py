#!/usr/bin/env python3
"""
Unified Codebase Analyzer Module

This module provides a comprehensive framework for analyzing codebases,
including code quality, dependencies, structure, and visualization support.
It serves as the primary API entry point for the analyzer backend.
"""

import os
import sys
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any, Optional, Union, Type, Callable
from enum import Enum

try:
    from codegen.sdk.core.codebase import Codebase
    from codegen.configs.models.codebase import CodebaseConfig
    from codegen.configs.models.secrets import SecretsConfig
    from codegen.sdk.codebase.config import ProjectConfig
    from codegen.git.schemas.repo_config import RepoConfig
    from codegen.git.repo_operator.repo_operator import RepoOperator
    from codegen.shared.enums.programming_language import ProgrammingLanguage
except ImportError:
    print("Codegen SDK not found. Please install it first.")
    sys.exit(1)

# Import internal modules - these will be replaced with actual imports once implemented
from codegen_on_oss.analyzers.issues import Issue, IssueSeverity, AnalysisType, IssueCategory

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Global file ignore patterns
GLOBAL_FILE_IGNORE_LIST = [
    "__pycache__",
    ".git",
    "node_modules",
    "dist",
    "build",
    ".DS_Store",
    ".pytest_cache",
    ".venv",
    "venv",
    "env",
    ".env",
    ".idea",
    ".vscode",
]

class AnalyzerRegistry:
    """Registry of analyzer plugins."""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AnalyzerRegistry, cls).__new__(cls)
            cls._instance._analyzers = {}
        return cls._instance
    
    def register(self, analysis_type: AnalysisType, analyzer_class: Type['AnalyzerPlugin']):
        """Register an analyzer plugin."""
        self._analyzers[analysis_type] = analyzer_class
    
    def get_analyzer(self, analysis_type: AnalysisType) -> Optional[Type['AnalyzerPlugin']]:
        """Get the analyzer plugin for a specific analysis type."""
        return self._analyzers.get(analysis_type)
    
    def list_analyzers(self) -> Dict[AnalysisType, Type['AnalyzerPlugin']]:
        """Get all registered analyzers."""
        return self._analyzers.copy()

class AnalyzerPlugin:
    """Base class for analyzer plugins."""
    
    def __init__(self, manager: 'AnalyzerManager'):
        """Initialize the analyzer plugin."""
        self.manager = manager
        self.issues = []
    
    def analyze(self) -> Dict[str, Any]:
        """Perform analysis using this plugin."""
        raise NotImplementedError("Analyzer plugins must implement analyze()")
    
    def add_issue(self, issue: Issue):
        """Add an issue to the list."""
        self.manager.add_issue(issue)
        self.issues.append(issue)

class CodeQualityPlugin(AnalyzerPlugin):
    """Plugin for code quality analysis."""
    
    def analyze(self) -> Dict[str, Any]:
        """Perform code quality analysis."""
        # This is a simplified placeholder - would import and use code_quality.py
        result = {
            "dead_code": self._find_dead_code(),
            "complexity": self._analyze_complexity(),
            "maintainability": self._analyze_maintainability(),
            "style_issues": self._analyze_style_issues()
        }
        return result
    
    def _find_dead_code(self) -> Dict[str, Any]:
        """Find unused code in the codebase."""
        # This is a placeholder
        return {"unused_functions": [], "unused_classes": [], "unused_variables": []}
    
    def _analyze_complexity(self) -> Dict[str, Any]:
        """Analyze code complexity."""
        # This is a placeholder
        return {"complex_functions": [], "average_complexity": 0}
    
    def _analyze_maintainability(self) -> Dict[str, Any]:
        """Analyze code maintainability."""
        # This is a placeholder
        return {"maintainability_index": {}}
    
    def _analyze_style_issues(self) -> Dict[str, Any]:
        """Analyze code style issues."""
        # This is a placeholder
        return {"style_violations": []}

class DependencyPlugin(AnalyzerPlugin):
    """Plugin for dependency analysis."""

    def analyze(self) -> Dict[str, Any]:
        """Perform dependency analysis using the DependencyAnalyzer."""
        from codegen_on_oss.analyzers.dependencies import DependencyAnalyzer
        from codegen_on_oss.analyzers.codebase_context import CodebaseContext

        # Create context if needed
        context = getattr(self.manager, 'base_context', None)
        if not context and hasattr(self.manager, 'base_codebase'):
            try:
                context = CodebaseContext(
                    codebase=self.manager.base_codebase,
                    base_path=self.manager.repo_path,
                    pr_branch=None,
                    base_branch=self.manager.base_branch
                )
                # Save context for future use
                self.manager.base_context = context
            except Exception as e:
                logger.error(f"Error initializing context: {e}")

        # Initialize and run the dependency analyzer
        if context:
            dependency_analyzer = DependencyAnalyzer(
                codebase=self.manager.base_codebase,
                context=context
            )

            # Run analysis
            result = dependency_analyzer.analyze().to_dict()

            # Add issues to the manager
            for issue in dependency_analyzer.issues.issues:
                self.add_issue(issue)

            return result
        else:
            # Fallback to simple analysis if context initialization failed
            result = {
                "import_dependencies": self._analyze_imports(),
                "circular_dependencies": self._find_circular_dependencies(),
                "module_coupling": self._analyze_module_coupling()
            }
            return result

    def _analyze_imports(self) -> Dict[str, Any]:
        """Fallback import analysis if context initialization failed."""
        return {"module_dependencies": [], "external_dependencies": []}

    def _find_circular_dependencies(self) -> Dict[str, Any]:
        """Fallback circular dependencies analysis if context initialization failed."""
        return {"circular_imports": []}

    def _analyze_module_coupling(self) -> Dict[str, Any]:
        """Fallback module coupling analysis if context initialization failed."""
        return {"high_coupling_modules": []}

class AnalyzerManager:
    """
    Unified manager for codebase analysis.
    
    This class serves as the main entry point for all analysis operations,
    coordinating different analyzer plugins and managing results.
    """
    
    def __init__(
        self,
        repo_url: Optional[str] = None,
        repo_path: Optional[str] = None,
        base_branch: str = "main",
        pr_number: Optional[int] = None,
        language: Optional[str] = None,
        file_ignore_list: Optional[List[str]] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the analyzer manager.
        
        Args:
            repo_url: URL of the repository to analyze
            repo_path: Local path to the repository to analyze
            base_branch: Base branch for comparison
            pr_number: PR number to analyze
            language: Programming language of the codebase
            file_ignore_list: List of file patterns to ignore
            config: Additional configuration options
        """
        self.repo_url = repo_url
        self.repo_path = repo_path
        self.base_branch = base_branch
        self.pr_number = pr_number
        self.language = language
        
        # Use custom ignore list or default global list
        self.file_ignore_list = file_ignore_list or GLOBAL_FILE_IGNORE_LIST
        
        # Configuration options
        self.config = config or {}
        
        # Codebase and context objects
        self.base_codebase = None
        self.pr_codebase = None
        
        # Analysis results
        self.issues = []
        self.results = {}
        
        # PR comparison data
        self.pr_diff = None
        self.commit_shas = None
        self.modified_symbols = None
        self.pr_branch = None
        
        # Initialize codebase(s) based on provided parameters
        if repo_url:
            self._init_from_url(repo_url, language)
        elif repo_path:
            self._init_from_path(repo_path, language)
        
        # If PR number is provided, initialize PR-specific data
        if self.pr_number is not None and self.base_codebase is not None:
            self._init_pr_data(self.pr_number)
        
        # Register default analyzers
        self._register_default_analyzers()
    
    def _init_from_url(self, repo_url: str, language: Optional[str] = None):
        """Initialize codebase from a repository URL."""
        try:
            # Extract repository information
            if repo_url.endswith('.git'):
                repo_url = repo_url[:-4]
            
            parts = repo_url.rstrip('/').split('/')
            repo_name = parts[-1]
            owner = parts[-2]
            repo_full_name = f"{owner}/{repo_name}"
            
            # Create temporary directory for cloning
            import tempfile
            tmp_dir = tempfile.mkdtemp(prefix="analyzer_")
            
            # Set up configuration
            config = CodebaseConfig(
                debug=False,
                allow_external=True,
                py_resolve_syspath=True,
            )
            
            secrets = SecretsConfig()
            
            # Determine programming language
            prog_lang = None
            if language:
                prog_lang = ProgrammingLanguage(language.upper())
            
            # Initialize the codebase
            logger.info(f"Initializing codebase from {repo_url}")
            
            self.base_codebase = Codebase.from_github(
                repo_full_name=repo_full_name,
                tmp_dir=tmp_dir,
                language=prog_lang,
                config=config,
                secrets=secrets
            )
            
            logger.info(f"Successfully initialized codebase from {repo_url}")
            
        except Exception as e:
            logger.error(f"Error initializing codebase from URL: {e}")
            raise
    
    def _init_from_path(self, repo_path: str, language: Optional[str] = None):
        """Initialize codebase from a local repository path."""
        try:
            # Set up configuration
            config = CodebaseConfig(
                debug=False,
                allow_external=True,
                py_resolve_syspath=True,
            )
            
            secrets = SecretsConfig()
            
            # Initialize the codebase
            logger.info(f"Initializing codebase from {repo_path}")
            
            # Determine programming language
            prog_lang = None
            if language:
                prog_lang = ProgrammingLanguage(language.upper())
            
            # Set up repository configuration
            repo_config = RepoConfig.from_repo_path(repo_path)
            repo_config.respect_gitignore = False
            repo_operator = RepoOperator(repo_config=repo_config, bot_commit=False)
            
            # Create project configuration
            project_config = ProjectConfig(
                repo_operator=repo_operator,
                programming_language=prog_lang if prog_lang else None
            )
            
            # Initialize codebase
            self.base_codebase = Codebase(
                projects=[project_config],
                config=config,
                secrets=secrets
            )
            
            logger.info(f"Successfully initialized codebase from {repo_path}")
            
        except Exception as e:
            logger.error(f"Error initializing codebase from path: {e}")
            raise
    
    def _init_pr_data(self, pr_number: int):
        """Initialize PR-specific data."""
        try:
            logger.info(f"Fetching PR #{pr_number} data")
            result = self.base_codebase.get_modified_symbols_in_pr(pr_number)
            
            # Unpack the result tuple
            if len(result) >= 3:
                self.pr_diff, self.commit_shas, self.modified_symbols = result[:3]
                if len(result) >= 4:
                    self.pr_branch = result[3]
                
            logger.info(f"Found {len(self.modified_symbols)} modified symbols in PR")
            
            # Initialize PR codebase
            self._init_pr_codebase()
            
        except Exception as e:
            logger.error(f"Error initializing PR data: {e}")
            raise
    
    def _init_pr_codebase(self):
        """Initialize PR codebase by checking out the PR branch."""
        if not self.base_codebase or not self.pr_number:
            logger.error("Base codebase or PR number not initialized")
            return
            
        try:
            # Get PR data if not already fetched
            if not self.pr_branch:
                self._init_pr_data(self.pr_number)
                
            if not self.pr_branch:
                logger.error("Failed to get PR branch")
                return
                
            # Clone the base codebase
            self.pr_codebase = self.base_codebase
                
            # Checkout PR branch
            logger.info(f"Checking out PR branch: {self.pr_branch}")
            self.pr_codebase.checkout(self.pr_branch)
            
            logger.info("Successfully initialized PR codebase")
                
        except Exception as e:
            logger.error(f"Error initializing PR codebase: {e}")
            raise
    
    def _register_default_analyzers(self):
        """Register default analyzers."""
        registry = AnalyzerRegistry()
        registry.register(AnalysisType.CODE_QUALITY, CodeQualityPlugin)
        registry.register(AnalysisType.DEPENDENCY, DependencyPlugin)
    
    def add_issue(self, issue: Issue):
        """Add an issue to the list."""
        # Check if issue should be skipped
        if self._should_skip_issue(issue):
            return
            
        self.issues.append(issue)
    
    def _should_skip_issue(self, issue: Issue) -> bool:
        """Check if an issue should be skipped."""
        # Skip issues in ignored files
        file_path = issue.file
        
        # Check against ignore list
        for pattern in self.file_ignore_list:
            if pattern in file_path:
                return True
        
        # Check if the file is a test file
        if "test" in file_path.lower() or "tests" in file_path.lower():
            # Skip low-severity issues in test files
            if issue.severity in [IssueSeverity.INFO, IssueSeverity.WARNING]:
                return True
        
        return False
    
    def get_issues(self, severity: Optional[IssueSeverity] = None, category: Optional[IssueCategory] = None) -> List[Issue]:
        """
        Get all issues matching the specified criteria.
        
        Args:
            severity: Optional severity level to filter by
            category: Optional category to filter by
            
        Returns:
            List of matching issues
        """
        filtered_issues = self.issues
        
        if severity:
            filtered_issues = [i for i in filtered_issues if i.severity == severity]
        
        if category:
            filtered_issues = [i for i in filtered_issues if i.category == category]
        
        return filtered_issues
    
    def analyze(
        self, 
        analysis_types: Optional[List[Union[AnalysisType, str]]] = None,
        output_file: Optional[str] = None,
        output_format: str = "json"
    ) -> Dict[str, Any]:
        """
        Perform analysis on the codebase.
        
        Args:
            analysis_types: List of analysis types to perform
            output_file: Path to save results to
            output_format: Format of the output file
            
        Returns:
            Dictionary containing analysis results
        """
        if not self.base_codebase:
            raise ValueError("Codebase not initialized")
            
        # Convert string analysis types to enums
        if analysis_types:
            analysis_types = [
                at if isinstance(at, AnalysisType) else AnalysisType(at)
                for at in analysis_types
            ]
        else:
            # Default to code quality and dependency analysis
            analysis_types = [AnalysisType.CODE_QUALITY, AnalysisType.DEPENDENCY]
            
        # Initialize results
        self.results = {
            "metadata": {
                "analysis_time": datetime.now().isoformat(),
                "analysis_types": [t.value for t in analysis_types],
                "repo_name": getattr(self.base_codebase.ctx, 'repo_name', None),
                "language": str(getattr(self.base_codebase.ctx, 'programming_language', None)),
            },
            "summary": {},
            "results": {}
        }
        
        # Reset issues
        self.issues = []
        
        # Run each analyzer
        registry = AnalyzerRegistry()
        
        for analysis_type in analysis_types:
            analyzer_class = registry.get_analyzer(analysis_type)
            
            if analyzer_class:
                logger.info(f"Running {analysis_type.value} analysis")
                analyzer = analyzer_class(self)
                analysis_result = analyzer.analyze()
                
                # Add results to unified results
                self.results["results"][analysis_type.value] = analysis_result
            else:
                logger.warning(f"No analyzer found for {analysis_type.value}")
        
        # Add issues to results
        self.results["issues"] = [issue.to_dict() for issue in self.issues]
        
        # Add issue statistics
        self.results["issue_stats"] = {
            "total": len(self.issues),
            "by_severity": {
                "critical": sum(1 for issue in self.issues if issue.severity == IssueSeverity.CRITICAL),
                "error": sum(1 for issue in self.issues if issue.severity == IssueSeverity.ERROR),
                "warning": sum(1 for issue in self.issues if issue.severity == IssueSeverity.WARNING),
                "info": sum(1 for issue in self.issues if issue.severity == IssueSeverity.INFO),
            }
        }
        
        # Save results if output file is specified
        if output_file:
            self.save_results(output_file, output_format)
        
        return self.results
    
    def save_results(self, output_file: str, format: str = "json"):
        """
        Save analysis results to a file.
        
        Args:
            output_file: Path to the output file
            format: Output format (json, html)
        """
        if format == "json":
            with open(output_file, 'w') as f:
                json.dump(self.results, f, indent=2)
        elif format == "html":
            self._generate_html_report(output_file)
        else:
            # Default to JSON
            with open(output_file, 'w') as f:
                json.dump(self.results, f, indent=2)
                
        logger.info(f"Results saved to {output_file}")
    
    def _generate_html_report(self, output_file: str):
        """Generate an HTML report of the analysis results."""
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Codebase Analysis Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1, h2, h3 {{ color: #333; }}
                .error {{ color: red; }}
                .warning {{ color: orange; }}
                .info {{ color: blue; }}
                .section {{ margin-bottom: 30px; }}
                pre {{ background-color: #f5f5f5; padding: 10px; border-radius: 5px; overflow-x: auto; }}
                .issue {{ margin-bottom: 10px; padding: 10px; border-radius: 5px; }}
                .critical {{ background-color: #ffcdd2; }}
                .error {{ background-color: #ffebee; }}
                .warning {{ background-color: #fff8e1; }}
                .info {{ background-color: #e8f5e9; }}
            </style>
        </head>
        <body>
            <h1>Codebase Analysis Report</h1>
            <div class="section">
                <h2>Summary</h2>
                <p>Repository: {self.results['metadata'].get('repo_name', 'Unknown')}</p>
                <p>Language: {self.results['metadata'].get('language', 'Unknown')}</p>
                <p>Analysis Time: {self.results['metadata'].get('analysis_time', 'Unknown')}</p>
                <p>Analysis Types: {', '.join(self.results['metadata'].get('analysis_types', []))}</p>
                <p>Total Issues: {len(self.issues)}</p>
                <ul>
                    <li class="critical">Critical: {self.results['issue_stats']['by_severity'].get('critical', 0)}</li>
                    <li class="error">Errors: {self.results['issue_stats']['by_severity'].get('error', 0)}</li>
                    <li class="warning">Warnings: {self.results['issue_stats']['by_severity'].get('warning', 0)}</li>
                    <li class="info">Info: {self.results['issue_stats']['by_severity'].get('info', 0)}</li>
                </ul>
            </div>
        """
        
        # Add issues section
        html_content += """
            <div class="section">
                <h2>Issues</h2>
        """
        
        # Add issues by severity
        for severity in ["critical", "error", "warning", "info"]:
            severity_issues = [issue for issue in self.issues if issue.severity.value == severity]
            
            if severity_issues:
                html_content += f"""
                <h3>{severity.upper()} Issues ({len(severity_issues)})</h3>
                <div class="issues">
                """
                
                for issue in severity_issues:
                    location = f"{issue.file}:{issue.line}" if issue.line else issue.file
                    category = f"[{issue.category.value}]" if hasattr(issue, 'category') and issue.category else ""
                    
                    html_content += f"""
                    <div class="issue {severity}">
                        <p><strong>{location}</strong> {category} {issue.message}</p>
                        <p>{issue.suggestion if hasattr(issue, 'suggestion') else ""}</p>
                    </div>
                    """
                
                html_content += """
                </div>
                """
        
        # Add detailed analysis sections
        html_content += """
            <div class="section">
                <h2>Detailed Analysis</h2>
        """
        
        for analysis_type, results in self.results.get('results', {}).items():
            html_content += f"""
            <h3>{analysis_type}</h3>
            <pre>{json.dumps(results, indent=2)}</pre>
            """
        
        html_content += """
            </div>
        </body>
        </html>
        """
        
        with open(output_file, 'w') as f:
            f.write(html_content)
    
    def generate_report(self, report_type: str = "summary") -> str:
        """
        Generate a report from the analysis results.
        
        Args:
            report_type: Type of report to generate (summary, detailed, issues)
            
        Returns:
            Report as a string
        """
        if not self.results:
            raise ValueError("No analysis results available")
        
        if report_type == "summary":
            return self._generate_summary_report()
        elif report_type == "detailed":
            return self._generate_detailed_report()
        elif report_type == "issues":
            return self._generate_issues_report()
        else:
            raise ValueError(f"Unknown report type: {report_type}")
    
    def _generate_summary_report(self) -> str:
        """Generate a summary report."""
        report = "===== Codebase Analysis Summary Report =====\n\n"
        
        # Add metadata
        report += f"Repository: {self.results['metadata'].get('repo_name', 'Unknown')}\n"
        report += f"Language: {self.results['metadata'].get('language', 'Unknown')}\n"
        report += f"Analysis Time: {self.results['metadata'].get('analysis_time', 'Unknown')}\n"
        report += f"Analysis Types: {', '.join(self.results['metadata'].get('analysis_types', []))}\n\n"
        
        # Add issue statistics
        report += f"Total Issues: {len(self.issues)}\n"
        report += f"Critical: {self.results['issue_stats']['by_severity'].get('critical', 0)}\n"
        report += f"Errors: {self.results['issue_stats']['by_severity'].get('error', 0)}\n"
        report += f"Warnings: {self.results['issue_stats']['by_severity'].get('warning', 0)}\n"
        report += f"Info: {self.results['issue_stats']['by_severity'].get('info', 0)}\n\n"
        
        # Add analysis summaries
        for analysis_type, results in self.results.get('results', {}).items():
            report += f"===== {analysis_type.upper()} Analysis =====\n"
            
            if analysis_type == "code_quality":
                if "dead_code" in results:
                    dead_code = results["dead_code"]
                    report += f"Dead Code: {len(dead_code.get('unused_functions', []))} unused functions, "
                    report += f"{len(dead_code.get('unused_classes', []))} unused classes\n"
                
                if "complexity" in results:
                    complexity = results["complexity"]
                    report += f"Complexity: {len(complexity.get('complex_functions', []))} complex functions\n"
            
            elif analysis_type == "dependency":
                if "circular_dependencies" in results:
                    circular = results["circular_dependencies"]
                    report += f"Circular Dependencies: {len(circular.get('circular_imports', []))}\n"
                
                if "module_coupling" in results:
                    coupling = results["module_coupling"]
                    report += f"High Coupling Modules: {len(coupling.get('high_coupling_modules', []))}\n"
            
            report += "\n"
        
        return report
    
    def _generate_detailed_report(self) -> str:
        """Generate a detailed report."""
        report = "===== Codebase Analysis Detailed Report =====\n\n"
        
        # Add metadata
        report += f"Repository: {self.results['metadata'].get('repo_name', 'Unknown')}\n"
        report += f"Language: {self.results['metadata'].get('language', 'Unknown')}\n"
        report += f"Analysis Time: {self.results['metadata'].get('analysis_time', 'Unknown')}\n"
        report += f"Analysis Types: {', '.join(self.results['metadata'].get('analysis_types', []))}\n\n"
        
        # Add detailed issue report
        report += "===== Issues =====\n\n"
        
        for severity in ["critical", "error", "warning", "info"]:
            severity_issues = [issue for issue in self.issues if issue.severity.value == severity]
            
            if severity_issues:
                report += f"{severity.upper()} Issues ({len(severity_issues)}):\n"
                
                for issue in severity_issues:
                    location = f"{issue.file}:{issue.line}" if issue.line else issue.file
                    category = f"[{issue.category.value}]" if hasattr(issue, 'category') and issue.category else ""
                    
                    report += f"- {location} {category} {issue.message}\n"
                    if hasattr(issue, 'suggestion') and issue.suggestion:
                        report += f"  Suggestion: {issue.suggestion}\n"
                
                report += "\n"
        
        # Add detailed analysis
        for analysis_type, results in self.results.get('results', {}).items():
            report += f"===== {analysis_type.upper()} Analysis =====\n\n"
            
            # Format based on analysis type
            if analysis_type == "code_quality":
                # Dead code details
                if "dead_code" in results:
                    dead_code = results["dead_code"]
                    report += "Dead Code:\n"
                    
                    if dead_code.get('unused_functions'):
                        report += "  Unused Functions:\n"
                        for func in dead_code.get('unused_functions', [])[:10]:  # Limit to 10
                            report += f"  - {func.get('name')} ({func.get('file')})\n"
                        
                        if len(dead_code.get('unused_functions', [])) > 10:
                            report += f"    ... and {len(dead_code.get('unused_functions', [])) - 10} more\n"
                    
                    if dead_code.get('unused_classes'):
                        report += "  Unused Classes:\n"
                        for cls in dead_code.get('unused_classes', [])[:10]:  # Limit to 10
                            report += f"  - {cls.get('name')} ({cls.get('file')})\n"
                        
                        if len(dead_code.get('unused_classes', [])) > 10:
                            report += f"    ... and {len(dead_code.get('unused_classes', [])) - 10} more\n"
                    
                    report += "\n"
                
                # Complexity details
                if "complexity" in results:
                    complexity = results["complexity"]
                    report += "Code Complexity:\n"
                    
                    if complexity.get('complex_functions'):
                        report += "  Complex Functions:\n"
                        for func in complexity.get('complex_functions', [])[:10]:  # Limit to 10
                            report += f"  - {func.get('name')} (Complexity: {func.get('complexity')}, {func.get('file')})\n"
                        
                        if len(complexity.get('complex_functions', [])) > 10:
                            report += f"    ... and {len(complexity.get('complex_functions', [])) - 10} more\n"
                    
                    report += "\n"
            
            elif analysis_type == "dependency":
                # Circular dependencies
                if "circular_dependencies" in results:
                    circular = results["circular_dependencies"]
                    report += "Circular Dependencies:\n"
                    
                    if circular.get('circular_imports'):
                        for i, cycle in enumerate(circular.get('circular_imports', [])[:5]):  # Limit to 5
                            report += f"  Cycle {i+1} (Length: {cycle.get('length')}):\n"
                            for j, file_path in enumerate(cycle.get('files', [])):
                                report += f"    {j+1}. {file_path}\n"
                        
                        if len(circular.get('circular_imports', [])) > 5:
                            report += f"    ... and {len(circular.get('circular_imports', [])) - 5} more cycles\n"
                    
                    report += "\n"
                
                # Module coupling
                if "module_coupling" in results:
                    coupling = results["module_coupling"]
                    report += "Module Coupling:\n"
                    
                    if coupling.get('high_coupling_modules'):
                        report += "  High Coupling Modules:\n"
                        for module in coupling.get('high_coupling_modules', [])[:10]:  # Limit to 10
                            report += f"  - {module.get('module')} (Ratio: {module.get('coupling_ratio'):.2f})\n"
                        
                        if len(coupling.get('high_coupling_modules', [])) > 10:
                            report += f"    ... and {len(coupling.get('high_coupling_modules', [])) - 10} more\n"
                    
                    report += "\n"
        
        return report
    
    def _generate_issues_report(self) -> str:
        """Generate an issues-focused report."""
        report = "===== Codebase Analysis Issues Report =====\n\n"
        
        # Add issue statistics
        report += f"Total Issues: {len(self.issues)}\n"
        report += f"Critical: {self.results['issue_stats']['by_severity'].get('critical', 0)}\n"
        report += f"Errors: {self.results['issue_stats']['by_severity'].get('error', 0)}\n"
        report += f"Warnings: {self.results['issue_stats']['by_severity'].get('warning', 0)}\n"
        report += f"Info: {self.results['issue_stats']['by_severity'].get('info', 0)}\n\n"
        
        # Add issues by severity
        for severity in ["critical", "error", "warning", "info"]:
            severity_issues = [issue for issue in self.issues if issue.severity.value == severity]
            
            if severity_issues:
                report += f"{severity.upper()} Issues ({len(severity_issues)}):\n"
                
                for issue in severity_issues:
                    location = f"{issue.file}:{issue.line}" if issue.line else issue.file
                    category = f"[{issue.category.value}]" if hasattr(issue, 'category') and issue.category else ""
                    
                    report += f"- {location} {category} {issue.message}\n"
                    if hasattr(issue, 'suggestion') and issue.suggestion:
                        report += f"  Suggestion: {issue.suggestion}\n"
                
                report += "\n"
        
        return report

def main():
    """Command-line entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Unified Codebase Analyzer")
    
    # Repository source options
    source_group = parser.add_mutually_exclusive_group(required=True)
    source_group.add_argument("--repo-url", help="URL of the repository to analyze")
    source_group.add_argument("--repo-path", help="Local path to the repository to analyze")
    
    # Analysis options
    parser.add_argument("--analysis-types", nargs="+", choices=[at.value for at in AnalysisType], 
                        default=["code_quality", "dependency"],
                        help="Types of analysis to perform")
    parser.add_argument("--language", choices=["python", "typescript"], 
                        help="Programming language (auto-detected if not provided)")
    parser.add_argument("--base-branch", default="main", 
                        help="Base branch for PR comparison (default: main)")
    parser.add_argument("--pr-number", type=int, 
                        help="PR number to analyze")
    
    # Output options
    parser.add_argument("--output-file", 
                        help="Path to the output file")
    parser.add_argument("--output-format", choices=["json", "html", "console"], default="json", 
                        help="Output format")
    parser.add_argument("--report-type", choices=["summary", "detailed", "issues"], default="summary",
                        help="Type of report to generate (default: summary)")
    
    args = parser.parse_args()
    
    try:
        # Initialize the analyzer manager
        manager = AnalyzerManager(
            repo_url=args.repo_url,
            repo_path=args.repo_path,
            language=args.language,
            base_branch=args.base_branch,
            pr_number=args.pr_number
        )
        
        # Run the analysis
        manager.analyze(
            analysis_types=args.analysis_types,
            output_file=args.output_file,
            output_format=args.output_format
        )
        
        # Generate and print report if format is console
        if args.output_format == "console":
            report = manager.generate_report(args.report_type)
            print(report)
            
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()