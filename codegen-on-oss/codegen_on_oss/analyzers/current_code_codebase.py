"""
Current Code Codebase Module

This module provides functionality for accessing and analyzing the current codebase.
It offers tools to create codebase objects, import modules, and collect documented objects.

The module is designed to be more self-contained with reduced dependencies on external
modules, enhanced error handling, and improved logging capabilities.
"""

import importlib
import os
import sys
import logging
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, TypedDict, Union, cast
import traceback

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define custom exceptions for better error handling
class CodebaseError(Exception):
    """Base exception for all codebase-related errors."""
    pass

class CodebaseInitError(CodebaseError):
    """Exception raised when initializing a codebase fails."""
    pass

class ModuleImportError(CodebaseError):
    """Exception raised when importing modules fails."""
    pass

class DocumentationError(CodebaseError):
    """Exception raised when processing documentation objects fails."""
    pass

# Define programming language enum locally to reduce dependencies
class ProgrammingLanguage(str, Enum):
    """Programming language enum with common languages."""
    PYTHON = "python"
    TYPESCRIPT = "typescript"
    JAVASCRIPT = "javascript"
    JAVA = "java"
    GO = "go"
    RUST = "rust"
    CPP = "cpp"
    CSHARP = "csharp"
    RUBY = "ruby"
    PHP = "php"
    SWIFT = "swift"
    KOTLIN = "kotlin"
    UNKNOWN = "unknown"

# Type definitions for better type checking
class RepoConfig:
    """Repository configuration class."""
    
    def __init__(self, repo_path: str, respect_gitignore: bool = True):
        """Initialize repository configuration.
        
        Args:
            repo_path: Path to the repository
            respect_gitignore: Whether to respect .gitignore files
        """
        self.repo_path = repo_path
        self.respect_gitignore = respect_gitignore
    
    @classmethod
    def from_repo_path(cls, repo_path: str) -> 'RepoConfig':
        """Create a RepoConfig instance from a repository path.
        
        Args:
            repo_path: Path to the repository
            
        Returns:
            A RepoConfig instance
        """
        return cls(repo_path=repo_path)

class RepoOperator:
    """Repository operator class for interacting with Git repositories."""
    
    def __init__(self, repo_config: RepoConfig, bot_commit: bool = False):
        """Initialize repository operator.
        
        Args:
            repo_config: Repository configuration
            bot_commit: Whether commits should be made by a bot
        """
        self.repo_config = repo_config
        self.bot_commit = bot_commit
        self.repo_path = repo_config.repo_path

class CodebaseConfig:
    """Configuration for codebase analysis."""
    
    def __init__(self, base_path: str = "", **kwargs):
        """Initialize codebase configuration.
        
        Args:
            base_path: Base path within the repository
            **kwargs: Additional configuration options
        """
        self.base_path = base_path
        self.options = kwargs
    
    def model_copy(self, update: Dict[str, Any] = None) -> 'CodebaseConfig':
        """Create a copy of this configuration with updated values.
        
        Args:
            update: Dictionary of values to update
            
        Returns:
            A new CodebaseConfig instance with updated values
        """
        if update is None:
            update = {}
        
        new_config = CodebaseConfig(base_path=self.base_path, **self.options)
        for key, value in update.items():
            setattr(new_config, key, value)
        
        return new_config

class SecretsConfig:
    """Configuration for secrets and credentials."""
    
    def __init__(self, **kwargs):
        """Initialize secrets configuration.
        
        Args:
            **kwargs: Secret configuration options
        """
        self.secrets = kwargs

class ProjectConfig:
    """Configuration for a project within a codebase."""
    
    def __init__(
        self,
        repo_operator: RepoOperator,
        programming_language: ProgrammingLanguage = ProgrammingLanguage.PYTHON,
        subdirectories: Optional[List[str]] = None,
        base_path: str = ""
    ):
        """Initialize project configuration.
        
        Args:
            repo_operator: Repository operator for the project
            programming_language: Primary programming language of the project
            subdirectories: List of subdirectories to include
            base_path: Base path within the repository
        """
        self.repo_operator = repo_operator
        self.programming_language = programming_language
        self.subdirectories = subdirectories or []
        self.base_path = base_path

