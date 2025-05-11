from typing import Any, Dict, List, Optional, Union

class CodebaseComparator:
    def __init__(
        self,
        base_repo_url: Optional[str] = None,
        base_repo_path: Optional[str] = None,
        compare_repo_url: Optional[str] = None,
        compare_repo_path: Optional[str] = None,
        base_branch: Optional[str] = None,
        compare_branch: Optional[str] = None,
        language: Optional[str] = None,
    ) -> None: ...
    
    def compare(
        self,
        categories: Optional[List[str]] = None,
        depth: int = 2,
        output_format: str = "console",
        output_file: Optional[str] = None,
    ) -> Dict[str, Any]: ...

