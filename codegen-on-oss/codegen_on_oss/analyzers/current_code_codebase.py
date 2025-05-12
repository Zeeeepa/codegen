"""
Current Code Codebase Module

This module provides functionality for accessing and analyzing the current codebase.
It offers tools to create codebase objects, import modules, and collect documented objects.

The module is designed to be more self-contained with reduced dependencies on external
modules, enhanced error handling, and improved logging capabilities.
"""

import importlib
import logging
import os
from enum import Enum
from pathlib import Path
from typing import Any, TypedDict

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# Define custom exceptions for better error handling
class CodebaseError(Exception):
    """Base exception for all codebase-related errors."""

    pass


class CodebaseInitError(CodebaseError):
    """Exception raised when initializing a codebase fails.

    This exception is raised when there's an error during codebase initialization,
    such as missing projects or invalid configuration.
    """

    def __init__(self, message: str = "Initialization failed"):
        """Initialize the exception with a message.

        Args:
            message: Error message
        """
        super().__init__(message)


class ModuleImportError(CodebaseError):
    """Exception raised when importing modules fails.

    This exception is raised when there's an error during module import,
    such as missing dependencies or syntax errors.
    """

    pass


class DocumentationError(CodebaseError):
    """Exception raised when processing documentation objects fails.

    This exception is raised when there's an error during documentation processing,
    such as invalid documentation format or missing documentation objects.
    """

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
    def from_repo_path(cls, repo_path: str) -> "RepoConfig":
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

    def model_copy(self, update: dict[str, Any] | None = None) -> "CodebaseConfig":
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
        subdirectories: list[str] | None = None,
        base_path: str = "",
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
        projects: list[ProjectConfig],
        config: CodebaseConfig | None = None,
        secrets: SecretsConfig | None = None,
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

    def _validate_projects(self):
        """Validate that projects are specified."""
        if not self.projects:
            raise CodebaseInitError("Empty")

    def _initialize(self):
        """Initialize codebase properties and validate configuration."""
        try:
            # Validate projects
            self._validate_projects()

            # Set up additional properties
            self.repo_paths = [p.repo_operator.repo_path for p in self.projects]
            self.base_paths = [p.base_path for p in self.projects]

            logger.info(f"Initialized codebase with {len(self.projects)} projects")
        except Exception as e:
            logger.exception("Failed to initialize codebase")
            # Re-raise the original exception if it's already a CodebaseInitError
            if isinstance(e, CodebaseInitError):
                raise
            # Otherwise, wrap it in a CodebaseInitError
            raise CodebaseInitError() from e


# Type alias for codebase
CodebaseType = Codebase
PyCodebaseType = Codebase
TSCodebaseType = Codebase


class DocumentedObject:
    """Class representing a documented object in the codebase."""

    def __init__(self, name: str, module: str, obj: Any):
        """Initialize documented object.

        Args:
            name: Name of the documented object
            module: Module containing the documented object
            obj: The actual object being documented
        """
        self.name = name
        self.module = module
        self.obj = obj

    def __eq__(self, other):
        """Check if two documented objects are equal."""
        if not isinstance(other, DocumentedObject):
            return False
        return self.name == other.name and self.module == other.module


# Global collections for documented objects
apidoc_objects: list[DocumentedObject] = []
py_apidoc_objects: list[DocumentedObject] = []
ts_apidoc_objects: list[DocumentedObject] = []
no_apidoc_objects: list[DocumentedObject] = []


def get_repo_path() -> str:
    """Get the repository path.

    Returns:
        Path to the repository root
    """
    try:
        # Try to get the repository path from environment variables
        if "REPO_PATH" in os.environ:
            return os.environ["REPO_PATH"]

        # Fall back to current working directory
        repo_path = os.getcwd()
        logger.info(f"Using current directory as repository path: {repo_path}")
    except Exception:
        logger.exception("Error determining repository path")
        # Fall back to current directory
        repo_path = os.getcwd()

    return repo_path


def get_base_path(repo_path: str) -> str:
    """Get the base path within the repository.

    Args:
        repo_path: Path to the repository

    Returns:
        Base path within the repository where code is located
    """
    try:
        # Try to get the base path from environment variables
        if "BASE_PATH" in os.environ:
            return os.environ["BASE_PATH"]

        # Check common base paths
        common_paths = ["src", "lib", "app", "codegen"]
        for path in common_paths:
            if os.path.exists(os.path.join(repo_path, path)):
                logger.info(f"Found base path: {path}")
                return path
    except Exception:
        logger.exception("Error determining base path")
        # Fall back to empty string (repository root)
        return ""

    # Fall back to empty string (repository root)
    return ""