class Codebase:
    """Codebase class for analyzing and interacting with code repositories."""
    
    def __init__(
        self,
        projects: List[ProjectConfig],
        config: Optional[CodebaseConfig] = None,
        secrets: Optional[SecretsConfig] = None
    ):
        """Initialize codebase.
        
        Args:
            projects: List of project configurations
            config: Codebase configuration
            secrets: Secrets configuration
        """
        self.projects = projects
        self.config = config or CodebaseConfig()
        self.secrets = secrets or SecretsConfig()
        
        # Initialize codebase properties
        self._initialize()
    
    def _initialize(self):
        """Initialize codebase properties and validate configuration."""
        try:
            # Validate projects
            if not self.projects:
                raise CodebaseInitError("No projects specified for codebase")
            
            # Set up additional properties
            self.repo_paths = [p.repo_operator.repo_path for p in self.projects]
            self.base_paths = [p.base_path for p in self.projects]
            
            logger.info(f"Initialized codebase with {len(self.projects)} projects")
        except Exception as e:
            logger.error(f"Failed to initialize codebase: {str(e)}")
            raise CodebaseInitError(f"Failed to initialize codebase: {str(e)}") from e

# Type alias for codebase
CodebaseType = Codebase
PyCodebaseType = Codebase
TSCodebaseType = Codebase

class DocumentedObject:
    """Class representing a documented object in the codebase."""
    
    def __init__(self, name: str, module: str, object: Any):
        """Initialize documented object.
        
        Args:
            name: Name of the object
            module: Module containing the object
            object: The actual object
        """
        self.name = name
        self.module = module
        self.object = object
    
    def __eq__(self, other):
        """Check if two documented objects are equal."""
        if not isinstance(other, DocumentedObject):
            return False
        return self.name == other.name and self.module == other.module

# Global collections for documented objects
apidoc_objects: List[DocumentedObject] = []
py_apidoc_objects: List[DocumentedObject] = []
ts_apidoc_objects: List[DocumentedObject] = []
no_apidoc_objects: List[DocumentedObject] = []

def get_repo_path() -> str:
    """Returns the base directory path of the repository being analyzed.
    If not explicitly provided, defaults to the current directory.
    
    Returns:
        The repository path
    """
    try:
        # Default to current directory if not specified
        repo_path = os.getcwd()
        logger.debug(f"Using repository path: {repo_path}")
        return repo_path
    except Exception as e:
        logger.error(f"Error determining repository path: {str(e)}")
        # Fall back to current directory
        return os.getcwd()

def get_base_path(repo_path: str) -> str:
    """Determines the base path within the repository.
    For monorepos this might be a subdirectory, for simple repos it's the root.
    
    Args:
        repo_path: Path to the repository
        
    Returns:
        The base path within the repository
    """
    try:
        # Check if there's a src directory, which is a common pattern
        if os.path.isdir(os.path.join(repo_path, "src")):
            logger.debug(f"Found 'src' directory in {repo_path}")
            return "src"
        
        # Check for other common patterns
        for common_dir in ["source", "lib", "app"]:
            if os.path.isdir(os.path.join(repo_path, common_dir)):
                logger.debug(f"Found '{common_dir}' directory in {repo_path}")
                return common_dir
        
        logger.debug(f"No common source directory found in {repo_path}, using root")
        return ""
    except Exception as e:
        logger.error(f"Error determining base path: {str(e)}")
        # Fall back to empty string (repository root)
        return ""

