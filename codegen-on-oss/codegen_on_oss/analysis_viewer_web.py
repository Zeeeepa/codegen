#!/usr/bin/env python3
"""
Web interface for the codebase analysis viewer.
"""

import os
import sys
import json
import tempfile
import argparse
import webbrowser
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Tuple

try:
    import gradio as gr
except ImportError:
    print("Gradio not found. Please install it with 'pip install gradio'.")
    sys.exit(1)

try:
    from .codebase_analyzer import CodebaseAnalyzer
    from .codebase_comparator import CodebaseComparator
except ImportError:
    try:
        from codebase_analyzer import CodebaseAnalyzer
        from codebase_comparator import CodebaseComparator
    except ImportError:
        print(
            "Codebase analysis modules not found. "
            "Please ensure they're in the same directory."
        )
        sys.exit(1)


class AnalysisViewerWeb:
    """
    Web interface for the codebase analysis viewer.
    
    This class provides a web-based interface for analyzing and comparing codebases
    using Gradio.
    """
    
    def __init__(self):
        """Initialize the web interface."""
        self.analyzer = None
        self.comparator = None
        self.last_results = None
        self.temp_dir = tempfile.mkdtemp(prefix="codebase_analysis_")
    
    def analyze_repo(
        self,
        repo_source: str,
        repo_url: str,
        repo_path: str,
        language: str,
        categories: List[str],
        depth: int
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Analyze a repository.
        
        Args:
            repo_source: Source of the repository (url or local)
            repo_url: URL of the repository to analyze
            repo_path: Local path to the repository to analyze
            language: Programming language of the codebase
            categories: Categories to analyze
            depth: Depth of analysis
            
        Returns:
            Tuple containing the analysis report and results
        """
        try:
            # Initialize the analyzer
            if repo_source == "url":
                if not repo_url:
                    return "Please enter a repository URL.", None
                
                self.analyzer = CodebaseAnalyzer(
                    repo_url=repo_url,
                    language=language if language else None
                )
            else:  # local
                if not repo_path:
                    return "Please enter a repository path.", None
                
                self.analyzer = CodebaseAnalyzer(
                    repo_path=repo_path,
                    language=language if language else None
                )
            
            # Convert categories string to list
            categories_list = None
            if categories:
                categories_list = [cat.strip() for cat in categories.split(",")]
            
            # Perform the analysis
            self.last_results = self.analyzer.analyze(
                categories=categories_list,
                depth=depth
            )
            
            # Generate HTML report
            report_path = os.path.join(self.temp_dir, "analysis_report.html")
            self.analyzer._generate_html_report(report_path)
            
            with open(report_path, "r") as f:
                report_html = f.read()
            
            return report_html, self.last_results
        
        except Exception as e:
            import traceback
            error_msg = f"Error analyzing repository: {str(e)}\n\n{traceback.format_exc()}"
            return error_msg, None
    
    def compare_repos(
        self,
        base_source: str,
        base_url: str,
        base_path: str,
        compare_source: str,
        compare_url: str,
        compare_path: str,
        base_branch: str,
        compare_branch: str,
        language: str,
        categories: str,
        depth: int
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Compare two repositories.
        
        Args:
            base_source: Source of the base repository (url or local)
            base_url: URL of the base repository
            base_path: Local path to the base repository
            compare_source: Source of the compare repository (url or local)
            compare_url: URL of the compare repository
            compare_path: Local path to the compare repository
            base_branch: Branch of the base repository
            compare_branch: Branch of the compare repository
            language: Programming language of the codebases
            categories: Categories to compare
            depth: Depth of comparison
            
        Returns:
            Tuple containing the comparison report and results
        """
        try:
            # Initialize the comparator
            base_repo_url = base_url if base_source == "url" else None
            base_repo_path = base_path if base_source == "local" else None
            compare_repo_url = compare_url if compare_source == "url" else None
            compare_repo_path = compare_path if compare_source == "local" else None
            
            if not (base_repo_url or base_repo_path):
                return "Please specify a base repository.", None
            
            if not (compare_repo_url or compare_repo_path):
                return "Please specify a compare repository.", None
            
            self.comparator = CodebaseComparator(
                base_repo_url=base_repo_url,
                base_repo_path=base_repo_path,
                compare_repo_url=compare_repo_url,
                compare_repo_path=compare_repo_path,
                base_branch=base_branch if base_branch else None,
                compare_branch=compare_branch if compare_branch else None,
                language=language if language else None
            )
            
            # Convert categories string to list
            categories_list = None
            if categories:
                categories_list = [cat.strip() for cat in categories.split(",")]
            
            # Perform the comparison
            self.last_results = self.comparator.compare(
                categories=categories_list
            )
            
            # Generate HTML report
            report_path = os.path.join(self.temp_dir, "comparison_report.html")
            self.comparator._generate_html_report(self.last_results, report_path)
            
            with open(report_path, "r") as f:
                report_html = f.read()
            
            return report_html, self.last_results
        
        except Exception as e:
            import traceback
            error_msg = f"Error comparing repositories: {str(e)}\n\n{traceback.format_exc()}"
            return error_msg, None
    
    def save_results(self, results: Dict[str, Any], format: str, filename: str) -> str:
        """
        Save the analysis or comparison results.
        
        Args:
            results: Results to save
            format: Format of the output (json or html)
            filename: Name of the output file
            
        Returns:
            Path to the saved file
        """
        if not results:
            return "No results to save."
        
        if not filename:
            filename = "results"
        
        if not filename.endswith(f".{format}"):
            filename += f".{format}"
        
        try:
            if format == "json":
                with open(filename, "w") as f:
                    json.dump(results, f, indent=2)
            elif format == "html":
                if "metadata" in results and "repo_name" in results["metadata"]:
                    # Analysis results
                    if self.analyzer:
                        self.analyzer._generate_html_report(filename)
                    else:
                        return "Analyzer not initialized."
                elif "metadata" in results and "base_repo" in results["metadata"]:
                    # Comparison results
                    if self.comparator:
                        self.comparator._generate_html_report(results, filename)
                    else:
                        return "Comparator not initialized."
                else:
                    return "Unknown result format."
            
            return f"Results saved to {filename}"
        
        except Exception as e:
            return f"Error saving results: {str(e)}"
    
    def create_interface(self):
        """Create the Gradio interface."""
        with gr.Blocks(title="Codebase Analysis Viewer") as interface:
            gr.Markdown("# Codebase Analysis Viewer")
            gr.Markdown("Analyze and compare codebases with comprehensive static analysis.")
            
            with gr.Tabs():
                with gr.TabItem("Analyze"):
                    with gr.Row():
                        with gr.Column():
                            analyze_source = gr.Radio(
                                ["url", "local"],
                                label="Repository Source",
                                value="url"
                            )
                            analyze_repo_url = gr.Textbox(
                                label="Repository URL",
                                placeholder="https://github.com/username/repo.git"
                            )
                            analyze_repo_path = gr.Textbox(
                                label="Repository Path",
                                placeholder="/path/to/local/repo",
                                visible=False
                            )
                            
                            def toggle_analyze_source(source):
                                return {
                                    analyze_repo_url: gr.update(visible=source == "url"),
                                    analyze_repo_path: gr.update(visible=source == "local")
                                }
                            
                            analyze_source.change(
                                toggle_analyze_source,
                                inputs=[analyze_source],
                                outputs=[analyze_repo_url, analyze_repo_path]
                            )
                            
                            analyze_language = gr.Textbox(
                                label="Language (optional)",
                                placeholder="python, javascript, etc."
                            )
                            analyze_categories = gr.Textbox(
                                label="Categories (comma-separated, optional)",
                                placeholder="codebase_structure, code_quality, etc."
                            )
                            analyze_depth = gr.Slider(
                                minimum=1,
                                maximum=3,
                                value=2,
                                step=1,
                                label="Analysis Depth"
                            )
                            analyze_button = gr.Button("Analyze Repository")
                        
                        with gr.Column():
                            analyze_output = gr.HTML(label="Analysis Results")
                            analyze_json = gr.JSON(label="Raw Results", visible=False)
                            
                            with gr.Row():
                                save_format = gr.Radio(
                                    ["json", "html"],
                                    label="Save Format",
                                    value="html"
                                )
                                save_filename = gr.Textbox(
                                    label="Filename",
                                    placeholder="analysis_results"
                                )
                                save_button = gr.Button("Save Results")
                            
                            save_status = gr.Textbox(label="Save Status")
                    
                    analyze_button.click(
                        self.analyze_repo,
                        inputs=[
                            analyze_source,
                            analyze_repo_url,
                            analyze_repo_path,
                            analyze_language,
                            analyze_categories,
                            analyze_depth
                        ],
                        outputs=[analyze_output, analyze_json]
                    )
                    
                    save_button.click(
                        self.save_results,
                        inputs=[analyze_json, save_format, save_filename],
                        outputs=[save_status]
                    )
                
                with gr.TabItem("Compare"):
                    with gr.Row():
                        with gr.Column():
                            gr.Markdown("## Base Repository")
                            base_source = gr.Radio(
                                ["url", "local"],
                                label="Base Repository Source",
                                value="url"
                            )
                            base_url = gr.Textbox(
                                label="Base Repository URL",
                                placeholder="https://github.com/username/repo.git"
                            )
                            base_path = gr.Textbox(
                                label="Base Repository Path",
                                placeholder="/path/to/local/repo",
                                visible=False
                            )
                            
                            def toggle_base_source(source):
                                return {
                                    base_url: gr.update(visible=source == "url"),
                                    base_path: gr.update(visible=source == "local")
                                }
                            
                            base_source.change(
                                toggle_base_source,
                                inputs=[base_source],
                                outputs=[base_url, base_path]
                            )
                            
                            base_branch = gr.Textbox(
                                label="Base Branch (optional)",
                                placeholder="main, master, etc."
                            )
                        
                        with gr.Column():
                            gr.Markdown("## Compare Repository")
                            compare_source = gr.Radio(
                                ["url", "local"],
                                label="Compare Repository Source",
                                value="url"
                            )
                            compare_url = gr.Textbox(
                                label="Compare Repository URL",
                                placeholder="https://github.com/username/repo.git"
                            )
                            compare_path = gr.Textbox(
                                label="Compare Repository Path",
                                placeholder="/path/to/local/repo",
                                visible=False
                            )
                            
                            def toggle_compare_source(source):
                                return {
                                    compare_url: gr.update(visible=source == "url"),
                                    compare_path: gr.update(visible=source == "local")
                                }
                            
                            compare_source.change(
                                toggle_compare_source,
                                inputs=[compare_source],
                                outputs=[compare_url, compare_path]
                            )
                            
                            compare_branch = gr.Textbox(
                                label="Compare Branch (optional)",
                                placeholder="main, master, etc."
                            )
                    
                    with gr.Row():
                        with gr.Column():
                            compare_language = gr.Textbox(
                                label="Language (optional)",
                                placeholder="python, javascript, etc."
                            )
                            compare_categories = gr.Textbox(
                                label="Categories (comma-separated, optional)",
                                placeholder="codebase_structure, code_quality, etc."
                            )
                            compare_depth = gr.Slider(
                                minimum=1,
                                maximum=3,
                                value=2,
                                step=1,
                                label="Comparison Depth"
                            )
                            compare_button = gr.Button("Compare Repositories")
                    
                    with gr.Row():
                        compare_output = gr.HTML(label="Comparison Results")
                        compare_json = gr.JSON(label="Raw Results", visible=False)
                    
                    with gr.Row():
                        compare_save_format = gr.Radio(
                            ["json", "html"],
                            label="Save Format",
                            value="html"
                        )
                        compare_save_filename = gr.Textbox(
                            label="Filename",
                            placeholder="comparison_results"
                        )
                        compare_save_button = gr.Button("Save Results")
                    
                    compare_save_status = gr.Textbox(label="Save Status")
                    
                    compare_button.click(
                        self.compare_repos,
                        inputs=[
                            base_source,
                            base_url,
                            base_path,
                            compare_source,
                            compare_url,
                            compare_path,
                            base_branch,
                            compare_branch,
                            compare_language,
                            compare_categories,
                            compare_depth
                        ],
                        outputs=[compare_output, compare_json]
                    )
                    
                    compare_save_button.click(
                        self.save_results,
                        inputs=[compare_json, compare_save_format, compare_save_filename],
                        outputs=[compare_save_status]
                    )
                
                with gr.TabItem("Help"):
                    gr.Markdown("""
                    # Codebase Analysis Viewer Help
                    
                    This tool allows you to analyze and compare codebases with comprehensive static analysis.
                    
                    ## Analyze Tab
                    
                    Use this tab to analyze a single codebase. You can specify:
                    
                    - **Repository Source**: URL or local path
                    - **Language**: Programming language of the codebase (auto-detected if not provided)
                    - **Categories**: Specific categories to analyze (comma-separated)
                    - **Analysis Depth**: Level of detail for the analysis (1-3)
                    
                    ## Compare Tab
                    
                    Use this tab to compare two codebases. You can specify:
                    
                    - **Base Repository**: The first repository to compare
                    - **Compare Repository**: The second repository to compare against the base
                    - **Branches**: Specific branches to compare
                    - **Language**: Programming language of the codebases (auto-detected if not provided)
                    - **Categories**: Specific categories to compare (comma-separated)
                    - **Comparison Depth**: Level of detail for the comparison (1-3)
                    
                    ## Analysis Categories
                    
                    The following categories are available for analysis and comparison:
                    
                    - **codebase_structure**: File counts, language distribution, directory structure, etc.
                    - **symbol_level**: Function parameters, return types, complexity metrics, etc.
                    - **dependency_flow**: Function call relationships, entry point analysis, etc.
                    - **code_quality**: Unused functions, repeated code patterns, refactoring opportunities, etc.
                    - **visualization**: Module dependencies, symbol dependencies, call hierarchies, etc.
                    - **language_specific**: Decorator usage, type hint coverage, etc.
                    - **code_metrics**: Cyclomatic complexity, Halstead volume, maintainability index, etc.
                    
                    ## Saving Results
                    
                    You can save the analysis or comparison results in JSON or HTML format.
                    """)
        
        return interface
    
    def launch(self, port=7860, host="127.0.0.1", share=False, open_browser=True):
        """
        Launch the web interface.
        
        Args:
            port: Port to run the web interface on
            host: Host to run the web interface on
            share: Whether to create a shareable link
            open_browser: Whether to open the browser automatically
        """
        interface = self.create_interface()
        
        if open_browser:
            # Open the browser after a short delay
            def open_browser_tab():
                webbrowser.open(f"http://{host}:{port}")
            
            import threading
            import time
            threading.Timer(1.5, open_browser_tab).start()
        
        interface.launch(
            server_name=host,
            server_port=port,
            share=share,
            inbrowser=False  # We handle browser opening ourselves
        )


def main():
    """Main entry point for the analysis viewer web interface."""
    parser = argparse.ArgumentParser(description="Codebase Analysis Viewer Web Interface")
    parser.add_argument("--port", type=int, default=7860, help="Port to run the web interface on")
    parser.add_argument("--host", default="127.0.0.1", help="Host to run the web interface on")
    parser.add_argument("--share", action="store_true", help="Create a shareable link")
    parser.add_argument("--no-browser", action="store_true", help="Don't open the browser automatically")
    
    args = parser.parse_args()
    
    viewer = AnalysisViewerWeb()
    viewer.launch(
        port=args.port,
        host=args.host,
        share=args.share,
        open_browser=not args.no_browser
    )


if __name__ == "__main__":
    main()
