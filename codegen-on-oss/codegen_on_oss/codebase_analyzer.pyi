from typing import Dict, List, Any, Optional, Union

class CodebaseAnalyzer:
    def __init__(
        self, 
        repo_url: Optional[str] = None, 
        repo_path: Optional[str] = None, 
        language: Optional[str] = None
    ) -> None: ...
    
    def analyze(
        self, 
        categories: Optional[List[str]] = None, 
        output_format: str = "json", 
        output_file: Optional[str] = None,
        depth: int = 2
    ) -> Dict[str, Any]: ...
    
    def _generate_html_report(
        self,
        output_file: str
    ) -> None: ...

def main() -> None: ...
