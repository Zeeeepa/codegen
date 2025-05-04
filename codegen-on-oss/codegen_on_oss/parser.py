import gc
import sys
import traceback
from pathlib import Path
from typing import TYPE_CHECKING, Dict, Any, Optional, Tuple
from urllib.parse import urlparse

from codegen import Codebase
from codegen.sdk.codebase.validation import (
    PostInitValidationStatus,
    post_init_validation,
)
from codegen.sdk.extensions.utils import uncache_all
from loguru import logger

from codegen_on_oss.errors import PostValidationError
from codegen_on_oss.metrics import MetricsProfiler

if TYPE_CHECKING:
    from codegen.sdk.codebase.config import ProjectConfig


class CodegenParser:
    """
    Parser for codegen repositories.
    
    This class handles parsing repositories using the Codegen SDK and provides
    error handling and metrics profiling.
    
    Attributes:
        repo_dir: Directory where repositories are stored
        metrics_profiler: Profiler for measuring performance metrics
    """
    
    if TYPE_CHECKING:
        repo_dir: Path
        metrics_profiler: MetricsProfiler

    def __init__(self, repo_dir: Path, metrics_profiler: MetricsProfiler):
        """
        Initialize the CodegenParser.
        
        Args:
            repo_dir: Directory where repositories will be stored
            metrics_profiler: Profiler for measuring performance metrics
        """
        self.repo_dir = repo_dir
        self.repo_dir.mkdir(parents=True, exist_ok=True)
        self.metrics_profiler = metrics_profiler
        sys.setrecursionlimit(10000000)

    def parse(self, url: str, language: str | None = None, commit_hash: str | None = None) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """
        Parse the repository at the given URL. MetricsProfiler is used to profile the parse and
        post_init_validation.

        Args:
            url: The URL of the repository to parse
            language: The programming language of the repository
            commit_hash: The commit hash to parse. If None, the head commit will be used

        Returns:
            Tuple containing:
                - Success status (bool)
                - Metrics data (Dict or None if failed)
                - Error message (str or None if successful)
        """
        repo_name = urlparse(url).path.removeprefix("/").removesuffix(".git")
        repo_dest_path = Path(*repo_name.split("/"))
        repo_dest_path = self.repo_dir / repo_dest_path
        repo_logger = logger.bind(repo_name=repo_name)

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
                        profile.revision = (
                            profile.revision
                            or projects[0].repo_operator.head_commit  # assume projects is not empty
                        )
                        # from_repo would have performed any repo initialization necessary
                        # It could pull or use cached
                        profile.reset_checkpoint()
                        try:
                            super().__init__(*args, projects=projects, **kwargs)
                            profile.language = profile.language or str(self.language).lower()
                            profile.measure("codebase_parse")
                            validation_status = post_init_validation(self)

                            profile.measure("post_init_validation")
                            if validation_status is PostInitValidationStatus.SUCCESS:
                                return
                            else:
                                raise PostValidationError(validation_status)
                        except Exception as e:
                            repo_logger.error(f"Error during codebase initialization: {str(e)}")
                            raise

                codebase = ProfiledCodebase.from_repo(
                    repo_name, tmp_dir=str(self.repo_dir.absolute()), commit=commit_hash
                )
                
                # If we got here, parsing was successful
                return True, profile.data, None
                
        except PostValidationError as e:
            error_msg = f"Post-validation failed: {str(e)}"
            repo_logger.error(error_msg)
            return False, None, error_msg
        except Exception as e:
            error_msg = f"Error parsing repository: {str(e)}\n{traceback.format_exc()}"
            repo_logger.error(error_msg)
            return False, None, error_msg

    def gc(self):
        """
        Perform garbage collection to free memory.
        """
        uncache_all()
        gc.collect()
