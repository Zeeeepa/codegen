from typing import Dict, List, Any, Optional, Tuple, Callable
import gradio as gr

class CodebaseAnalysisViewerWeb:
    def __init__(self) -> None: ...
    def launch(self, share: bool = False, inbrowser: bool = True) -> None: ...
    def _create_interface(self) -> gr.Blocks: ...
    def _analyze_codebase(
        self, 
        repo_url: str, 
        repo_path: str, 
        language: str, 
        categories: List[str]
    ) -> Tuple[str, Dict[str, Any]]: ...
    def _compare_codebases(
        self, 
        base_repo_url: str, 
        base_repo_path: str, 
        compare_repo_url: str, 
        compare_repo_path: str, 
        base_branch: str, 
        compare_branch: str, 
        language: str, 
        categories: List[str]
    ) -> Tuple[str, Dict[str, Any]]: ...
    def _format_results(self, results: Dict[str, Any]) -> str: ...

def main() -> None: ...

