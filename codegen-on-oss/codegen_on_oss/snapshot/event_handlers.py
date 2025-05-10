import logging
import os
import tempfile
from typing import Any, Dict, Literal

import modal
from classy_fastapi import Routable, post
from codegen.agents.code_agent import CodeAgent
from codegen.extensions.events.codegen_app import CodegenApp
from codegen.extensions.events.modal.base import CodebaseEventsApp, EventRouterMixin
from codegen.extensions.github.types.pull_request import PullRequestLabeledEvent
from codegen.extensions.linear.types import LinearEvent
from codegen.extensions.slack.types import SlackEvent
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from pr_tasks import lint_for_dev_import_violations

# Import analysis modules
from codegen_on_oss.analysis.swe_harness_agent import SWEHarnessAgent
from codegen_on_oss.snapshot.codebase_snapshot import SnapshotManager

load_dotenv(".env")


logging.basicConfig(level=logging.INFO, force=True)
logger = logging.getLogger(__name__)

codegen_events_app = modal.App("codegen-events-router")

SNAPSHOT_DICT_ID = "codegen-events-codebase-snapshots"

# Create the base image with dependencies
base_image = (
    modal.Image.debian_slim(python_version="3.13")
    .apt_install("git")
    .pip_install(
        # =====[ Codegen ]=====
        "codegen==0.42.1",
        # =====[ Rest ]=====
        "openai>=1.1.0",
        "fastapi[standard]",
        "slack_sdk",
        "classy-fastapi>=0.6.1",
        "networkx>=2.8.0",
        "pygithub>=1.58.0",
    )
)


event_handlers_app = modal.App("codegen-event-handlers")


