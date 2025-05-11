import gradio as gr
from typing import Dict, List, Optional, Any, Union, Tuple

class AnalysisViewerWeb:
    def __init__(self) -> None: ...
    
    def analyze_repo(
        self,
        repo_source: str,
        repo_url: str,
        repo_path: str,
        language: str,
        categories: List[str],
        depth: int
    ) -> Tuple[str, Dict[str, Any]]: ...
    
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
    ) -> Tuple[str, Dict[str, Any]]: ...
    
    def save_results(
        self, 
        results: Dict[str, Any], 
        format: str, 
        filename: str
    ) -> str: ...
    
    def create_interface(self) -> gr.Blocks: ...
    
    def launch(
        self, 
        port: int = 7860, 
        host: str = "127.0.0.1", 
        share: bool = False, 
        open_browser: bool = True
    ) -> None: ...

def main() -> None: ...
