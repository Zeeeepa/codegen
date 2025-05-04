import gc
import os
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Optional
from urllib.parse import urlparse

from codegen import Codebase
from codegen.sdk.codebase.validation import (
    PostInitValidationStatus,
    post_init_validation,
)
from codegen.sdk.extensions.utils import uncache_all
from loguru import logger

from codegen_on_oss.errors import (
    InvalidInputError,
    PostValidationError,
    RepositoryError,
)
from codegen_on_oss.metrics import MetricsProfiler

if TYPE_CHECKING:
    from codegen.sdk.codebase.config import ProjectConfig


class CodegenParser:
    if TYPE_CHECKING:
        repo_dir: Path
        metrics_profiler: MetricsProfiler

    def __init__(self, repo_dir: Path, metrics_profiler: MetricsProfiler):
        """
        Initialize the CodegenParser.

        Args:
            repo_dir: Directory where repositories will be cloned
            metrics_profiler: Profiler for measuring performance metrics

        Raises:
            InvalidInputError: If repo_dir is not a valid path or metrics_profiler is None
        """
        if not repo_dir:
            raise InvalidInputError("Repository directory cannot be None", "repo_dir")
        if not metrics_profiler:
            raise InvalidInputError("Metrics profiler cannot be None", "metrics_profiler")

        self.repo_dir = repo_dir
        self.repo_dir.mkdir(parents=True, exist_ok=True)
        self.metrics_profiler = metrics_profiler
        sys.setrecursionlimit(10000000)
        logger.debug(f"Initialized CodegenParser with repo_dir: {repo_dir}")

    def parse(self, url: str, language: str | None = None, commit_hash: str | None = None):
        """
        Parse the repository at the given URL. MetricsProfiler is used to profile the parse and
        post_init_validation.

        Args:
            url (str): The URL of the repository to parse.
            language (str | None): The programming language of the repository.
            commit_hash (str | None): The commit hash to parse. If None, the head commit will be used.

        Raises:
            InvalidInputError: If the URL is invalid or empty
            RepositoryError: If there's an error accessing or cloning the repository
            PostValidationError: If post-validation fails
        """
        # Validate inputs
        if not url:
            raise InvalidInputError("Repository URL cannot be empty", "url")
        
        try:
            parsed_url = urlparse(url)
            if not parsed_url.scheme and not parsed_url.path:
                raise InvalidInputError("Invalid repository URL format", "url")
        except Exception as e:
            raise InvalidInputError(f"Failed to parse URL: {str(e)}", "url")

        repo_name = urlparse(url).path.removeprefix("/").removesuffix(".git")
        repo_dest_path = Path(*repo_name.split("/"))
        repo_dest_path = self.repo_dir / repo_dest_path
        repo_logger = logger.bind(repo_name=repo_name)

        repo_logger.info(f"Starting to parse repository: {repo_name}")
        if commit_hash:
            repo_logger.info(f"Using commit hash: {commit_hash}")
        if language:
            repo_logger.info(f"Using language: {language}")

        self.gc()

        try:
            with self.metrics_profiler.start_profiler(
                name=repo_name, revision=commit_hash, language=language, logger=repo_logger
            ) as profile:
                # Awkward design here is due to adapting to using Codebase.from_repo() and parsing done in __init__.
                # May want to consider  __init__ with parsed state from a separate input handling / parser class.
                class ProfiledCodebase(Codebase):
                    def __init__(self, *args, projects: "list[ProjectConfig]", **kwargs):
                        # Since Codebase is performing git ops, we need to extract commit if it wasn't explicitly provided.
                        try:
                            profile.revision = (
                                profile.revision
                                or projects[0].repo_operator.head_commit  # assume projects is not empty
                            )
                            # from_repo would have performed any repo initialization necessary
                            # It could pull or use cached
                            profile.reset_checkpoint()
                            super().__init__(*args, projects=projects, **kwargs)
                            profile.language = profile.language or str(self.language).lower()
                            profile.measure("codebase_parse")
                            validation_status = post_init_validation(self)

                            profile.measure("post_init_validation")
                            if validation_status is PostInitValidationStatus.SUCCESS:
                                repo_logger.info(f"Successfully parsed repository: {repo_name}")
                                return
                            else:
                                error_msg = f"Post-validation failed with status: {validation_status}"
                                repo_logger.error(error_msg)
                                raise PostValidationError(validation_status, error_msg)
                        except Exception as e:
                            if not isinstance(e, PostValidationError):
                                repo_logger.exception(f"Error during codebase initialization: {str(e)}")
                                raise RepositoryError(f"Failed to initialize codebase: {str(e)}")
                            raise

                try:
                    ProfiledCodebase.from_repo(
                        repo_name, tmp_dir=str(self.repo_dir.absolute()), commit=commit_hash
                    )
                except Exception as e:
                    if "Could not resolve host" in str(e):
                        repo_logger.error(f"Network error while accessing repository: {str(e)}")
                        raise RepositoryError(f"Network error: {str(e)}")
                    elif "does not exist" in str(e) or "not found" in str(e).lower():
                        repo_logger.error(f"Repository not found: {str(e)}")
                        raise RepositoryError(f"Repository not found: {str(e)}")
                    elif "authentication" in str(e).lower():
                        repo_logger.error(f"Authentication error: {str(e)}")
                        raise RepositoryError(f"Authentication error: {str(e)}")
                    else:
                        repo_logger.exception(f"Error parsing repository: {str(e)}")
                        raise RepositoryError(f"Failed to parse repository: {str(e)}")
        except Exception as e:
            if not isinstance(e, (InvalidInputError, RepositoryError, PostValidationError)):
                repo_logger.exception(f"Unexpected error during parsing: {str(e)}")
                raise RepositoryError(f"Unexpected error: {str(e)}")
            raise

    def gc(self):
        """
        Perform garbage collection to free memory.
        """
        logger.debug("Performing garbage collection")
        uncache_all()
        gc.collect()