def detect_programming_language(repo_path: str, base_path: str = "") -> ProgrammingLanguage:
    """Detect the primary programming language of a repository.
    
    Args:
        repo_path: Path to the repository
        base_path: Base path within the repository
        
    Returns:
        The detected programming language
    """
    try:
        full_path = os.path.join(repo_path, base_path)
        
        # Count files by extension
        extension_counts: Dict[str, int] = {}
        
        for root, _, files in os.walk(full_path):
            for file in files:
                _, ext = os.path.splitext(file)
                if ext:
                    extension_counts[ext] = extension_counts.get(ext, 0) + 1
        
        # Map extensions to languages
        extension_to_language = {
            '.py': ProgrammingLanguage.PYTHON,
            '.ts': ProgrammingLanguage.TYPESCRIPT,
            '.tsx': ProgrammingLanguage.TYPESCRIPT,
            '.js': ProgrammingLanguage.JAVASCRIPT,
            '.jsx': ProgrammingLanguage.JAVASCRIPT,
            '.java': ProgrammingLanguage.JAVA,
            '.go': ProgrammingLanguage.GO,
            '.rs': ProgrammingLanguage.RUST,
            '.cpp': ProgrammingLanguage.CPP,
            '.cc': ProgrammingLanguage.CPP,
            '.c': ProgrammingLanguage.CPP,
            '.cs': ProgrammingLanguage.CSHARP,
            '.rb': ProgrammingLanguage.RUBY,
            '.php': ProgrammingLanguage.PHP,
            '.swift': ProgrammingLanguage.SWIFT,
            '.kt': ProgrammingLanguage.KOTLIN,
        }
        
        # Find the most common language
        language_counts: Dict[ProgrammingLanguage, int] = {}
        
        for ext, count in extension_counts.items():
            if ext in extension_to_language:
                lang = extension_to_language[ext]
                language_counts[lang] = language_counts.get(lang, 0) + count
        
        if language_counts:
            # Return the most common language
            most_common_language = max(language_counts.items(), key=lambda x: x[1])[0]
            logger.info(f"Detected programming language: {most_common_language}")
            return most_common_language
        
        # Default to Python if no language detected
        logger.info("No programming language detected, defaulting to Python")
        return ProgrammingLanguage.PYTHON
    except Exception as e:
        logger.error(f"Error detecting programming language: {str(e)}")
        # Default to Python on error
        return ProgrammingLanguage.PYTHON

def get_selected_codebase(
    repo_path: Optional[str] = None,
    base_path: Optional[str] = None,
    config: Optional[CodebaseConfig] = None,
    secrets: Optional[SecretsConfig] = None, 
    subdirectories: Optional[List[str]] = None,
    programming_language: Optional[ProgrammingLanguage] = None
) -> CodebaseType:
    """Returns a Codebase instance for the selected repository.
    
    Args:
        repo_path: Path to the repository
        base_path: Base directory within the repository where code is located
        config: CodebaseConfig instance for customizing codebase behavior
        secrets: SecretsConfig for any credentials needed
        subdirectories: List of subdirectories to include in the analysis
        programming_language: Primary programming language of the codebase
        
    Returns:
        A Codebase instance initialized with the provided parameters
        
    Raises:
        CodebaseInitError: If codebase initialization fails
    """
    try:
        if not repo_path:
            repo_path = get_repo_path()
        
        if not base_path:
            base_path = get_base_path(repo_path)
        
        logger.info(f"Creating codebase from repo at: {repo_path} with base_path {base_path}")
        
        # Set up repository config
        repo_config = RepoConfig(repo_path=repo_path, respect_gitignore=True)
        op = RepoOperator(repo_config=repo_config, bot_commit=False)
        
        # Use provided config or create a new one
        config = (config or CodebaseConfig()).model_copy(update={"base_path": base_path})
        
        # Determine the programming language if not provided
        if not programming_language:
            programming_language = detect_programming_language(repo_path, base_path)
        
        # Create project config
        projects = [
            ProjectConfig(
                repo_operator=op,
                programming_language=programming_language,
                subdirectories=subdirectories,
                base_path=base_path
            )
        ]
        
        # Create and return codebase
        codebase = Codebase(projects=projects, config=config, secrets=secrets)
        return codebase
    except Exception as e:
        error_msg = f"Failed to create codebase: {str(e)}"
        logger.error(error_msg)
        logger.debug(f"Traceback: {traceback.format_exc()}")
        raise CodebaseInitError(error_msg) from e