@event_handlers_app.cls(
    image=base_image,
    secrets=[modal.Secret.from_dotenv(".env")],
    enable_memory_snapshot=True,
    container_idle_timeout=300,
)
class CustomEventHandlersAPI(CodebaseEventsApp):
    commit: str = modal.parameter(default="79114f67ccfe8700416cd541d1c7c43659a95342")
    repo_org: str = modal.parameter(default="codegen-sh")
    repo_name: str = modal.parameter(default="Kevin-s-Adventure-Game")
    snapshot_index_id: str = SNAPSHOT_DICT_ID
    snapshot_dir: str = modal.parameter(default="/tmp/codebase_snapshots")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Initialize the snapshot manager
        os.makedirs(self.snapshot_dir, exist_ok=True)
        self.snapshot_manager = SnapshotManager(self.snapshot_dir)

        # Initialize the SWE harness agent
        github_token = os.environ.get("GITHUB_TOKEN")
        self.swe_agent = SWEHarnessAgent(github_token, self.snapshot_dir)

    def setup_handlers(self, cg: CodegenApp):
        @cg.slack.event("app_mention")
        async def handle_mention(event: SlackEvent):
            logger.info("[APP_MENTION] Received cg_app_mention event")

            # Codebase
            logger.info("[CODEBASE] Initializing codebase")
            codebase = cg.get_codebase()

            # Code Agent
            logger.info("[CODE_AGENT] Initializing code agent")
            agent = CodeAgent(codebase=codebase)

            logger.info("[CODE_AGENT] Running code agent")
            response = agent.run(event.text)

            cg.slack.client.chat_postMessage(
                channel=event.channel, text=response, thread_ts=event.ts
            )

            return {
                "message": "Mentioned",
                "received_text": event.text,
                "response": response,
            }

        @cg.github.event("pull_request:labeled")
        def handle_pr(event: PullRequestLabeledEvent):
            logger.info("PR labeled")
            logger.info(f"PR head sha: {event.pull_request.head.sha}")

            codebase = cg.get_codebase()
            logger.info(f"Codebase: {codebase.name} codebase.repo: {codebase.repo_path}")

            # =====[ Check out commit ]=====
            logger.info("> Checking out commit")
            codebase.checkout(commit=event.pull_request.head.sha)

            # Create a snapshot of the current state
            logger.info("> Creating snapshot")
            snapshot = self.snapshot_manager.create_snapshot(
                codebase,
                commit_sha=event.pull_request.head.sha,
                snapshot_id=f"{event.repository.name}_{event.pull_request.head.sha}",
            )
            logger.info(f"> Snapshot created: {snapshot.snapshot_id}")

            # If the label is "CodeReview", analyze the PR
            if event.label.name == "CodeReview":
                logger.info("> Analyzing PR for code review")
                analysis_results = self.swe_agent.analyze_and_comment_on_pr(
                    f"{event.organization.login}/{event.repository.name}",
                    event.number,
                    post_comment=True,
                )
                logger.info(f"> Analysis complete: {analysis_results['is_properly_implemented']}")

                # Post a message to Slack with the analysis results
                if "SLACK_CHANNEL" in os.environ:
                    channel = os.environ["SLACK_CHANNEL"]
                    message = f"PR #{event.number} analysis complete:\n"
                    message += f"Quality Score: {analysis_results['quality_score']}/10.0 - {analysis_results['overall_assessment']}\n"
                    message += f"Properly Implemented: {'Yes' if analysis_results['is_properly_implemented'] else 'No'}\n"

                    if "issues" in analysis_results and analysis_results["issues"]:
                        message += "\nIssues:\n"
                        for issue in analysis_results["issues"]:
                            message += f"- {issue}\n"

                    cg.slack.client.chat_postMessage(channel=channel, text=message)

            # Run PR lints
            logger.info("> Running PR Lints")
            lint_for_dev_import_violations(codebase, event)

            return {
                "message": "PR event handled",
                "num_files": len(codebase.files),
                "num_functions": len(codebase.functions),
            }

        @cg.linear.event("Issue")
        def handle_issue(event: LinearEvent):
            logger.info(f"Issue created: {event}")
            codebase = cg.get_codebase()
            return {
                "message": "Linear Issue event",
                "num_files": len(codebase.files),
                "num_functions": len(codebase.functions),
            }

        @cg.github.event("pull_request:closed")
        def handle_pr_closed(event):
            logger.info("PR closed")

            # If the PR was merged, create a snapshot of the merged state
            if event.pull_request.merged:
                logger.info(f"PR #{event.number} was merged")

                codebase = cg.get_codebase()
                logger.info(f"Codebase: {codebase.name} codebase.repo: {codebase.repo_path}")

                # Check out the base branch (usually main or master)
                base_branch = event.pull_request.base.ref
                logger.info(f"> Checking out base branch: {base_branch}")
                codebase.checkout(branch=base_branch)

                # Create a snapshot of the current state
                logger.info("> Creating snapshot of merged state")
                snapshot = self.snapshot_manager.create_snapshot(
                    codebase,
                    commit_sha=event.pull_request.merge_commit_sha,
                    snapshot_id=f"{event.repository.name}_{event.pull_request.merge_commit_sha}",
                )
                logger.info(f"> Snapshot created: {snapshot.snapshot_id}")

            return {"message": "PR closed event handled"}


@codegen_events_app.cls(image=base_image, secrets=[modal.Secret.from_dotenv(".env")])
class WebhookEventRouterAPI(EventRouterMixin, Routable):
    snapshot_index_id: str = SNAPSHOT_DICT_ID

    def get_event_handler_cls(self):
        modal_cls = modal.Cls.from_name(app_name="Events", name="CustomEventHandlersAPI")
        return modal_cls

    @post("/{org}/{repo}/{provider}/events")
    async def handle_event(
        self,
        org: str,
        repo: str,
        provider: Literal["slack", "github", "linear"],
        request: Request,
    ):
        # Define the route for the webhook url sink, it will need to indicate the repo repo org, and the provider
        return await super().handle_event(org, repo, provider, request)

    @modal.asgi_app()
    def api(self):
        """Run the FastAPI app with the Router."""
        event_api = FastAPI()
        route_view = WebhookEventRouterAPI()
        event_api.include_router(route_view.router)
        return event_api