def detect_programming_language(
    repo_path: str, base_path: str = ""
) -> ProgrammingLanguage:
    """Detect the primary programming language of a repository.

    This function analyzes the files in the repository to determine
    the most likely primary programming language.

    Args:
        repo_path: Path to the repository
        base_path: Base directory within the repository

    Returns:
        Detected programming language (defaults to Python if detection fails)
    """
    try:
        # Get the full path to analyze
        full_path = os.path.join(repo_path, base_path) if base_path else repo_path

        # Count files by extension
        extension_counts = {}
        for _root, _, files in os.walk(full_path):
            for file in files:
                _, ext = os.path.splitext(file)
                if ext:
                    extension_counts[ext] = extension_counts.get(ext, 0) + 1

        # Map extensions to languages
        language_map = {
            ".py": ProgrammingLanguage.PYTHON,
            ".js": ProgrammingLanguage.JAVASCRIPT,
            ".ts": ProgrammingLanguage.TYPESCRIPT,
            ".tsx": ProgrammingLanguage.TYPESCRIPT,
            ".jsx": ProgrammingLanguage.JAVASCRIPT,
            ".java": ProgrammingLanguage.JAVA,
            ".go": ProgrammingLanguage.GO,
            ".rs": ProgrammingLanguage.RUST,
            ".rb": ProgrammingLanguage.RUBY,
            ".php": ProgrammingLanguage.PHP,
            ".cs": ProgrammingLanguage.CSHARP,
            ".cpp": ProgrammingLanguage.CPP,
            ".c": ProgrammingLanguage.C,
        }

        # Find the most common language
        language_counts = {}
        for ext, count in extension_counts.items():
            if ext in language_map:
                lang = language_map[ext]
                language_counts[lang] = language_counts.get(lang, 0) + count

        # Return the most common language, or Python if none found
        if language_counts:
            return max(language_counts.items(), key=lambda x: x[1])[0]
    except Exception:
        logger.exception("Error detecting programming language")

    # Default to Python on error or if no languages found
    return ProgrammingLanguage.PYTHON


