#!/usr/bin/env python3
"""
Codebase Analysis Viewer Web Interface

This module provides a web interface for the codebase analysis viewer,
allowing users to analyze single codebases or compare multiple codebases
through a browser-based UI.
"""

import os
import sys
import json
import logging
import tempfile
from typing import Dict, List, Any, Optional
from pathlib import Path
import threading
import webbrowser
from datetime import datetime

import gradio as gr

try:
    from codegen_on_oss.codebase_analyzer import CodebaseAnalyzer, METRICS_CATEGORIES
    from codegen_on_oss.codebase_comparator import CodebaseComparator
except ImportError:
    print("Codebase analysis modules not found. Please ensure they're in the same directory.")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

class CodebaseAnalysisViewerWeb:
    """
    Web interface for the codebase analysis viewer.
    
    This class provides a browser-based interface for analyzing single codebases
    or comparing multiple codebases using Gradio.
    """
    
    def __init__(self):
        """Initialize the web interface."""
        self.results_dir = Path("results")
        self.results_dir.mkdir(exist_ok=True)
        
        # Create the Gradio interface
        self._create_interface()
    
    def _create_interface(self):
        """Create the Gradio interface."""
        with gr.Blocks(title="Codebase Analysis Viewer") as self.interface:
            gr.Markdown("# Codebase Analysis Viewer")
            gr.Markdown("Analyze and compare codebases with powerful static analysis tools.")
            
            with gr.Tabs():
                with gr.TabItem("Single Codebase Analysis"):
                    self._create_single_analysis_tab()
                
                with gr.TabItem("Codebase Comparison"):
                    self._create_comparison_tab()
                
                with gr.TabItem("View Results"):
                    self._create_results_tab()
    
    def _create_single_analysis_tab(self):
        """Create the single codebase analysis tab."""
        with gr.Row():
            with gr.Column():
                repo_source = gr.Radio(
                    ["Repository URL", "Local Repository Path"],
                    label="Repository Source",
                    value="Repository URL"
                )
                
                repo_url = gr.Textbox(
                    label="Repository URL",
                    placeholder="https://github.com/username/repo"
                )
                
                repo_path = gr.Textbox(
                    label="Local Repository Path",
                    placeholder="/path/to/local/repo",
                    visible=False
                )
                
                language = gr.Dropdown(
                    ["Auto-detect", "Python", "TypeScript", "JavaScript", "Java", "Go", "Rust", "C++", "C#"],
                    label="Programming Language",
                    value="Auto-detect"
                )
                
                categories = gr.CheckboxGroup(
                    list(METRICS_CATEGORIES.keys()),
                    label="Categories to Analyze",
                    value=list(METRICS_CATEGORIES.keys())
                )
                
                output_format = gr.Radio(
                    ["HTML", "JSON"],
                    label="Output Format",
                    value="HTML"
                )
                
                analyze_button = gr.Button("Analyze Codebase", variant="primary")
            
            with gr.Column():
                analysis_output = gr.Textbox(
                    label="Analysis Status",
                    placeholder="Analysis results will appear here...",
                    lines=20
                )
                
                result_file = gr.File(label="Analysis Result File")
        
        # Handle repository source change
        def update_repo_input(source):
            if source == "Repository URL":
                return gr.update(visible=True), gr.update(visible=False)
            else:
                return gr.update(visible=False), gr.update(visible=True)
        
        repo_source.change(
            update_repo_input,
            inputs=[repo_source],
            outputs=[repo_url, repo_path]
        )
        
        # Handle analyze button click
        def analyze_codebase(repo_source, repo_url, repo_path, language, categories, output_format):
            try:
                # Prepare parameters
                repo_url_param = repo_url if repo_source == "Repository URL" else None
                repo_path_param = repo_path if repo_source == "Local Repository Path" else None
                language_param = None if language == "Auto-detect" else language.lower()
                
                # Initialize the analyzer
                analyzer = CodebaseAnalyzer(
                    repo_url=repo_url_param,
                    repo_path=repo_path_param,
                    language=language_param
                )
                
                # Generate a unique filename for the results
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                repo_name = repo_url.split("/")[-1] if repo_url_param else Path(repo_path).name
                
                if output_format == "HTML":
                    output_file = self.results_dir / f"analysis_{repo_name}_{timestamp}.html"
                else:
                    output_file = self.results_dir / f"analysis_{repo_name}_{timestamp}.json"
                
                # Perform the analysis
                results = analyzer.analyze(
                    categories=categories,
                    output_format=output_format.lower(),
                    output_file=str(output_file)
                )
                
                return f"Analysis completed successfully!\nResults saved to: {output_file}", output_file
            
            except Exception as e:
                import traceback
                error_msg = f"Error: {str(e)}\n\n{traceback.format_exc()}"
                return error_msg, None
        
        analyze_button.click(
            analyze_codebase,
            inputs=[repo_source, repo_url, repo_path, language, categories, output_format],
            outputs=[analysis_output, result_file]
        )
    
    def _create_comparison_tab(self):
        """Create the codebase comparison tab."""
        with gr.Row():
            with gr.Column():
                gr.Markdown("### Base Repository")
                
                base_repo_source = gr.Radio(
                    ["Repository URL", "Local Repository Path"],
                    label="Base Repository Source",
                    value="Repository URL"
                )
                
                base_repo_url = gr.Textbox(
                    label="Base Repository URL",
                    placeholder="https://github.com/username/repo"
                )
                
                base_repo_path = gr.Textbox(
                    label="Base Repository Path",
                    placeholder="/path/to/local/repo",
                    visible=False
                )
                
                base_branch = gr.Textbox(
                    label="Base Branch (optional)",
                    placeholder="main"
                )
            
            with gr.Column():
                gr.Markdown("### Comparison Repository")
                
                compare_repo_source = gr.Radio(
                    ["Repository URL", "Local Repository Path", "Same Repository (Different Branch)"],
                    label="Comparison Repository Source",
                    value="Repository URL"
                )
                
                compare_repo_url = gr.Textbox(
                    label="Comparison Repository URL",
                    placeholder="https://github.com/username/repo"
                )
                
                compare_repo_path = gr.Textbox(
                    label="Comparison Repository Path",
                    placeholder="/path/to/local/repo",
                    visible=False
                )
                
                compare_branch = gr.Textbox(
                    label="Comparison Branch",
                    placeholder="feature-branch",
                    visible=False
                )
        
        with gr.Row():
            with gr.Column():
                language = gr.Dropdown(
                    ["Auto-detect", "Python", "TypeScript", "JavaScript", "Java", "Go", "Rust", "C++", "C#"],
                    label="Programming Language",
                    value="Auto-detect"
                )
                
                categories = gr.CheckboxGroup(
                    list(METRICS_CATEGORIES.keys()),
                    label="Categories to Analyze",
                    value=list(METRICS_CATEGORIES.keys())
                )
                
                output_format = gr.Radio(
                    ["HTML", "JSON"],
                    label="Output Format",
                    value="HTML"
                )
                
                compare_button = gr.Button("Compare Codebases", variant="primary")
            
            with gr.Column():
                comparison_output = gr.Textbox(
                    label="Comparison Status",
                    placeholder="Comparison results will appear here...",
                    lines=20
                )
                
                comparison_file = gr.File(label="Comparison Result File")
        
        # Handle repository source changes
        def update_base_repo_input(source):
            if source == "Repository URL":
                return gr.update(visible=True), gr.update(visible=False)
            else:
                return gr.update(visible=False), gr.update(visible=True)
        
        base_repo_source.change(
            update_base_repo_input,
            inputs=[base_repo_source],
            outputs=[base_repo_url, base_repo_path]
        )
        
        def update_compare_repo_input(source):
            if source == "Repository URL":
                return gr.update(visible=True), gr.update(visible=False), gr.update(visible=False)
            elif source == "Local Repository Path":
                return gr.update(visible=False), gr.update(visible=True), gr.update(visible=False)
            else:  # Same Repository (Different Branch)
                return gr.update(visible=False), gr.update(visible=False), gr.update(visible=True)
        
        compare_repo_source.change(
            update_compare_repo_input,
            inputs=[compare_repo_source],
            outputs=[compare_repo_url, compare_repo_path, compare_branch]
        )
        
        # Handle compare button click
        def compare_codebases(
            base_repo_source, base_repo_url, base_repo_path, base_branch,
            compare_repo_source, compare_repo_url, compare_repo_path, compare_branch,
            language, categories, output_format
        ):
            try:
                # Prepare parameters
                base_repo_url_param = base_repo_url if base_repo_source == "Repository URL" else None
                base_repo_path_param = base_repo_path if base_repo_source == "Local Repository Path" else None
                
                if compare_repo_source == "Same Repository (Different Branch)":
                    compare_repo_url_param = base_repo_url_param
                    compare_repo_path_param = base_repo_path_param
                else:
                    compare_repo_url_param = compare_repo_url if compare_repo_source == "Repository URL" else None
                    compare_repo_path_param = compare_repo_path if compare_repo_source == "Local Repository Path" else None
                
                language_param = None if language == "Auto-detect" else language.lower()
                
                # Initialize the comparator
                comparator = CodebaseComparator(
                    base_repo_url=base_repo_url_param,
                    base_repo_path=base_repo_path_param,
                    compare_repo_url=compare_repo_url_param,
                    compare_repo_path=compare_repo_path_param,
                    base_branch=base_branch if base_branch else None,
                    compare_branch=compare_branch if compare_branch else None,
                    language=language_param
                )
                
                # Generate a unique filename for the results
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                base_name = base_repo_url.split("/")[-1] if base_repo_url_param else Path(base_repo_path).name
                compare_name = compare_repo_url.split("/")[-1] if compare_repo_url_param else Path(compare_repo_path).name
                
                if compare_repo_source == "Same Repository (Different Branch)":
                    compare_name = f"{base_name}_{compare_branch}"
                
                if output_format == "HTML":
                    output_file = self.results_dir / f"comparison_{base_name}_vs_{compare_name}_{timestamp}.html"
                else:
                    output_file = self.results_dir / f"comparison_{base_name}_vs_{compare_name}_{timestamp}.json"
                
                # Perform the comparison
                results = comparator.compare(
                    categories=categories,
                    output_format=output_format.lower(),
                    output_file=str(output_file)
                )
                
                return f"Comparison completed successfully!\nResults saved to: {output_file}", output_file
            
            except Exception as e:
                import traceback
                error_msg = f"Error: {str(e)}\n\n{traceback.format_exc()}"
                return error_msg, None
        
        compare_button.click(
            compare_codebases,
            inputs=[
                base_repo_source, base_repo_url, base_repo_path, base_branch,
                compare_repo_source, compare_repo_url, compare_repo_path, compare_branch,
                language, categories, output_format
            ],
            outputs=[comparison_output, comparison_file]
        )
    
    def _create_results_tab(self):
        """Create the results viewing tab."""
        with gr.Row():
            with gr.Column():
                result_files = gr.Dropdown(
                    self._get_result_files(),
                    label="Select Result File",
                    interactive=True
                )
                
                refresh_button = gr.Button("Refresh Results")
                
                view_button = gr.Button("View Selected Result", variant="primary")
            
            with gr.Column():
                result_viewer = gr.HTML(label="Result Viewer")
        
        # Handle refresh button click
        def refresh_results():
            return gr.update(choices=self._get_result_files())
        
        refresh_button.click(
            refresh_results,
            inputs=[],
            outputs=[result_files]
        )
        
        # Handle view button click
        def view_result(result_file):
            if not result_file:
                return "<p>Please select a result file to view.</p>"
            
            file_path = self.results_dir / result_file
            
            if not file_path.exists():
                return f"<p>Error: File {file_path} not found.</p>"
            
            if file_path.suffix == ".html":
                with open(file_path, "r") as f:
                    return f.read()
            elif file_path.suffix == ".json":
                try:
                    with open(file_path, "r") as f:
                        data = json.load(f)
                    
                    # Convert JSON to HTML for display
                    html = "<h2>JSON Result</h2>"
                    html += "<pre style='max-height: 500px; overflow-y: auto;'>"
                    html += json.dumps(data, indent=2)
                    html += "</pre>"
                    
                    return html
                except Exception as e:
                    return f"<p>Error loading JSON: {str(e)}</p>"
            else:
                return f"<p>Unsupported file format: {file_path.suffix}</p>"
        
        view_button.click(
            view_result,
            inputs=[result_files],
            outputs=[result_viewer]
        )
    
    def _get_result_files(self):
        """Get a list of result files in the results directory."""
        if not self.results_dir.exists():
            return []
        
        return [f.name for f in self.results_dir.iterdir() if f.suffix in [".html", ".json"]]
    
    def launch(self, share=False, inbrowser=True):
        """Launch the web interface."""
        # Open the browser after a short delay
        if inbrowser:
            threading.Timer(1.5, lambda: webbrowser.open("http://127.0.0.1:7860")).start()
        
        # Launch the interface
        self.interface.launch(share=share)


def main():
    """Main entry point for the web interface."""
    parser = argparse.ArgumentParser(description="Codebase Analysis Viewer Web Interface")
    parser.add_argument("--share", action="store_true", help="Create a shareable link")
    parser.add_argument("--no-browser", action="store_true", help="Don't open the browser automatically")
    
    args = parser.parse_args()
    
    try:
        app = CodebaseAnalysisViewerWeb()
        app.launch(share=args.share, inbrowser=not args.no_browser)
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