def import_modules_from_path(
    directory_path: str,
    package_prefix: str = "",
    excluded_modules: Optional[Set[str]] = None
) -> List[str]:
    """Imports all Python modules from the given directory path.
    
    This is used to collect all documented objects from the modules.
    
    Args:
        directory_path: Path to the directory containing Python modules
        package_prefix: Prefix to use for module imports (e.g., 'mypackage.')
        excluded_modules: Set of module names to exclude from importing
        
    Returns:
        List of successfully imported module names
        
    Raises:
        ModuleImportError: If module importing fails critically
    """
    if excluded_modules is None:
        excluded_modules = set()
    
    # Add common modules to exclude
    excluded_modules.update(["__pycache__", "braintrust_evaluator"])
    
    imported_modules = []
    directory = Path(directory_path)
    
    if not directory.exists() or not directory.is_dir():
        logger.warning(f"Directory does not exist: {directory_path}")
        return imported_modules
    
    try:
        for file in directory.rglob("*.py"):
            # Skip __init__.py and excluded modules
            if any(excluded in str(file) for excluded in excluded_modules) or "__init__" in file.name:
                continue
                
            try:
                # Convert path to module name
                relative_path = file.relative_to(directory)
                module_name = package_prefix + str(relative_path).replace("/", ".").removesuffix(".py")
                
                # Import the module
                importlib.import_module(module_name)
                logger.debug(f"Successfully imported module: {module_name}")
                imported_modules.append(module_name)
            except ImportError as e:
                logger.warning(f"Could not import {module_name}: {str(e)}")
            except Exception as e:
                logger.error(f"Error importing {module_name}: {str(e)}")
        
        return imported_modules
    except Exception as e:
        error_msg = f"Failed to import modules from {directory_path}: {str(e)}"
        logger.error(error_msg)
        logger.debug(f"Traceback: {traceback.format_exc()}")
        raise ModuleImportError(error_msg) from e

class DocumentedObjects(TypedDict):
    """Type definition for the documented objects collection."""
    apidoc: List[DocumentedObject]
    ts_apidoc: List[DocumentedObject]
    py_apidoc: List[DocumentedObject]
    no_apidoc: List[DocumentedObject]

def get_documented_objects(
    repo_path: Optional[str] = None,
    package_prefix: str = "",
    import_paths: Optional[List[str]] = None,
    excluded_modules: Optional[Set[str]] = None
) -> DocumentedObjects:
    """Get all objects decorated with API documentation decorators.
    
    This function imports modules from the specified paths and collects
    objects decorated with apidoc, py_apidoc, ts_apidoc, and no_apidoc.
    
    Args:
        repo_path: Path to the repository root
        package_prefix: Prefix to use for importing modules
        import_paths: List of paths to import from
        excluded_modules: Set of module names to exclude from importing
        
    Returns:
        A dictionary containing the collected documented objects
        
    Raises:
        DocumentationError: If documentation collection fails critically
    """
    try:
        if not repo_path:
            repo_path = get_repo_path()
        
        if not import_paths:
            # Default to importing from common directories
            base_path = get_base_path(repo_path)
            import_paths = [
                os.path.join(repo_path, base_path),
                os.path.join(repo_path, base_path, "codegen") if base_path else os.path.join(repo_path, "codegen"),
                os.path.join(repo_path, base_path, "sdk") if base_path else os.path.join(repo_path, "sdk"),
            ]
        
        # Import all modules to populate the documented objects lists
        imported_modules = []
        for path in import_paths:
            if os.path.exists(path) and os.path.isdir(path):
                imported_modules.extend(import_modules_from_path(path, package_prefix, excluded_modules))
        
        logger.info(f"Imported {len(imported_modules)} modules for documentation collection")
        
        # Try to add core types if they aren't already added
        try:
            # First try to import from codegen SDK if available
            try:
                from codegen.sdk.core.codebase import CodebaseType as SDKCodebaseType
                from codegen.sdk.core.codebase import PyCodebaseType as SDKPyCodebaseType
                from codegen.sdk.core.codebase import TSCodebaseType as SDKTSCodebaseType
                
                # Add core types if they aren't already added
                if not any(obj.name == "CodebaseType" for obj in apidoc_objects):
                    apidoc_objects.append(DocumentedObject(name="CodebaseType", module="codegen.sdk.core.codebase", object=SDKCodebaseType))
                if not any(obj.name == "PyCodebaseType" for obj in apidoc_objects):
                    apidoc_objects.append(DocumentedObject(name="PyCodebaseType", module="codegen.sdk.core.codebase", object=SDKPyCodebaseType))
                if not any(obj.name == "TSCodebaseType" for obj in apidoc_objects):
                    apidoc_objects.append(DocumentedObject(name="TSCodebaseType", module="codegen.sdk.core.codebase", object=SDKTSCodebaseType))
            except ImportError:
                # If SDK is not available, use our local types
                if not any(obj.name == "CodebaseType" for obj in apidoc_objects):
                    apidoc_objects.append(DocumentedObject(name="CodebaseType", module="codegen_on_oss.analyzers.current_code_codebase", object=CodebaseType))
                if not any(obj.name == "PyCodebaseType" for obj in apidoc_objects):
                    apidoc_objects.append(DocumentedObject(name="PyCodebaseType", module="codegen_on_oss.analyzers.current_code_codebase", object=PyCodebaseType))
                if not any(obj.name == "TSCodebaseType" for obj in apidoc_objects):
                    apidoc_objects.append(DocumentedObject(name="TSCodebaseType", module="codegen_on_oss.analyzers.current_code_codebase", object=TSCodebaseType))
        except Exception as e:
            logger.warning(f"Could not add core codebase types: {str(e)}")
        
        # Return the collected objects
        return {
            "apidoc": apidoc_objects,
            "py_apidoc": py_apidoc_objects,
            "ts_apidoc": ts_apidoc_objects,
            "no_apidoc": no_apidoc_objects
        }
    except Exception as e:
        error_msg = f"Failed to collect documented objects: {str(e)}"
        logger.error(error_msg)
        logger.debug(f"Traceback: {traceback.format_exc()}")
        raise DocumentationError(error_msg) from e

