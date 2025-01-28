import logging
import sys

import sentry_sdk
from git import Commit as GitCommit

from codegen.git.repo_operator.remote_repo_operator import RemoteRepoOperator
from codegen.git.schemas.github import GithubType
from codegen.git.schemas.repo_config import RepoConfig
from codegen.runner.models.apis import CreateBranchRequest, CreateBranchResponse, GetDiffRequest, GetDiffResponse
from codegen.runner.models.configs import get_codebase_config
from codegen.runner.sandbox.executor import SandboxExecutor
from codegen.sdk.codebase.config import ProjectConfig, SessionOptions
from codegen.sdk.codebase.factory.codebase_factory import CodebaseType
from codegen.sdk.core.codebase import Codebase
from codegen.sdk.enums import ProgrammingLanguage
from codegen.shared.compilation.string_to_code import create_execute_function_from_codeblock
from codegen.shared.performance.stopwatch_utils import stopwatch

logger = logging.getLogger(__name__)


class SandboxRunner:
    """Responsible for orchestrating the lifecycle of a warmed sandbox"""

    # =====[ __init__ instance attributes ]=====
    container_id: str
    repo: RepoConfig
    commit: GitCommit
    op: RemoteRepoOperator | None

    # =====[ computed instance attributes ]=====
    codebase: CodebaseType
    executor: SandboxExecutor

    def __init__(
        self,
        container_id: str,
        repo_config: RepoConfig,
    ) -> None:
        self.container_id = container_id
        self.repo = repo_config
        self.op = RemoteRepoOperator(repo_config, base_dir=repo_config.base_dir, github_type=GithubType.Github)
        self.commit = self.op.git_cli.head.commit

    async def warmup(self) -> None:
        """Warms up this runner by cloning the repo and parsing the graph."""
        logger.info(f"===== Warming runner for {self.repo.full_name} (ID={self.repo.id}) =====")
        sys.setrecursionlimit(10000)  # for graph parsing

        self.codebase = await self._build_graph()
        self.executor = SandboxExecutor(self.codebase)

    async def _build_graph(self) -> Codebase:
        logger.info("> Building graph...")
        programming_language = ProgrammingLanguage[self.op.repo_config.language.upper()]
        projects = [ProjectConfig(programming_language=programming_language, repo_operator=self.op, base_path=self.op.repo_config.base_path, subdirectories=self.op.repo_config.subdirectories)]
        return Codebase(projects=projects, config=get_codebase_config())

    @stopwatch
    def reset_runner(self) -> None:
        """Reset the runner to a cleaned/stable state for the next job.

        At the start of every job the runner should be in the following state:
        - Codebase is checked out to the pinned commit (i.e. self.commit)
        - Codebase LRP (LocalRepoOperator) has only the origin remote and no branches

        This method puts the runner in the above state and should be called at the end of every job.
        """
        # TODO: move self.codebase.reset() here instead of during run
        # TODO assert codebase is on the default branch and its clean
        # TODO re-enable this (i.e. rather than pinning the runner commit, always move it forward to the latest commit)
        logger.info("=====[ reset_runner ]=====")
        logger.info(f"Syncing runner to commit: {self.commit} ...")
        self.codebase.checkout(commit=self.commit)
        self.codebase.clean_repo()
        self.codebase.checkout(branch=self.codebase.default_branch, create_if_missing=True)

    @staticmethod
    def _set_sentry_tags(epic_id: int, is_admin: bool) -> None:
        """Set the sentry tags for a CodemodRun"""
        sentry_sdk.set_tag("epic_id", epic_id)  # To easily get to the epic in the UI
        sentry_sdk.set_tag("is_admin", is_admin)  # To filter "prod" level errors, ex if customer hits an error vs an admin

    async def get_diff(self, request: GetDiffRequest) -> GetDiffResponse:
        self._set_sentry_tags(epic_id=request.codemod.epic_id, is_admin=request.codemod.is_admin)
        custom_scope = {"context": request.codemod.codemod_context} if request.codemod.codemod_context else {}
        code_to_exec = create_execute_function_from_codeblock(codeblock=request.codemod.user_code, custom_scope=custom_scope)
        session_options = SessionOptions(max_transactions=request.max_transactions, max_seconds=request.max_seconds)

        res = await self.executor.execute(code_to_exec, session_options=session_options)

        return GetDiffResponse(result=res)

    async def create_branch(self, request: CreateBranchRequest) -> CreateBranchResponse:
        self._set_sentry_tags(epic_id=request.codemod.epic_id, is_admin=request.codemod.is_admin)
        custom_scope = {"context": request.codemod.codemod_context} if request.codemod.codemod_context else {}
        code_to_exec = create_execute_function_from_codeblock(codeblock=request.codemod.user_code, custom_scope=custom_scope)
        branch_config = request.branch_config

        branch_config.base_branch = branch_config.base_branch or self.codebase.default_branch
        self.executor.remote_repo.set_up_base_branch(branch_config.base_branch)
        self.executor.remote_repo.set_up_head_branch(branch_config.custom_head_branch, branch_config.force_push_head_branch)

        response = CreateBranchResponse()
        if "codebase.flag_instance" in request.codemod.user_code:
            flags = await self.executor.find_flags(code_to_exec)
            flag_groups = await self.executor.find_flag_groups(flags, request.grouping_config)
            response.num_flags = len(flags)
            response.group_segments = [group.segment for group in flag_groups]
            if len(flag_groups) == 0:
                logger.info("No flag groups found. Running without flagging.")
                flag_groups = [None]
        else:
            flag_groups = [None]

        # TODO: do this as part of find_flag_groups?
        max_prs = request.grouping_config.max_prs
        if max_prs and len(flag_groups) >= max_prs:
            logger.info(f"Max PRs limit reached: {max_prs}. Skipping remaining groups.")
            flag_groups = flag_groups[:max_prs]

        run_results, branches = await self.executor.execute_flag_groups(request.codemod, code_to_exec, flag_groups, branch_config)
        response.results = run_results
        response.branches = branches

        self.codebase.G.flags._flags.clear()
        return response
