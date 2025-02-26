import logging

from codeowners import CodeOwners

from codegen.git.clients.git_repo_client import GitRepoClient
from codegen.git.configs.constants import CODEOWNERS_FILEPATHS

logger = logging.getLogger(__name__)


def create_codeowners_parser_for_repo(py_github_repo: GitRepoClient) -> CodeOwners | None:
    for codeowners_filepath in CODEOWNERS_FILEPATHS:
        try:
            codeowner_file_contents = py_github_repo.get_contents(codeowners_filepath)
            if codeowner_file_contents:
                codeowners = CodeOwners(codeowner_file_contents)
                return codeowners
        except Exception as e:
            continue
    logger.info(f"Failed to create CODEOWNERS parser for repo: {py_github_repo.repo_config.name}. Returning None.")
    return None