def get_codebase_with_docs(
    repo_path: Optional[str] = None,
    base_path: Optional[str] = None,
    config: Optional[CodebaseConfig] = None,
    secrets: Optional[SecretsConfig] = None,
    subdirectories: Optional[List[str]] = None,
    programming_language: Optional[ProgrammingLanguage] = None,
    package_prefix: str = "",
    import_paths: Optional[List[str]] = None,
    excluded_modules: Optional[Set[str]] = None
) -> Tuple[CodebaseType, DocumentedObjects]:
    """Convenience function to get both a codebase and its documented objects.
    
    Args:
        repo_path: Path to the repository
        base_path: Base directory within the repository
        config: CodebaseConfig instance
        secrets: SecretsConfig instance
        subdirectories: List of subdirectories to include
        programming_language: Primary programming language of the codebase
        package_prefix: Prefix for importing modules
        import_paths: List of paths to import from
        excluded_modules: Set of module names to exclude from importing
        
    Returns:
        A tuple containing the Codebase instance and the documented objects
        
    Raises:
        CodebaseError: If either codebase creation or documentation collection fails
    """
    try:
        if not repo_path:
            repo_path = get_repo_path()
        
        # Get codebase
        codebase = get_selected_codebase(
            repo_path=repo_path,
            base_path=base_path,
            config=config,
            secrets=secrets,
            subdirectories=subdirectories,
            programming_language=programming_language
        )
        
        # Get documented objects
        documented_objects = get_documented_objects(
            repo_path=repo_path,
            package_prefix=package_prefix,
            import_paths=import_paths,
            excluded_modules=excluded_modules
        )
        
        return codebase, documented_objects
    except Exception as e:
        error_msg = f"Failed to get codebase with docs: {str(e)}"
        logger.error(error_msg)
        logger.debug(f"Traceback: {traceback.format_exc()}")
        raise CodebaseError(error_msg) from e

def set_log_level(level: int = logging.INFO):
    """Set the logging level for this module.
    
    Args:
        level: Logging level (e.g., logging.DEBUG, logging.INFO)
    """
    logger.setLevel(level)
    for handler in logger.handlers:
        handler.setLevel(level)

