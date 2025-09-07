"""
Project Adapter for Serena Tools Integration

Provides adapter interface between Serena's ProjectManager functionality
and SDK's existing project management systems.
"""

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

log = logging.getLogger(__name__)


class ProjectAdapter:
    """
    Adapter class that bridges Serena's ProjectManager functionality
    to SDK's existing project management capabilities.
    """
    
    def __init__(self, project_root: str = None):
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self._active_project = None
        self._project_config = {}
    
    def activate_project(self, project_path: str) -> str:
        """
        Activate a project for analysis and tool operations.
        
        :param project_path: Path to the project directory
        :return: Success message or error description
        """
        try:
            project_path = Path(project_path)
            if not project_path.is_absolute():
                project_path = self.project_root / project_path
            
            if not project_path.exists():
                return f"Project path does not exist: {project_path}"
            
            if not project_path.is_dir():
                return f"Project path is not a directory: {project_path}"
            
            self._active_project = project_path
            self._load_project_config()
            
            log.info(f"Activated project: {project_path}")
            return f"Successfully activated project: {project_path}"
            
        except Exception as e:
            log.error(f"Error activating project {project_path}: {e}")
            return f"Error activating project: {str(e)}"
    
    def get_active_project(self) -> Optional[Path]:
        """
        Get the currently active project path.
        
        :return: Path to active project or None if no project is active
        """
        return self._active_project
    
    def get_project_root(self) -> str:
        """
        Get the root directory of the active project.
        
        :return: String path to project root
        :raises ValueError: If no active project is set
        """
        if self._active_project is None:
            raise ValueError("No active project configuration is set")
        return str(self._active_project)
    
    def get_project_info(self) -> Dict[str, Any]:
        """
        Get information about the active project.
        
        :return: Dictionary containing project information
        """
        if self._active_project is None:
            return {"error": "No active project"}
        
        try:
            info = {
                "path": str(self._active_project),
                "name": self._active_project.name,
                "config": self._project_config,
                "files_count": self._count_project_files(),
                "languages": self._detect_languages(),
                "has_git": (self._active_project / ".git").exists(),
                "has_package_json": (self._active_project / "package.json").exists(),
                "has_pyproject_toml": (self._active_project / "pyproject.toml").exists(),
                "has_requirements_txt": (self._active_project / "requirements.txt").exists(),
            }
            return info
        except Exception as e:
            log.error(f"Error getting project info: {e}")
            return {"error": str(e)}
    
    def list_project_files(self, pattern: str = None, max_files: int = 100) -> List[str]:
        """
        List files in the active project.
        
        :param pattern: Optional glob pattern to filter files
        :param max_files: Maximum number of files to return
        :return: List of file paths relative to project root
        """
        if self._active_project is None:
            return []
        
        try:
            files = []
            if pattern:
                files = list(self._active_project.glob(pattern))
            else:
                files = list(self._active_project.rglob("*"))
            
            # Filter to only files (not directories)
            files = [f for f in files if f.is_file()]
            
            # Convert to relative paths
            relative_files = [str(f.relative_to(self._active_project)) for f in files]
            
            # Limit results
            return relative_files[:max_files]
            
        except Exception as e:
            log.error(f"Error listing project files: {e}")
            return []
    
    def find_files(self, pattern: str, max_files: int = 50) -> List[str]:
        """
        Find files matching a pattern in the active project.
        
        :param pattern: Glob pattern to search for
        :param max_files: Maximum number of files to return
        :return: List of matching file paths
        """
        return self.list_project_files(pattern, max_files)
    
    def get_project_structure(self, max_depth: int = 3) -> str:
        """
        Get a tree-like representation of the project structure.
        
        :param max_depth: Maximum depth to traverse
        :return: String representation of project structure
        """
        if self._active_project is None:
            return "No active project"
        
        try:
            return self._build_tree_structure(self._active_project, max_depth)
        except Exception as e:
            log.error(f"Error getting project structure: {e}")
            return f"Error getting project structure: {str(e)}"
    
    def _load_project_config(self):
        """Load project configuration from various config files."""
        self._project_config = {}
        
        # Try to load from various config files
        config_files = [
            ".serena.json",
            ".codegen.json", 
            "pyproject.toml",
            "package.json"
        ]
        
        for config_file in config_files:
            config_path = self._active_project / config_file
            if config_path.exists():
                try:
                    if config_file.endswith('.json'):
                        import json
                        with open(config_path) as f:
                            self._project_config[config_file] = json.load(f)
                    elif config_file.endswith('.toml'):
                        try:
                            import tomllib
                            with open(config_path, 'rb') as f:
                                self._project_config[config_file] = tomllib.load(f)
                        except ImportError:
                            # Fallback if tomllib not available
                            pass
                except Exception as e:
                    log.warning(f"Could not load config from {config_file}: {e}")
    
    def _count_project_files(self) -> int:
        """Count total files in the project."""
        try:
            return len([f for f in self._active_project.rglob("*") if f.is_file()])
        except Exception:
            return 0
    
    def _detect_languages(self) -> List[str]:
        """Detect programming languages used in the project."""
        language_extensions = {
            '.py': 'Python',
            '.js': 'JavaScript',
            '.ts': 'TypeScript',
            '.java': 'Java',
            '.cpp': 'C++',
            '.c': 'C',
            '.rs': 'Rust',
            '.go': 'Go',
            '.rb': 'Ruby',
            '.php': 'PHP',
            '.cs': 'C#',
            '.swift': 'Swift',
            '.kt': 'Kotlin',
            '.scala': 'Scala',
            '.clj': 'Clojure',
            '.hs': 'Haskell',
            '.ml': 'OCaml',
            '.fs': 'F#',
            '.dart': 'Dart',
            '.lua': 'Lua',
            '.r': 'R',
            '.m': 'Objective-C',
            '.sh': 'Shell',
            '.ps1': 'PowerShell'
        }
        
        detected = set()
        try:
            for file_path in self._active_project.rglob("*"):
                if file_path.is_file():
                    suffix = file_path.suffix.lower()
                    if suffix in language_extensions:
                        detected.add(language_extensions[suffix])
        except Exception:
            pass
        
        return sorted(list(detected))
    
    def _build_tree_structure(self, path: Path, max_depth: int, current_depth: int = 0, prefix: str = "") -> str:
        """Build a tree-like string representation of directory structure."""
        if current_depth >= max_depth:
            return ""
        
        items = []
        try:
            # Get directories and files separately
            dirs = [p for p in path.iterdir() if p.is_dir() and not p.name.startswith('.')]
            files = [p for p in path.iterdir() if p.is_file() and not p.name.startswith('.')]
            
            # Sort both
            dirs.sort(key=lambda x: x.name.lower())
            files.sort(key=lambda x: x.name.lower())
            
            all_items = dirs + files
            
            for i, item in enumerate(all_items):
                is_last = i == len(all_items) - 1
                current_prefix = "└── " if is_last else "├── "
                items.append(f"{prefix}{current_prefix}{item.name}")
                
                if item.is_dir() and current_depth < max_depth - 1:
                    next_prefix = prefix + ("    " if is_last else "│   ")
                    subtree = self._build_tree_structure(item, max_depth, current_depth + 1, next_prefix)
                    if subtree:
                        items.append(subtree)
        
        except PermissionError:
            items.append(f"{prefix}[Permission Denied]")
        except Exception as e:
            items.append(f"{prefix}[Error: {str(e)}]")
        
        return "\n".join(items)
