import importlib
import os
from pathlib import Path
from typing import Optional, TypedDict, Union, List

from codegen.shared.decorators.docs import DocumentedObject, apidoc_objects, no_apidoc_objects, py_apidoc_objects, ts_apidoc_objects
from codegen.sdk.core.codebase import Codebase, CodebaseType
from codegen.sdk.codebase.config import ProjectConfig
from codegen.configs.models.codebase import CodebaseConfig
from codegen.configs.models.secrets import SecretsConfig
from codegen.git.repo_operator.repo_operator import RepoOperator
from codegen.git.schemas.repo_config import RepoConfig
from codegen.shared.enums.programming_language import ProgrammingLanguage
from codegen.shared.logging.get_logger import get_logger

logger = get_logger(__name__)


def get_repo_path() -> str:
    """Returns the base directory path of the repository being analyzed.
    If not explicitly provided, defaults to the current directory.
    """
    # Default to current directory if not specified
    return os.getcwd()


def get_base_path(repo_path: str) -> str:
    """Determines the base path within the repository.
    For monorepos this might be a subdirectory, for simple repos it's the root.
    """
    # Check if there's a src directory, which is a common pattern
    if os.path.isdir(os.path.join(repo_path, "src")):
        return "src"
    return ""


def get_selected_codebase(
    repo_path: Optional[str] = None,
    base_path: Optional[str] = None,
    config: Optional[CodebaseConfig] = None,
    secrets: Optional[SecretsConfig] = None, 
    subdirectories: Optional[List[str]] = None,
    programming_language: Optional[ProgrammingLanguage] = None
) -> CodebaseType:
    """Returns a Codebase instance for the selected repository.
    
    Parameters:
        repo_path: Path to the repository
        base_path: Base directory within the repository where code is located
        config: CodebaseConfig instance for customizing codebase behavior
        secrets: SecretsConfig for any credentials needed
        subdirectories: List of subdirectories to include in the analysis
        programming_language: Primary programming language of the codebase
        
    Returns:
        A Codebase instance initialized with the provided parameters
    """
    if not repo_path:
        repo_path = get_repo_path()
    
    if not base_path:
        base_path = get_base_path(repo_path)
    
    logger.info(f"Creating codebase from repo at: {repo_path} with base_path {base_path}")
    
    # Set up repository config
    repo_config = RepoConfig.from_repo_path(repo_path)
    repo_config.respect_gitignore = True  # Respect gitignore by default
    op = RepoOperator(repo_config=repo_config, bot_commit=False)
    
    # Use provided config or create a new one
    config = (config or CodebaseConfig()).model_copy(update={"base_path": base_path})
    
    # Determine the programming language if not provided
    if not programming_language:
        # Default to Python, but try to detect from files
        programming_language = ProgrammingLanguage.PYTHON
        # TODO: Add language detection logic if needed
    
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


def import_modules_from_path(directory_path: str, package_prefix: str = ""):
    """Imports all Python modules from the given directory path.
    
    This is used to collect all documented objects from the modules.
    
    Parameters:
        directory_path: Path to the directory containing Python modules
        package_prefix: Prefix to use for module imports (e.g., 'mypackage.')
    """
    directory = Path(directory_path)
    if not directory.exists() or not directory.is_dir():
        logger.warning(f"Directory does not exist: {directory_path}")
        return
    
    for file in directory.rglob("*.py"):
        if "__init__" in file.name or "braintrust_evaluator" in file.name:
            continue
            
        try:
            # Convert path to module name
            relative_path = file.relative_to(directory)
            module_name = package_prefix + str(relative_path).replace("/", ".").removesuffix(".py")
            
            # Import the module
            importlib.import_module(module_name)
            logger.debug(f"Successfully imported module: {module_name}")
        except Exception as e:
            logger.error(f"Error importing {module_name}: {e}")


class DocumentedObjects(TypedDict):
    """Type definition for the documented objects collection."""
    apidoc: list[DocumentedObject]
    ts_apidoc: list[DocumentedObject]
    py_apidoc: list[DocumentedObject]
    no_apidoc: list[DocumentedObject]


def get_documented_objects(
    repo_path: Optional[str] = None,
    package_prefix: str = "",
    import_paths: Optional[List[str]] = None
) -> DocumentedObjects:
    """Get all objects decorated with API documentation decorators.
    
    This function imports modules from the specified paths and collects
    objects decorated with apidoc, py_apidoc, ts_apidoc, and no_apidoc.
    
    Parameters:
        repo_path: Path to the repository root
        package_prefix: Prefix to use for importing modules
        import_paths: List of paths to import from
        
    Returns:
        A dictionary containing the collected documented objects
    """
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
    for path in import_paths:
        if os.path.exists(path) and os.path.isdir(path):
            import_modules_from_path(path, package_prefix)
    
    # Add core types if they aren't already added
    from codegen.sdk.core.codebase import CodebaseType, PyCodebaseType, TSCodebaseType
    
    if CodebaseType not in apidoc_objects:
        apidoc_objects.append(DocumentedObject(name="CodebaseType", module="codegen.sdk.core.codebase", object=CodebaseType))
    if PyCodebaseType not in apidoc_objects:
        apidoc_objects.append(DocumentedObject(name="PyCodebaseType", module="codegen.sdk.core.codebase", object=PyCodebaseType))
    if TSCodebaseType not in apidoc_objects:
        apidoc_objects.append(DocumentedObject(name="TSCodebaseType", module="codegen.sdk.core.codebase", object=TSCodebaseType))
    
    # Return the collected objects
    return {
        "apidoc": apidoc_objects,
        "py_apidoc": py_apidoc_objects,
        "ts_apidoc": ts_apidoc_objects,
        "no_apidoc": no_apidoc_objects
    }


def get_codebase_with_docs(
    repo_path: Optional[str] = None,
    base_path: Optional[str] = None,
    config: Optional[CodebaseConfig] = None,
    secrets: Optional[SecretsConfig] = None,
    subdirectories: Optional[List[str]] = None,
    programming_language: Optional[ProgrammingLanguage] = None,
    package_prefix: str = "",
    import_paths: Optional[List[str]] = None
) -> tuple[CodebaseType, DocumentedObjects]:
    """Convenience function to get both a codebase and its documented objects.
    
    Parameters:
        repo_path: Path to the repository
        base_path: Base directory within the repository
        config: CodebaseConfig instance
        secrets: SecretsConfig instance
        subdirectories: List of subdirectories to include
        programming_language: Primary programming language of the codebase
        package_prefix: Prefix for importing modules
        import_paths: List of paths to import from
        
    Returns:
        A tuple containing the Codebase instance and the documented objects
    """
    if not repo_path:
        repo_path = get_repo_path()
    
    codebase = get_selected_codebase(
        repo_path=repo_path,
        base_path=base_path,
        config=config,
        secrets=secrets,
        subdirectories=subdirectories,
        programming_language=programming_language
    )
    
    documented_objects = get_documented_objects(
        repo_path=repo_path,
        package_prefix=package_prefix,
        import_paths=import_paths
    )
    
    return codebase, documented_objects