# Setup a cron job to trigger updates to the codebase snapshots.
@codegen_events_app.function(
    schedule=modal.Cron("*/10 * * * *"),
    image=base_image,
    secrets=[modal.Secret.from_dotenv(".env")],
)
def refresh_repository_snapshots():
    WebhookEventRouterAPI().refresh_repository_snapshots(snapshot_index_id=SNAPSHOT_DICT_ID)


# Add a new endpoint to analyze a PR
@codegen_events_app.function(image=base_image, secrets=[modal.Secret.from_dotenv(".env")])
@modal.web_endpoint(method="POST")
def analyze_pr(payload: Dict[str, Any]):
    """
    Analyze a pull request and return the results.

    Payload should include:
    - repo_url: The repository URL or owner/repo string
    - pr_number: The pull request number
    - github_token: Optional GitHub token for private repositories
    """
    try:
        # Extract parameters from payload
        repo_url = payload.get("repo_url")
        pr_number = payload.get("pr_number")
        github_token = payload.get("github_token", os.environ.get("GITHUB_TOKEN"))

        if not repo_url or not pr_number:
            return {"error": "Missing required parameters: repo_url and pr_number"}

        # Create a SWE harness agent
        snapshot_dir = tempfile.mkdtemp(prefix="pr_analysis_")
        swe_agent = SWEHarnessAgent(github_token, snapshot_dir)

        # Analyze the PR
        analysis_results = swe_agent.analyze_pull_request(repo_url, pr_number)

        # Return the results
        return {
            "success": True,
            "is_properly_implemented": analysis_results["is_properly_implemented"],
            "quality_score": analysis_results["quality_score"],
            "overall_assessment": analysis_results["overall_assessment"],
            "report": analysis_results["report"],
            "issues": analysis_results.get("issues", []),
        }
    except Exception as e:
        logger.error(f"Error analyzing PR: {e}")
        return {"success": False, "error": str(e)}


# Add a new endpoint to analyze a commit
@codegen_events_app.function(image=base_image, secrets=[modal.Secret.from_dotenv(".env")])
@modal.web_endpoint(method="POST")
def analyze_commit(payload: Dict[str, Any]):
    """
    Analyze a commit and return the results.

    Payload should include:
    - repo_url: The repository URL or owner/repo string
    - base_commit: The base commit SHA (before the changes)
    - head_commit: The head commit SHA (after the changes)
    - github_token: Optional GitHub token for private repositories
    """
    try:
        # Extract parameters from payload
        repo_url = payload.get("repo_url")
        base_commit = payload.get("base_commit")
        head_commit = payload.get("head_commit")
        github_token = payload.get("github_token", os.environ.get("GITHUB_TOKEN"))

        if not repo_url or not base_commit or not head_commit:
            return {"error": "Missing required parameters: repo_url, base_commit, and head_commit"}

        # Create a SWE harness agent
        snapshot_dir = tempfile.mkdtemp(prefix="commit_analysis_")
        swe_agent = SWEHarnessAgent(github_token, snapshot_dir)

        # Analyze the commit
        analysis_results = swe_agent.analyze_commit(repo_url, base_commit, head_commit)

        # Return the results
        return {
            "success": True,
            "is_properly_implemented": analysis_results["is_properly_implemented"],
            "quality_score": analysis_results["quality_score"],
            "overall_assessment": analysis_results["overall_assessment"],
            "report": analysis_results["report"],
            "issues": analysis_results.get("issues", []),
        }
    except Exception as e:
        logger.error(f"Error analyzing commit: {e}")
        return {"success": False, "error": str(e)}


app = modal.App("Events", secrets=[modal.Secret.from_dotenv(".env")])
app.include(event_handlers_app)
app.include(codegen_events_app)
