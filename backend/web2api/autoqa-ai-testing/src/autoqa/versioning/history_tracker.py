"""
Test run history tracker for versioned test tracking.

Provides persistent storage and retrieval of test snapshots with
date-based organization and efficient querying.
"""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

import structlog

from autoqa.versioning.models import (
    BoundingBox,
    ElementState,
    NetworkRequest,
    TestSnapshot,
    VersioningConfig,
)

if TYPE_CHECKING:
    from autoqa.runner.test_runner import TestRunResult

logger = structlog.get_logger(__name__)


class HistoryStorageError(Exception):
    """Raised when history storage operations fail."""

    pass


class SnapshotNotFoundError(Exception):
    """Raised when a requested snapshot cannot be found."""

    pass


class TestRunHistory:
    """
    Stores and retrieves test run snapshots for version comparison.

    Storage structure:
        {storage_path}/
            {sanitized_test_name}/
                {YYYY-MM-DD_HH-MM-SS}/
                    screenshot.png
                    snapshot.json
                    metadata.json
    """

    DATE_FORMAT = "%Y-%m-%d_%H-%M-%S"

    def __init__(
        self,
        storage_path: str | Path = ".autoqa/history",
        config: VersioningConfig | None = None,
    ) -> None:
        self._storage_path = Path(storage_path)
        self._config = config or VersioningConfig()
        self._log = logger.bind(component="history_tracker")

        self._storage_path.mkdir(parents=True, exist_ok=True)

    @property
    def storage_path(self) -> Path:
        """Get the storage path."""
        return self._storage_path

    def save_snapshot(
        self,
        test_name: str,
        run_data: TestRunResult,
        page: Any | None = None,
        additional_data: dict[str, Any] | None = None,
    ) -> TestSnapshot:
        """
        Save a snapshot of a test run.

        Args:
            test_name: Name of the test
            run_data: Test run result data
            page: Browser page for capturing additional state (optional)
            additional_data: Extra data to include in snapshot

        Returns:
            The saved TestSnapshot

        Raises:
            HistoryStorageError: If snapshot cannot be saved
        """
        timestamp = datetime.now(UTC)
        version_id = self._generate_version_id(test_name, timestamp)

        snapshot = TestSnapshot(
            test_name=test_name,
            timestamp=timestamp,
            version_id=version_id,
            test_status=run_data.status,
            duration_ms=run_data.duration_ms,
            error_message=run_data.error,
        )

        test_dir = self._get_test_dir(test_name)
        version_dir = test_dir / timestamp.strftime(self.DATE_FORMAT)

        try:
            version_dir.mkdir(parents=True, exist_ok=True)

            # Capture screenshot if page is available
            if page is not None and self._config.capture_screenshots:
                screenshot_path = self._capture_screenshot(page, version_dir)
                if screenshot_path:
                    snapshot.screenshot_path = str(screenshot_path)
                    snapshot.screenshot_hash = self._compute_file_hash(screenshot_path)

            # Capture page state if page is available
            if page is not None:
                self._capture_page_state(page, snapshot)

            # Capture network requests from run data
            if self._config.capture_network and run_data.network_log:
                snapshot.network_requests = [
                    self._convert_network_entry(entry)
                    for entry in run_data.network_log
                ]

            # Capture element states if configured
            if page is not None and self._config.capture_elements:
                snapshot.element_states = self._capture_element_states(
                    page, self._config.element_selectors
                )

            # Add additional data
            if additional_data:
                snapshot.extracted_texts.update(
                    additional_data.get("extracted_texts", {})
                )

            # Save snapshot data
            snapshot_file = version_dir / "snapshot.json"
            snapshot_file.write_text(
                json.dumps(snapshot.to_dict(), indent=2, default=str),
                encoding="utf-8",
            )

            # Save metadata
            metadata = {
                "version_id": version_id,
                "test_name": test_name,
                "timestamp": timestamp.isoformat(),
                "config": self._config.to_dict(),
            }
            metadata_file = version_dir / "metadata.json"
            metadata_file.write_text(
                json.dumps(metadata, indent=2),
                encoding="utf-8",
            )

            self._log.info(
                "Snapshot saved",
                test=test_name,
                version=version_id,
                path=str(version_dir),
            )

            return snapshot

        except Exception as e:
            self._log.error(
                "Failed to save snapshot",
                test=test_name,
                error=str(e),
            )
            raise HistoryStorageError(f"Failed to save snapshot: {e}") from e

    def get_snapshots(
        self,
        test_name: str,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
    ) -> list[TestSnapshot]:
        """
        Get snapshots for a test within a date range.

        Args:
            test_name: Name of the test
            from_date: Start of date range (inclusive)
            to_date: End of date range (inclusive)

        Returns:
            List of snapshots sorted by timestamp (oldest first)
        """
        test_dir = self._get_test_dir(test_name)
        if not test_dir.exists():
            return []

        snapshots: list[TestSnapshot] = []

        for version_dir in sorted(test_dir.iterdir()):
            if not version_dir.is_dir():
                continue

            try:
                timestamp = datetime.strptime(
                    version_dir.name, self.DATE_FORMAT
                ).replace(tzinfo=UTC)

                # Apply date filters
                if from_date and timestamp < from_date:
                    continue
                if to_date and timestamp > to_date:
                    continue

                snapshot = self._load_snapshot(version_dir)
                if snapshot:
                    snapshots.append(snapshot)

            except ValueError:
                # Skip directories that don't match date format
                continue

        return sorted(snapshots, key=lambda s: s.timestamp)

    def get_latest(self, test_name: str) -> TestSnapshot | None:
        """
        Get the most recent snapshot for a test.

        Args:
            test_name: Name of the test

        Returns:
            Latest snapshot or None if no snapshots exist
        """
        snapshots = self.get_snapshots(test_name)
        return snapshots[-1] if snapshots else None

    def get_by_date(
        self,
        test_name: str,
        target_date: datetime,
        exact_match: bool = False,
    ) -> TestSnapshot | None:
        """
        Get snapshot closest to a specific date.

        Args:
            test_name: Name of the test
            target_date: Target date to find
            exact_match: If True, only return snapshot from that exact day

        Returns:
            Snapshot closest to target date or None
        """
        snapshots = self.get_snapshots(test_name)
        if not snapshots:
            return None

        if exact_match:
            target_day = target_date.date()
            for snapshot in snapshots:
                if snapshot.timestamp.date() == target_day:
                    return snapshot
            return None

        # Find closest snapshot
        closest: TestSnapshot | None = None
        min_diff: float = float("inf")

        for snapshot in snapshots:
            diff = abs((snapshot.timestamp - target_date).total_seconds())
            if diff < min_diff:
                min_diff = diff
                closest = snapshot

        return closest

    def get_by_version_id(self, test_name: str, version_id: str) -> TestSnapshot | None:
        """
        Get snapshot by its version ID.

        Args:
            test_name: Name of the test
            version_id: Version identifier

        Returns:
            Snapshot with matching version ID or None
        """
        snapshots = self.get_snapshots(test_name)
        for snapshot in snapshots:
            if snapshot.version_id == version_id:
                return snapshot
        return None

    def list_versions(self, test_name: str) -> list[datetime]:
        """
        List all version timestamps for a test.

        Args:
            test_name: Name of the test

        Returns:
            List of timestamps sorted chronologically
        """
        snapshots = self.get_snapshots(test_name)
        return [s.timestamp for s in snapshots]

    def list_tests(self) -> list[str]:
        """
        List all tests that have snapshots.

        Returns:
            List of test names
        """
        tests: list[str] = []
        for test_dir in self._storage_path.iterdir():
            if test_dir.is_dir() and not test_dir.name.startswith("."):
                tests.append(self._unsanitize_test_name(test_dir.name))
        return sorted(tests)

    def delete_snapshot(self, test_name: str, version_id: str) -> bool:
        """
        Delete a specific snapshot.

        Args:
            test_name: Name of the test
            version_id: Version to delete

        Returns:
            True if deleted, False if not found
        """
        snapshot = self.get_by_version_id(test_name, version_id)
        if not snapshot:
            return False

        version_dir = self._get_version_dir_from_timestamp(test_name, snapshot.timestamp)
        if version_dir and version_dir.exists():
            shutil.rmtree(version_dir)
            self._log.info("Snapshot deleted", test=test_name, version=version_id)
            return True

        return False

    def cleanup_old_snapshots(self, retention_days: int | None = None) -> int:
        """
        Remove snapshots older than retention period.

        Args:
            retention_days: Days to retain (uses config if not specified)

        Returns:
            Number of snapshots deleted
        """
        days = retention_days or self._config.retention_days
        cutoff = datetime.now(UTC).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        cutoff = cutoff.replace(day=cutoff.day - days)

        deleted_count = 0

        for test_name in self.list_tests():
            snapshots = self.get_snapshots(test_name, to_date=cutoff)
            for snapshot in snapshots:
                if self.delete_snapshot(test_name, snapshot.version_id):
                    deleted_count += 1

        self._log.info(
            "Cleanup completed",
            deleted=deleted_count,
            retention_days=days,
        )

        return deleted_count

    def _get_test_dir(self, test_name: str) -> Path:
        """Get directory for a test's snapshots."""
        safe_name = self._sanitize_test_name(test_name)
        return self._storage_path / safe_name

    def _get_version_dir_from_timestamp(
        self, test_name: str, timestamp: datetime
    ) -> Path | None:
        """Get version directory from timestamp."""
        test_dir = self._get_test_dir(test_name)
        version_dir = test_dir / timestamp.strftime(self.DATE_FORMAT)
        return version_dir if version_dir.exists() else None

    def _sanitize_test_name(self, test_name: str) -> str:
        """Sanitize test name for use as directory name."""
        return re.sub(r"[^\w\-_]", "_", test_name)

    def _unsanitize_test_name(self, dir_name: str) -> str:
        """Attempt to restore original test name from directory name."""
        # This is a best-effort restoration
        return dir_name.replace("_", " ")

    def _generate_version_id(self, test_name: str, timestamp: datetime) -> str:  # noqa: ARG002
        """Generate unique version ID."""
        unique_part = uuid.uuid4().hex[:8]
        date_part = timestamp.strftime("%Y%m%d%H%M%S")
        return f"{date_part}-{unique_part}"

    def _load_snapshot(self, version_dir: Path) -> TestSnapshot | None:
        """Load snapshot from directory."""
        snapshot_file = version_dir / "snapshot.json"
        if not snapshot_file.exists():
            return None

        try:
            data = json.loads(snapshot_file.read_text(encoding="utf-8"))
            return TestSnapshot.from_dict(data)
        except (json.JSONDecodeError, KeyError) as e:
            self._log.warning(
                "Failed to load snapshot",
                path=str(version_dir),
                error=str(e),
            )
            return None

    def _capture_screenshot(self, page: Any, version_dir: Path) -> Path | None:
        """Capture screenshot from page."""
        try:
            screenshot_path = version_dir / "screenshot.png"
            page.screenshot(str(screenshot_path))
            return screenshot_path
        except Exception as e:
            self._log.warning("Failed to capture screenshot", error=str(e))
            return None

    def _capture_page_state(self, page: Any, snapshot: TestSnapshot) -> None:
        """Capture page state (title, URL) from page."""
        try:
            snapshot.page_title = page.title() if hasattr(page, "title") else None
            snapshot.page_url = page.url() if hasattr(page, "url") else None
        except Exception as e:
            self._log.debug("Failed to capture page state", error=str(e))

    def _capture_element_states(
        self, page: Any, selectors: list[str]
    ) -> list[ElementState]:
        """Capture element states for configured selectors."""
        states: list[ElementState] = []

        for selector in selectors:
            try:
                state = self._capture_single_element_state(page, selector)
                if state:
                    states.append(state)
            except Exception as e:
                self._log.debug(
                    "Failed to capture element state",
                    selector=selector,
                    error=str(e),
                )

        return states

    def _capture_single_element_state(
        self, page: Any, selector: str
    ) -> ElementState | None:
        """Capture state of a single element."""
        try:
            # This is a placeholder - actual implementation depends on browser API
            is_visible = page.is_visible(selector) if hasattr(page, "is_visible") else True
            is_enabled = page.is_enabled(selector) if hasattr(page, "is_enabled") else True

            # Try to get bounding box
            bbox: BoundingBox | None = None
            if hasattr(page, "get_bounding_box"):
                box_data = page.get_bounding_box(selector)
                if box_data:
                    bbox = BoundingBox(
                        x=int(box_data.get("x", 0)),
                        y=int(box_data.get("y", 0)),
                        width=int(box_data.get("width", 0)),
                        height=int(box_data.get("height", 0)),
                    )

            # Try to get text content
            text_content = None
            if hasattr(page, "extract_text"):
                text_content = page.extract_text(selector)

            return ElementState(
                selector=selector,
                tag_name="unknown",  # Would need DOM query
                text_content=text_content,
                attributes={},
                bounding_box=bbox,
                is_visible=is_visible,
                is_enabled=is_enabled,
            )

        except Exception:
            return None

    def _convert_network_entry(self, entry: dict[str, Any]) -> NetworkRequest:
        """Convert network log entry to NetworkRequest."""
        return NetworkRequest(
            url=entry.get("url", ""),
            method=entry.get("method", "GET"),
            status_code=entry.get("status_code") or entry.get("status"),
            response_time_ms=entry.get("response_time_ms") or entry.get("duration"),
            request_headers=entry.get("request_headers", {}),
            response_headers=entry.get("response_headers", {}),
            content_type=entry.get("content_type") or entry.get("mimeType"),
            content_length=entry.get("content_length") or entry.get("responseSize"),
        )

    def _compute_file_hash(self, file_path: Path) -> str:
        """Compute SHA256 hash of a file."""
        sha256 = hashlib.sha256()
        with file_path.open("rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest()
