from contextlib import asynccontextmanager

import modal
from codegen.extensions.swebench.utils import SweBenchExample

from .snapshot_manager import (
    ModalDictSnapshotManager,
    SnapshotManager,
)

BASE_IMAGE: modal.Image = modal.Image.debian_slim(python_version="3.13").apt_install("git")

try:
    # To ensure secrets are consistent across runs, we look up existing secret
    secret = modal.Secret.from_name("swebench-agent-run-secrets")
except modal.exception.NotFoundError:
    secret = modal.Secret.from_dotenv()

app = modal.App.lookup(name="swebench-agent-run", create_if_missing=True)


class SandboxManager:
    keep_alive: bool

    def __init__(
        self,
        keep_alive: bool = False,
        snapshot_manager: SnapshotManager | None = None,
    ):
        self.keep_alive = keep_alive
        self.snapshot_manager = snapshot_manager or ModalDictSnapshotManager()

    async def create_sandbox(self, example: SweBenchExample) -> modal.Sandbox:
        existing_snapshot_uid = await self.snapshot_manager.get_snapshot_uid(example)
        if existing_snapshot_uid:
            return await modal.Sandbox._experimental_from_snapshot(existing_snapshot_uid)

        # TODO: test if this get local version works / add ability to install specific version
        with modal.enable_output():
            return await modal.Sandbox.create(
                app=app,
                image=BASE_IMAGE.run_commands(f"cd /root; git clone {example.repo} && cd {example.repo} && git checkout {example.environment_setup_commit}"),
                secrets=[secret],
                tags={"repo": example.repo, "commit": example.environment_setup_commit},
            )

    @asynccontextmanager
    async def get_sandbox(self, example: SweBenchExample):
        async for sandbox in modal.Sandbox.list(
            app_id=app.app_id,
            tags={"repo": example.repo, "commit": example.environment_setup_commit},
        ):
            break
        else:
            sandbox = await self.create_sandbox(example)

        try:
            await sandbox.wait()
            yield sandbox
        finally:
            if not self.keep_alive:
                # Killing sandbox, so take a snapshot and save it
                await sandbox.exec(
                    "bash",
                    "-c",
                    f"cd /root/{example.repo}; git stash",  # cheeky little stash
                )
                snapshot = await sandbox._experimental_snapshot()  # commit any codegen updates

                await self.snapshot_manager.save_snapshot_uid(example, snapshot.object_id)

                # Codebase.from_repo doesn't use git to fetch/checkout the repo.
                # We could replace this with our own git commands to control the file state
                await sandbox.terminate()
