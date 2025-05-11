from typing import Any, Dict, List, Optional, Union

class CodebaseAnalyzer:
    def __init__(
        self,
        repo_url: Optional[str] = None,
        repo_path: Optional[str] = None,
        language: Optional[str] = None,
    ) -> None: ...
    
    def analyze(
        self,
        categories: Optional[List[str]] = None,
        depth: int = 2,
        output_format: str = "console",
        output_file: Optional[str] = None,
    ) -> Dict[str, Any]: ...

