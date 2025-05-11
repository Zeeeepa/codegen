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
import argparse
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
        self.temp_dir = Path(tempfile.mkdtemp(prefix="codebase_analysis_"))
        
        # Create the Gradio interface
        self._create_interface()
    
    def _create_interface(self):
        """Create the Gradio interface."""
        with gr.Blocks(title="Codebase Analysis Viewer", theme=gr.themes.Soft()) as self.interface:
            gr.Markdown("# Codebase Analysis Viewer")
            gr.Markdown("Analyze and compare codebases with powerful static analysis tools.")
            
            with gr.Tabs():
                with gr.TabItem("Single Codebase Analysis"):
                    self._create_single_analysis_tab()
                
                with gr.TabItem("Codebase Comparison"):
                    self._create_comparison_tab()
                
                with gr.TabItem("View Results"):
                    self._create_results_tab()
                
                with gr.TabItem("Help & Examples"):
                    self._create_help_tab()
    
    def _create_single_analysis_tab(self):
        """Create the single codebase analysis tab."""
        with gr.Row():
            with gr.Column(scale=1):
                repo_source = gr.Radio(
                    ["Repository URL", "Local Repository Path", "Upload ZIP File"],
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
                
                repo_zip = gr.File(
                    label="Upload Repository ZIP",
                    file_types=[".zip"],
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
                
                depth = gr.Slider(
                    minimum=1,
                    maximum=3,
                    value=2,
                    step=1,
                    label="Analysis Depth (1=Basic, 3=Detailed)"
                )
                
                output_format = gr.Radio(
                    ["HTML", "JSON"],
                    label="Output Format",
                    value="HTML"
                )
                
                analyze_button = gr.Button("Analyze Codebase", variant="primary")
            
            with gr.Column(scale=1):
                analysis_output = gr.Textbox(
                    label="Analysis Status",
                    placeholder="Analysis results will appear here...",
                    lines=20
                )
                
                result_file = gr.File(label="Analysis Result File")
                
                with gr.Accordion("Visualization", open=False):
                    visualization_type = gr.Radio(
                        ["Module Dependencies", "Symbol Dependencies", "Code Metrics", "Language Distribution"],
                        label="Visualization Type",
                        value="Module Dependencies"
                    )
                    visualization_output = gr.Plot(label="Visualization")
                    generate_viz_button = gr.Button("Generate Visualization")
        
        # Handle repository source change
        def update_repo_input(source):
            if source == "Repository URL":
                return gr.update(visible=True), gr.update(visible=False), gr.update(visible=False)
            elif source == "Local Repository Path":
                return gr.update(visible=False), gr.update(visible=True), gr.update(visible=False)
            else:  # Upload ZIP File
                return gr.update(visible=False), gr.update(visible=False), gr.update(visible=True)
        
        repo_source.change(
            update_repo_input,
            inputs=[repo_source],
            outputs=[repo_url, repo_path, repo_zip]
        )
        
        # Handle analyze button click
        def analyze_codebase(repo_source, repo_url, repo_path, repo_zip, language, categories, depth, output_format):
            try:
                # Prepare parameters
                repo_url_param = None
                repo_path_param = None
                
                if repo_source == "Repository URL":
                    repo_url_param = repo_url
                elif repo_source == "Local Repository Path":
                    repo_path_param = repo_path
                elif repo_source == "Upload ZIP File" and repo_zip is not None:
                    # Extract the ZIP file to a temporary directory
                    import zipfile
                    zip_path = repo_zip.name
                    extract_dir = self.temp_dir / f"upload_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    extract_dir.mkdir(exist_ok=True)
                    
                    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                        zip_ref.extractall(extract_dir)
                    
                    # Find the repository root (first directory with .git or first directory if no .git)
                    repo_root = None
                    for path in extract_dir.iterdir():
                        if path.is_dir():
                            if (path / ".git").exists():
                                repo_root = path
                                break
                            elif repo_root is None:
                                repo_root = path
                    
                    if repo_root is None:
                        return "Error: No valid repository found in the ZIP file.", None
                    
                    repo_path_param = str(repo_root)
                
                language_param = None if language == "Auto-detect" else language.lower()
                
                # Initialize the analyzer
                analyzer = CodebaseAnalyzer(
                    repo_url=repo_url_param,
                    repo_path=repo_path_param,
                    language=language_param
                )
                
                # Generate a unique filename for the results
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                if repo_url_param:
                    repo_name = repo_url.split("/")[-1].replace(".git", "")
                elif repo_path_param:
                    repo_name = Path(repo_path_param).name
                else:
                    repo_name = "unknown_repo"
                
                if output_format == "HTML":
                    output_file = self.results_dir / f"analysis_{repo_name}_{timestamp}.html"
                else:
                    output_file = self.results_dir / f"analysis_{repo_name}_{timestamp}.json"
                
                # Perform the analysis
                results = analyzer.analyze(
                    categories=categories,
                    depth=int(depth),
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
            inputs=[repo_source, repo_url, repo_path, repo_zip, language, categories, depth, output_format],
            outputs=[analysis_output, result_file]
        )
        
        # Handle visualization generation
        def generate_visualization(visualization_type, result_file):
            if not result_file:
                return None
            
            try:
                import matplotlib.pyplot as plt
                import networkx as nx
                import numpy as np
                import json
                
                # Load the analysis results
                with open(result_file.name, "r") as f:
                    if result_file.name.endswith(".json"):
                        results = json.load(f)
                    else:  # HTML file
                        # Extract JSON data from HTML (simplified approach)
                        content = f.read()
                        json_start = content.find("var analysisData = ") + len("var analysisData = ")
                        json_end = content.find("</script>", json_start)
                        if json_start > len("var analysisData = ") and json_end > json_start:
                            json_str = content[json_start:json_end].strip().rstrip(";")
                            results = json.loads(json_str)
                        else:
                            return None
                
                plt.figure(figsize=(10, 8))
                
                if visualization_type == "Module Dependencies":
                    # Create a directed graph of module dependencies
                    G = nx.DiGraph()
                    
                    # Add nodes and edges based on imports
                    if "dependencies" in results and "module_dependencies" in results["dependencies"]:
                        for module, imports in results["dependencies"]["module_dependencies"].items():
                            G.add_node(module)
                            for imported in imports:
                                G.add_edge(module, imported)
                    
                    # Draw the graph
                    pos = nx.spring_layout(G)
                    nx.draw(G, pos, with_labels=True, node_color="skyblue", node_size=1500, 
                            font_size=10, font_weight="bold", arrows=True)
                    plt.title("Module Dependencies")
                
                elif visualization_type == "Symbol Dependencies":
                    # Create a directed graph of symbol dependencies
                    G = nx.DiGraph()
                    
                    # Add nodes and edges based on function calls
                    if "dependencies" in results and "function_calls" in results["dependencies"]:
                        for func, calls in results["dependencies"]["function_calls"].items():
                            G.add_node(func)
                            for called in calls:
                                G.add_edge(func, called)
                    
                    # Draw the graph
                    pos = nx.spring_layout(G)
                    nx.draw(G, pos, with_labels=True, node_color="lightgreen", node_size=1500, 
                            font_size=8, font_weight="bold", arrows=True)
                    plt.title("Symbol Dependencies")
                
                elif visualization_type == "Code Metrics":
                    # Bar chart of code metrics
                    metrics = {}
                    
                    if "code_metrics" in results:
                        for metric, value in results["code_metrics"].items():
                            if isinstance(value, (int, float)):
                                metrics[metric] = value
                    
                    if metrics:
                        plt.bar(metrics.keys(), metrics.values(), color="coral")
                        plt.xticks(rotation=45, ha="right")
                        plt.tight_layout()
                        plt.title("Code Metrics")
                    else:
                        plt.text(0.5, 0.5, "No code metrics available", 
                                ha="center", va="center", fontsize=12)
                
                elif visualization_type == "Language Distribution":
                    # Pie chart of language distribution
                    languages = {}
                    
                    if "structure" in results and "language_distribution" in results["structure"]:
                        languages = results["structure"]["language_distribution"]
                    
                    if languages:
                        plt.pie(languages.values(), labels=languages.keys(), autopct='%1.1f%%',
                                startangle=90, colors=plt.cm.Paired.colors)
                        plt.axis('equal')
                        plt.title("Language Distribution")
                    else:
                        plt.text(0.5, 0.5, "No language distribution available", 
                                ha="center", va="center", fontsize=12)
                
                return plt
            
            except Exception as e:
                import traceback
                logger.error(f"Visualization error: {str(e)}\n{traceback.format_exc()}")
                
                plt.figure(figsize=(10, 8))
                plt.text(0.5, 0.5, f"Error generating visualization:\n{str(e)}", 
                        ha="center", va="center", fontsize=12, color="red")
                return plt
        
        generate_viz_button.click(
            generate_visualization,
            inputs=[visualization_type, result_file],
            outputs=[visualization_output]
        )
    
    def _create_comparison_tab(self):
        """Create the codebase comparison tab."""
        with gr.Row():
            with gr.Column():
                gr.Markdown("### Base Repository")
                
                base_repo_source = gr.Radio(
                    ["Repository URL", "Local Repository Path", "Upload ZIP File"],
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
                
                base_repo_zip = gr.File(
                    label="Upload Base Repository ZIP",
                    file_types=[".zip"],
                    visible=False
                )
                
                base_branch = gr.Textbox(
                    label="Base Branch (optional)",
                    placeholder="main"
                )
            
            with gr.Column():
                gr.Markdown("### Comparison Repository")
                
                compare_repo_source = gr.Radio(
                    ["Repository URL", "Local Repository Path", "Upload ZIP File", "Same Repository (Different Branch)"],
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
                
                compare_repo_zip = gr.File(
                    label="Upload Comparison Repository ZIP",
                    file_types=[".zip"],
                    visible=False
                )
                
                compare_branch = gr.Textbox(
                    label="Comparison Branch",
                    placeholder="feature-branch",
                    visible=False
                )
        
        with gr.Row():
            with gr.Column(scale=1):
                language = gr.Dropdown(
                    ["Auto-detect", "Python", "TypeScript", "JavaScript", "Java", "Go", "Rust", "C++", "C#"],
                    label="Programming Language",
                    value="Auto-detect"
                )
                
                categories = gr.CheckboxGroup(
                    list(METRICS_CATEGORIES.keys()),
                    label="Categories to Compare",
                    value=list(METRICS_CATEGORIES.keys())
                )
                
                depth = gr.Slider(
                    minimum=1,
                    maximum=3,
                    value=2,
                    step=1,
                    label="Comparison Depth (1=Basic, 3=Detailed)"
                )
                
                output_format = gr.Radio(
                    ["HTML", "JSON"],
                    label="Output Format",
                    value="HTML"
                )
                
                compare_button = gr.Button("Compare Codebases", variant="primary")
            
            with gr.Column(scale=1):
                comparison_output = gr.Textbox(
                    label="Comparison Status",
                    placeholder="Comparison results will appear here...",
                    lines=20
                )
                
                comparison_file = gr.File(label="Comparison Result File")
                
                with gr.Accordion("Visualization", open=False):
                    comparison_viz_type = gr.Radio(
                        ["Diff Summary", "Added/Removed Files", "Code Metrics Comparison", "Dependency Changes"],
                        label="Visualization Type",
                        value="Diff Summary"
                    )
                    comparison_viz_output = gr.Plot(label="Visualization")
                    generate_comparison_viz_button = gr.Button("Generate Visualization")
        
        # Handle repository source changes
        def update_base_repo_input(source):
            if source == "Repository URL":
                return gr.update(visible=True), gr.update(visible=False), gr.update(visible=False)
            elif source == "Local Repository Path":
                return gr.update(visible=False), gr.update(visible=True), gr.update(visible=False)
            else:  # Upload ZIP File
                return gr.update(visible=False), gr.update(visible=False), gr.update(visible=True)
        
        base_repo_source.change(
            update_base_repo_input,
            inputs=[base_repo_source],
            outputs=[base_repo_url, base_repo_path, base_repo_zip]
        )
        
        def update_compare_repo_input(source):
            if source == "Repository URL":
                return gr.update(visible=True), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False)
            elif source == "Local Repository Path":
                return gr.update(visible=False), gr.update(visible=True), gr.update(visible=False), gr.update(visible=False)
            elif source == "Upload ZIP File":
                return gr.update(visible=False), gr.update(visible=False), gr.update(visible=True), gr.update(visible=False)
            else:  # Same Repository (Different Branch)
                return gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(visible=True)
        
        compare_repo_source.change(
            update_compare_repo_input,
            inputs=[compare_repo_source],
            outputs=[compare_repo_url, compare_repo_path, compare_repo_zip, compare_branch]
        )
        
        # Handle compare button click
        def compare_codebases(
            base_repo_source, base_repo_url, base_repo_path, base_repo_zip, base_branch,
            compare_repo_source, compare_repo_url, compare_repo_path, compare_repo_zip, compare_branch,
            language, categories, depth, output_format
        ):
            try:
                # Prepare parameters
                base_repo_url_param = None
                base_repo_path_param = None
                compare_repo_url_param = None
                compare_repo_path_param = None
                
                # Process base repository
                if base_repo_source == "Repository URL":
                    base_repo_url_param = base_repo_url
                elif base_repo_source == "Local Repository Path":
                    base_repo_path_param = base_repo_path
                elif base_repo_source == "Upload ZIP File" and base_repo_zip is not None:
                    # Extract the ZIP file to a temporary directory
                    import zipfile
                    zip_path = base_repo_zip.name
                    extract_dir = self.temp_dir / f"base_upload_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    extract_dir.mkdir(exist_ok=True)
                    
                    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                        zip_ref.extractall(extract_dir)
                    
                    # Find the repository root
                    repo_root = None
                    for path in extract_dir.iterdir():
                        if path.is_dir():
                            if (path / ".git").exists():
                                repo_root = path
                                break
                            elif repo_root is None:
                                repo_root = path
                    
                    if repo_root is None:
                        return "Error: No valid repository found in the base ZIP file.", None
                    
                    base_repo_path_param = str(repo_root)
                
                # Process comparison repository
                if compare_repo_source == "Same Repository (Different Branch)":
                    compare_repo_url_param = base_repo_url_param
                    compare_repo_path_param = base_repo_path_param
                elif compare_repo_source == "Repository URL":
                    compare_repo_url_param = compare_repo_url
                elif compare_repo_source == "Local Repository Path":
                    compare_repo_path_param = compare_repo_path
                elif compare_repo_source == "Upload ZIP File" and compare_repo_zip is not None:
                    # Extract the ZIP file to a temporary directory
                    import zipfile
                    zip_path = compare_repo_zip.name
                    extract_dir = self.temp_dir / f"compare_upload_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    extract_dir.mkdir(exist_ok=True)
                    
                    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                        zip_ref.extractall(extract_dir)
                    
                    # Find the repository root
                    repo_root = None
                    for path in extract_dir.iterdir():
                        if path.is_dir():
                            if (path / ".git").exists():
                                repo_root = path
                                break
                            elif repo_root is None:
                                repo_root = path
                    
                    if repo_root is None:
                        return "Error: No valid repository found in the comparison ZIP file.", None
                    
                    compare_repo_path_param = str(repo_root)
                
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
                
                if base_repo_url_param:
                    base_name = base_repo_url.split("/")[-1].replace(".git", "")
                elif base_repo_path_param:
                    base_name = Path(base_repo_path_param).name
                else:
                    base_name = "unknown_base"
                
                if compare_repo_source == "Same Repository (Different Branch)":
                    compare_name = f"{base_name}_{compare_branch}"
                elif compare_repo_url_param:
                    compare_name = compare_repo_url.split("/")[-1].replace(".git", "")
                elif compare_repo_path_param:
                    compare_name = Path(compare_repo_path_param).name
                else:
                    compare_name = "unknown_compare"
                
                if output_format == "HTML":
                    output_file = self.results_dir / f"comparison_{base_name}_vs_{compare_name}_{timestamp}.html"
                else:
                    output_file = self.results_dir / f"comparison_{base_name}_vs_{compare_name}_{timestamp}.json"
                
                # Perform the comparison
                results = comparator.compare(
                    categories=categories,
                    depth=int(depth),
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
                base_repo_source, base_repo_url, base_repo_path, base_repo_zip, base_branch,
                compare_repo_source, compare_repo_url, compare_repo_path, compare_repo_zip, compare_branch,
                language, categories, depth, output_format
            ],
            outputs=[comparison_output, comparison_file]
        )
        
        # Handle visualization generation
        def generate_comparison_visualization(visualization_type, result_file):
            if not result_file:
                return None
            
            try:
                import matplotlib.pyplot as plt
                import numpy as np
                import json
                
                # Load the comparison results
                with open(result_file.name, "r") as f:
                    if result_file.name.endswith(".json"):
                        results = json.load(f)
                    else:  # HTML file
                        # Extract JSON data from HTML (simplified approach)
                        content = f.read()
                        json_start = content.find("var comparisonData = ") + len("var comparisonData = ")
                        json_end = content.find("</script>", json_start)
                        if json_start > len("var comparisonData = ") and json_end > json_start:
                            json_str = content[json_start:json_end].strip().rstrip(";")
                            results = json.loads(json_str)
                        else:
                            return None
                
                plt.figure(figsize=(10, 8))
                
                if visualization_type == "Diff Summary":
                    # Bar chart of added/modified/removed counts
                    diff_summary = {
                        "Added": 0,
                        "Modified": 0,
                        "Removed": 0
                    }
                    
                    if "diff_summary" in results:
                        diff_summary = results["diff_summary"]
                    
                    plt.bar(diff_summary.keys(), diff_summary.values(), color=["green", "orange", "red"])
                    plt.title("Diff Summary")
                    plt.ylabel("Count")
                    for i, v in enumerate(diff_summary.values()):
                        plt.text(i, v + 0.5, str(v), ha='center')
                
                elif visualization_type == "Added/Removed Files":
                    # Pie chart of file types added/removed
                    file_types = {}
                    
                    if "file_changes" in results:
                        for file_path in results["file_changes"].get("added", []):
                            ext = Path(file_path).suffix
                            if ext:
                                file_types[ext] = file_types.get(ext, 0) + 1
                            else:
                                file_types["(no extension)"] = file_types.get("(no extension)", 0) + 1
                    
                    if file_types:
                        plt.pie(file_types.values(), labels=file_types.keys(), autopct='%1.1f%%',
                                startangle=90, colors=plt.cm.Paired.colors)
                        plt.axis('equal')
                        plt.title("Added Files by Type")
                    else:
                        plt.text(0.5, 0.5, "No file type data available", 
                                ha="center", va="center", fontsize=12)
                
                elif visualization_type == "Code Metrics Comparison":
                    # Comparison of code metrics between base and comparison
                    if "code_metrics" in results and "base" in results["code_metrics"] and "compare" in results["code_metrics"]:
                        base_metrics = results["code_metrics"]["base"]
                        compare_metrics = results["code_metrics"]["compare"]
                        
                        # Find common metrics
                        common_metrics = set(base_metrics.keys()) & set(compare_metrics.keys())
                        common_metrics = [m for m in common_metrics if isinstance(base_metrics[m], (int, float)) and isinstance(compare_metrics[m], (int, float))]
                        
                        if common_metrics:
                            x = np.arange(len(common_metrics))
                            width = 0.35
                        
                            base_values = [base_metrics[m] for m in common_metrics]
                            compare_values = [compare_metrics[m] for m in common_metrics]
                        
                            plt.bar(x - width/2, base_values, width, label='Base')
                            plt.bar(x + width/2, compare_values, width, label='Compare')
                            
                            plt.xlabel('Metrics')
                            plt.ylabel('Values')
                            plt.title('Code Metrics Comparison')
                            plt.xticks(x, common_metrics, rotation=45, ha="right")
                            plt.legend()
                            plt.tight_layout()
                        else:
                            plt.text(0.5, 0.5, "No comparable metrics available", 
                                    ha="center", va="center", fontsize=12)
                    else:
                        plt.text(0.5, 0.5, "No code metrics comparison available", 
                                ha="center", va="center", fontsize=12)
                
                elif visualization_type == "Dependency Changes":
                    # Visualization of dependency changes
                    if "dependency_changes" in results:
                        dep_changes = results["dependency_changes"]
                        
                        categories = ["Added", "Removed", "Modified"]
                        values = [
                            len(dep_changes.get("added", [])),
                            len(dep_changes.get("removed", [])),
                            len(dep_changes.get("modified", []))
                        ]
                        
                        plt.bar(categories, values, color=["green", "red", "orange"])
                        plt.title("Dependency Changes")
                        plt.ylabel("Count")
                        for i, v in enumerate(values):
                            plt.text(i, v + 0.5, str(v), ha='center')
                    else:
                        plt.text(0.5, 0.5, "No dependency changes data available", 
                                ha="center", va="center", fontsize=12)
                
                return plt
            
            except Exception as e:
                import traceback
                logger.error(f"Comparison visualization error: {str(e)}\n{traceback.format_exc()}")
                
                plt.figure(figsize=(10, 8))
                plt.text(0.5, 0.5, f"Error generating visualization:\n{str(e)}", 
                        ha="center", va="center", fontsize=12, color="red")
                return plt
        
        generate_comparison_viz_button.click(
            generate_comparison_visualization,
            inputs=[comparison_viz_type, comparison_file],
            outputs=[comparison_viz_output]
        )
    
    def _create_results_tab(self):
        """Create the results viewing tab."""
        with gr.Row():
            with gr.Column(scale=1):
                result_files = gr.Dropdown(
                    self._get_result_files(),
                    label="Select Result File",
                    interactive=True
                )
                
                refresh_button = gr.Button("Refresh Results")
                
                with gr.Row():
                    view_button = gr.Button("View Selected Result", variant="primary")
                    download_button = gr.Button("Download Result", variant="secondary")
                    delete_button = gr.Button("Delete Result", variant="stop")
                
                with gr.Accordion("Result Management", open=False):
                    export_format = gr.Radio(
                        ["HTML", "JSON", "PDF"],
                        label="Export Format",
                        value="HTML"
                    )
                    export_button = gr.Button("Export Result")
                    
                    gr.Markdown("### Batch Operations")
                    delete_all_button = gr.Button("Delete All Results", variant="stop")
            
            with gr.Column(scale=2):
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
        
        # Handle download button click
        def download_result(result_file):
            if not result_file:
                return None
            
            file_path = self.results_dir / result_file
            
            if not file_path.exists():
                return None
            
            return file_path
        
        download_button.click(
            download_result,
            inputs=[result_files],
            outputs=[gr.File(label="Download")]
        )
        
        # Handle delete button click
        def delete_result(result_file):
            if not result_file:
                return "No file selected.", gr.update(choices=self._get_result_files())
            
            file_path = self.results_dir / result_file
            
            if not file_path.exists():
                return f"Error: File {file_path} not found.", gr.update(choices=self._get_result_files())
            
            try:
                file_path.unlink()
                return f"Successfully deleted {result_file}.", gr.update(choices=self._get_result_files())
            except Exception as e:
                return f"Error deleting file: {str(e)}", gr.update(choices=self._get_result_files())
        
        delete_button.click(
            delete_result,
            inputs=[result_files],
            outputs=[gr.Textbox(label="Delete Status"), result_files]
        )
        
        # Handle export button click
        def export_result(result_file, export_format):
            if not result_file:
                return "No file selected.", None
            
            file_path = self.results_dir / result_file
            
            if not file_path.exists():
                return f"Error: File {file_path} not found.", None
            
            try:
                # Generate a new filename for the exported file
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                base_name = file_path.stem
                
                if export_format == "HTML" and file_path.suffix != ".html":
                    # Convert JSON to HTML
                    with open(file_path, "r") as f:
                        data = json.load(f)
                    
                    export_path = self.results_dir / f"{base_name}_export_{timestamp}.html"
                    
                    # Create a simple HTML template
                    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>Codebase Analysis Result</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #333; }}
        pre {{ background-color: #f5f5f5; padding: 10px; border-radius: 5px; overflow-x: auto; }}
        .section {{ margin-bottom: 20px; }}
    </style>
</head>
<body>
    <h1>Codebase Analysis Result</h1>
    <div class="section">
        <h2>Result Data</h2>
        <pre>{json.dumps(data, indent=2)}</pre>
    </div>
    <script>
        var analysisData = {json.dumps(data)};
    </script>
</body>
</html>"""
                    
                    with open(export_path, "w") as f:
                        f.write(html_content)
                    
                    return f"Exported to HTML: {export_path}", export_path
                
                elif export_format == "JSON" and file_path.suffix != ".json":
                    # Convert HTML to JSON (extract the JSON data from the HTML)
                    with open(file_path, "r") as f:
                        content = f.read()
                    
                    json_start = content.find("var analysisData = ") + len("var analysisData = ")
                    json_end = content.find("</script>", json_start)
                    
                    if json_start > len("var analysisData = ") and json_end > json_start:
                        json_str = content[json_start:json_end].strip().rstrip(";")
                        data = json.loads(json_str)
                        
                        export_path = self.results_dir / f"{base_name}_export_{timestamp}.json"
                        
                        with open(export_path, "w") as f:
                            json.dump(data, f, indent=2)
                        
                        return f"Exported to JSON: {export_path}", export_path
                    else:
                        return "Error: Could not extract JSON data from HTML.", None
                
                elif export_format == "PDF":
                    # Convert to PDF using a library like weasyprint or pdfkit
                    try:
                        import pdfkit
                        export_path = self.results_dir / f"{base_name}_export_{timestamp}.pdf"
                        
                        if file_path.suffix == ".html":
                            # Convert HTML directly to PDF
                            pdfkit.from_file(str(file_path), str(export_path))
                        else:  # JSON
                            # Convert JSON to HTML first, then to PDF
                            with open(file_path, "r") as f:
                                data = json.load(f)
                            
                            html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>Codebase Analysis Result</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #333; }}
        pre {{ background-color: #f5f5f5; padding: 10px; border-radius: 5px; overflow-x: auto; }}
        .section {{ margin-bottom: 20px; }}
    </style>
</head>
<body>
    <h1>Codebase Analysis Result</h1>
    <div class="section">
        <h2>Result Data</h2>
        <pre>{json.dumps(data, indent=2)}</pre>
    </div>
</body>
</html>"""
                            
                            temp_html = self.temp_dir / f"temp_{timestamp}.html"
                            with open(temp_html, "w") as f:
                                f.write(html_content)
                            
                            pdfkit.from_file(str(temp_html), str(export_path))
                            temp_html.unlink()  # Remove temporary HTML file
                        
                        return f"Exported to PDF: {export_path}", export_path
                    except ImportError:
                        return "Error: pdfkit library not installed. Please install it with 'pip install pdfkit'.", None
                    except Exception as e:
                        return f"Error exporting to PDF: {str(e)}", None
                
                else:
                    # Just copy the file with a new name
                    export_path = self.results_dir / f"{base_name}_export_{timestamp}{file_path.suffix}"
                    import shutil
                    shutil.copy2(file_path, export_path)
                    return f"Exported to {export_format}: {export_path}", export_path
            
            except Exception as e:
                return f"Error exporting file: {str(e)}", None
        
        export_button.click(
            export_result,
            inputs=[result_files, export_format],
            outputs=[gr.Textbox(label="Export Status"), gr.File(label="Exported File")]
        )
        
        # Handle delete all button click
        def delete_all_results():
            try:
                deleted_count = 0
                for file_path in self.results_dir.iterdir():
                    if file_path.suffix in [".html", ".json", ".pdf"]:
                        file_path.unlink()
                        deleted_count += 1
                
                return f"Successfully deleted {deleted_count} result files.", gr.update(choices=[])
            except Exception as e:
                return f"Error deleting files: {str(e)}", gr.update(choices=self._get_result_files())
        
        delete_all_button.click(
            delete_all_results,
            inputs=[],
            outputs=[gr.Textbox(label="Delete Status"), result_files]
        )
    
    def _create_help_tab(self):
        """Create the help and examples tab."""
        with gr.Blocks():
            gr.Markdown("# Help & Examples")
            
            with gr.Accordion("Getting Started", open=True):
                gr.Markdown("""
                ## Getting Started with Codebase Analysis Viewer
                
                This tool allows you to analyze and compare codebases using powerful static analysis techniques.
                
                ### Basic Workflow
                
                1. **Single Codebase Analysis**:
                   - Provide a repository URL, local path, or upload a ZIP file
                   - Select analysis options (language, categories, depth)
                   - Click "Analyze Codebase"
                   - View results and visualizations
                
                2. **Codebase Comparison**:
                   - Provide two repositories (or two branches of the same repository)
                   - Select comparison options
                   - Click "Compare Codebases"
                   - View comparison results and visualizations
                
                3. **View Results**:
                   - Access previously generated analysis and comparison reports
                   - Select a result file and click "View Selected Result"
                """)
            
            with gr.Accordion("Analysis Categories", open=False):
                gr.Markdown("""
                ## Analysis Categories
                
                The analyzer supports the following categories:
                
                - **Structure**: File counts, language distribution, directory structure
                - **Symbols**: Function parameters, return types, complexity metrics
                - **Dependencies**: Function call relationships, entry point analysis
                - **Quality**: Unused functions, repeated code patterns, refactoring opportunities
                - **Metrics**: Cyclomatic complexity, Halstead volume, maintainability index
                - **Language Specific**: Decorator usage, type hint coverage (Python), etc.
                
                Adjust the analysis depth to control the level of detail:
                - **Depth 1**: Basic analysis (faster)
                - **Depth 2**: Standard analysis (balanced)
                - **Depth 3**: Detailed analysis (slower)
                """)
            
            with gr.Accordion("Example Repositories", open=False):
                gr.Markdown("""
                ## Example Repositories
                
                Try analyzing these repositories:
                
                ### Python Projects
                - https://github.com/pallets/flask
                - https://github.com/django/django
                - https://github.com/psf/requests
                
                ### JavaScript/TypeScript Projects
                - https://github.com/facebook/react
                - https://github.com/vercel/next.js
                - https://github.com/microsoft/TypeScript
                
                ### Other Languages
                - https://github.com/golang/go (Go)
                - https://github.com/rust-lang/rust (Rust)
                - https://github.com/JetBrains/kotlin (Kotlin)
                """)
            
            with gr.Accordion("Visualization Guide", open=False):
                gr.Markdown("""
                ## Visualization Guide
                
                The tool provides various visualizations to help understand your codebase:
                
                ### Single Codebase Visualizations
                
                - **Module Dependencies**: Graph showing import relationships between modules
                - **Symbol Dependencies**: Graph showing function call relationships
                - **Code Metrics**: Bar chart of various code quality metrics
                - **Language Distribution**: Pie chart showing programming language distribution
                
                ### Comparison Visualizations
                
                - **Diff Summary**: Bar chart showing added, modified, and removed elements
                - **Added/Removed Files**: Pie chart of file types added or removed
                - **Code Metrics Comparison**: Side-by-side comparison of metrics between codebases
                - **Dependency Changes**: Bar chart showing dependency changes
                """)
            
            with gr.Accordion("Troubleshooting", open=False):
                gr.Markdown("""
                ## Troubleshooting
                
                ### Common Issues
                
                - **Repository Access**: Ensure public repositories are accessible or provide credentials for private repos
                - **ZIP Files**: Make sure uploaded ZIP files contain a valid repository structure
                - **Large Repositories**: Very large repositories may take longer to analyze or cause timeouts
                - **Memory Issues**: Reduce analysis depth for large codebases if you encounter memory errors
                
                ### Error Messages
                
                If you encounter errors, check the analysis status output for detailed error messages.
                Common errors include:
                
                - Repository not found or inaccessible
                - Invalid repository structure
                - Unsupported file formats
                - Memory limitations
                
                ### Getting Help
                
                For additional help, please refer to the documentation or contact support.
                """)
            
            with gr.Accordion("About", open=False):
                gr.Markdown("""
                ## About Codebase Analysis Viewer
                
                This tool is part of the codegen-on-oss project, which provides tools for analyzing
                and comparing codebases using static analysis techniques.
                
                ### Features
                
                - Comprehensive static analysis of codebases
                - Comparison between different repositories or branches
                - Interactive visualizations
                - Support for multiple programming languages
                - Downloadable reports in various formats
                
                ### Technologies
                
                - Built with Python and Gradio
                - Uses advanced static analysis techniques
                - Supports visualization with matplotlib and networkx
                - Handles various repository sources (URL, local path, ZIP upload)
                
                ### Version
                
                Version 0.1.0
                """)
    
    def _get_result_files(self):
        """Get a list of result files in the results directory."""
        if not self.results_dir.exists():
            return []
        
        return [f.name for f in self.results_dir.iterdir() if f.suffix in [".html", ".json"]]
    
    def launch(self, share=False, inbrowser=True, port=7860, host="127.0.0.1"):
        """
        Launch the web interface.
        
        Args:
            share: Whether to create a shareable link
            inbrowser: Whether to open the browser automatically
            port: Port to run the web interface on
            host: Host to run the web interface on
        """
        # Open the browser after a short delay
        if inbrowser:
            threading.Timer(1.5, lambda: webbrowser.open(f"http://{host}:{port}")).start()
        
        # Launch the interface
        self.interface.launch(share=share, server_name=host, server_port=port)
    
    def cleanup(self):
        """Clean up temporary files."""
        import shutil
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir, ignore_errors=True)


def main():
    """Main entry point for the web interface."""
    parser = argparse.ArgumentParser(description="Codebase Analysis Viewer Web Interface")
    parser.add_argument("--share", action="store_true", help="Create a shareable link")
    parser.add_argument("--no-browser", action="store_true", help="Don't open the browser automatically")
    parser.add_argument("--port", type=int, default=7860, help="Port to run the web interface on")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host to run the web interface on")
    
    args = parser.parse_args()
    
    try:
        app = CodebaseAnalysisViewerWeb()
        app.launch(share=args.share, inbrowser=not args.no_browser, port=args.port, host=args.host)
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        # Clean up temporary files
        if 'app' in locals():
            app.cleanup()


if __name__ == "__main__":
    main()
