import io
import json
from collections import defaultdict

import modal
from codegen.extensions.swebench.utils import SweBenchExample


class SnapshotManager:
    async def get_snapshot_uid(self, example: SweBenchExample) -> str:
        raise NotImplementedError("Not implemented")

    async def save_snapshot_uid(self, example: SweBenchExample, snapshot_uid: str) -> None:
        raise NotImplementedError("Not implemented")


class VolumeSnapshotManager(SnapshotManager):
    def __init__(self, volume_name: str = "swebench-agent-snapshot-volume"):
        self.snapshot_volume = modal.Volume.from_name(volume_name, create_if_missing=True)
        self.snapshot_meta_file_path: str = "/root/snapshot_meta.json"

    async def get_snapshot_uid(self, example: SweBenchExample) -> str:
        snapshot_meta = await self.read_snapshot_meta()
        return snapshot_meta[example.repo][example.base_commit]

    async def save_snapshot_uid(self, example: SweBenchExample, snapshot_uid: str) -> None:
        snapshot_meta = await self.read_snapshot_meta()
        snapshot_meta[example.repo][example.environment_setup_commit] = snapshot_uid
        async with self.snapshot_volume.batch_upload() as upload:
            await upload.put_file(
                io.BytesIO(json.dumps(snapshot_meta).encode("utf-8")),
                self.snapshot_meta_file_path,
            )
        await self.snapshot_volume.commit()

    async def read_snapshot_meta(self) -> dict[str, dict[str, str]]:
        bytes_io = io.BytesIO()
        try:
            await self.snapshot_volume.read_file_into_fileobj(self.snapshot_meta_file_path, bytes_io)
            snapshot_meta = json.loads(bytes_io.getvalue().decode("utf-8"))
        except FileNotFoundError:
            snapshot_meta = {}
        return defaultdict(lambda: defaultdict(lambda: None), snapshot_meta)


class ModalDictSnapshotManager(SnapshotManager):
    def __init__(self, name: str = "swebench-agent-snapshot-dict"):
        self.snapshot_dict = modal.Dict.from_name(name, create_if_missing=True)

    async def get_snapshot_uid(self, example: SweBenchExample) -> str | None:
        try:
            return self.snapshot_dict[(example.repo, example.environment_setup_commit)]
        except KeyError:
            return None

    async def save_snapshot_uid(self, example: SweBenchExample, snapshot_uid: str) -> None:
        self.snapshot_dict[(example.repo, example.environment_setup_commit)] = snapshot_uid