def get_selected_codebase(
    repo_path: str | None = None,
    base_path: str | None = None,
    config: CodebaseConfig | None = None,
    secrets: SecretsConfig | None = None,
    programming_language: ProgrammingLanguage | None = None,
    subdirectories: list[str] | None = None,
) -> CodebaseType:
    """Returns a Codebase instance for the selected repository.

    Args:
        repo_path: Path to the repository
        base_path: Base directory within the repository where code is located
        config: CodebaseConfig instance for customizing codebase behavior
        secrets: SecretsConfig instance for providing credentials
        programming_language: Primary programming language of the repository
        subdirectories: List of subdirectories to include in the codebase

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

        logger.info(
            f"Creating codebase from repo at: {repo_path} with base_path {base_path}"
        )

        # Set up repository config
        repo_config = RepoConfig(repo_path=repo_path, respect_gitignore=True)
        op = RepoOperator(repo_config=repo_config, bot_commit=False)

        # Use provided config or create a new one
        config = (config or CodebaseConfig()).model_copy(
            update={"base_path": base_path}
        )

        # Determine the programming language if not provided
        if not programming_language:
            programming_language = detect_programming_language(repo_path, base_path)

        # Create project config
        projects = [
            ProjectConfig(
                repo_operator=op,
                programming_language=programming_language,
                subdirectories=subdirectories,
                base_path=base_path,
            )
        ]

        # Create and return codebase
        codebase = Codebase(projects=projects, config=config, secrets=secrets)
    except Exception as e:
        error_msg = f"Failed to create codebase: {e!s}"
        logger.exception("Codebase creation failed")
        raise CodebaseInitError(error_msg) from e
    else:
        return codebase


def import_modules_from_path(
    directory_path: str,
    package_prefix: str = "",
    excluded_modules: set[str] | None = None,
) -> list[str]:
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
            if (
                any(excluded in str(file) for excluded in excluded_modules)
                or "__init__" in file.name
            ):
                continue

            try:
                # Convert path to module name
                relative_path = file.relative_to(directory)
                module_name = package_prefix + str(relative_path).replace(
                    "/", "."
                ).removesuffix(".py")

                # Import the module
                importlib.import_module(module_name)
                logger.debug(f"Successfully imported module: {module_name}")
                imported_modules.append(module_name)
            except ImportError as e:
                logger.warning(f"Could not import {module_name}: {e!s}")
            except Exception:
                logger.exception(f"Error importing {module_name}")
    except Exception as e:
        error_msg = f"Failed to import modules from {directory_path}: {e!s}"
        logger.exception(error_msg)
        raise ModuleImportError(error_msg) from e
    else:
        return imported_modules


class DocumentedObjects(TypedDict):
    """Type definition for the documented objects collection."""

    apidoc: list[DocumentedObject]
    ts_apidoc: list[DocumentedObject]
    py_apidoc: list[DocumentedObject]
    no_apidoc: list[DocumentedObject]


def get_documented_objects(
    repo_path: str | None = None,
    package_prefix: str = "",
    import_paths: list[str] | None = None,
    excluded_modules: set[str] | None = None,
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
                os.path.join(repo_path, base_path, "codegen")
                if base_path
                else os.path.join(repo_path, "codegen"),
                os.path.join(repo_path, base_path, "sdk")
                if base_path
                else os.path.join(repo_path, "sdk"),
            ]

        # Import all modules to populate the documented objects lists
        imported_modules = []
        for path in import_paths:
            if os.path.exists(path) and os.path.isdir(path):
                imported_modules.extend(
                    import_modules_from_path(path, package_prefix, excluded_modules)
                )

        logger.info(
            f"Imported {len(imported_modules)} modules for documentation collection"
        )

        # Try to add core types if they aren't already added
        try:
            # First try to import from the original location
            for obj_name in ["CodebaseType", "PyCodebaseType", "TSCodebaseType"]:
                obj_exists = any(doc.name == obj_name for doc in apidoc_objects)
                if not obj_exists:
                    # Add the local version
                    apidoc_objects.append(
                        DocumentedObject(
                            name=obj_name,
                            module="codegen_on_oss.analyzers.current_code_codebase",
                            obj=globals()[obj_name],
                        )
                    )
        except Exception as e:
            logger.warning(f"Could not add core types to documented objects: {e}")
    except Exception as e:
        error_msg = f"Failed to collect documented objects: {e!s}"
        logger.exception(error_msg)
        raise DocumentationError(error_msg) from e
    else:
        # Return the collected objects in the else block
        return {
            "apidoc": apidoc_objects,
            "py_apidoc": py_apidoc_objects,
            "ts_apidoc": ts_apidoc_objects,
            "no_apidoc": no_apidoc_objects,
        }


def get_codebase_with_docs(
    repo_path: str | None = None,
    base_path: str | None = None,
    config: CodebaseConfig | None = None,
    secrets: SecretsConfig | None = None,
    programming_language: ProgrammingLanguage | None = None,
    subdirectories: list[str] | None = None,
    package_prefix: str = "",
    import_paths: list[str] | None = None,
) -> tuple[CodebaseType, DocumentedObjects]:
    """Convenience function to get both a codebase and its documented objects.

    Args:
        repo_path: Path to the repository
        base_path: Base directory within the repository
        config: CodebaseConfig instance
        secrets: SecretsConfig instance
        programming_language: Primary programming language
        subdirectories: List of subdirectories to include
        package_prefix: Prefix to use for importing modules
        import_paths: List of paths to import from

    Returns:
        A tuple containing (codebase, documented_objects)

    Raises:
        CodebaseError: If either codebase or documentation collection fails
    """
    try:
        # Get the codebase
        codebase = get_selected_codebase(
            repo_path=repo_path,
            base_path=base_path,
            config=config,
            secrets=secrets,
            programming_language=programming_language,
            subdirectories=subdirectories,
        )

        # Get the documented objects
        documented_objects = get_documented_objects(
            repo_path=repo_path,
            package_prefix=package_prefix,
            import_paths=import_paths,
        )
    except Exception as e:
        error_msg = f"Failed to get codebase with docs: {e!s}"
        logger.exception(error_msg)
        raise CodebaseError(error_msg) from e
    else:
        return codebase, documented_objects


def set_log_level(level: int = logging.INFO):
    """Set the logging level for this module.

    Args:
        level: Logging level (e.g., logging.DEBUG, logging.INFO)
    """
    logger.setLevel(level)
    for handler in logger.handlers:
        handler.setLevel(level)
