import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from watchfiles import Change

from codegen_on_oss.analyzers.diff_lite import ChangeType, DiffLite


class TestChangeType(unittest.TestCase):
    def test_from_watch_change_type_added(self):
        self.assertEqual(
            ChangeType.from_watch_change_type(Change.added), ChangeType.Added
        )

    def test_from_watch_change_type_deleted(self):
        self.assertEqual(
            ChangeType.from_watch_change_type(Change.deleted), ChangeType.Removed
        )

    def test_from_watch_change_type_modified(self):
        self.assertEqual(
            ChangeType.from_watch_change_type(Change.modified), ChangeType.Modified
        )

    def test_from_watch_change_type_invalid(self):
        # Create a mock Change that doesn't match any of the expected values
        invalid_change = MagicMock()
        with self.assertRaises(ValueError):
            ChangeType.from_watch_change_type(invalid_change)

    def test_from_git_change_type_modified(self):
        self.assertEqual(ChangeType.from_git_change_type("M"), ChangeType.Modified)

    def test_from_git_change_type_removed(self):
        self.assertEqual(ChangeType.from_git_change_type("D"), ChangeType.Removed)

    def test_from_git_change_type_renamed(self):
        self.assertEqual(ChangeType.from_git_change_type("R"), ChangeType.Renamed)

    def test_from_git_change_type_added(self):
        self.assertEqual(ChangeType.from_git_change_type("A"), ChangeType.Added)

    def test_from_git_change_type_invalid(self):
        with self.assertRaises(ValueError):
            ChangeType.from_git_change_type("X")


class TestDiffLite(unittest.TestCase):
    def test_from_watch_change(self):
        path = "test/path.py"
        diff = DiffLite.from_watch_change(Change.added, path)

        self.assertEqual(diff.change_type, ChangeType.Added)
        self.assertEqual(diff.path, Path(path))
        self.assertIsNone(diff.rename_from)
        self.assertIsNone(diff.rename_to)
        self.assertIsNone(diff.old_content)

    @patch("git.Diff")
    def test_from_git_diff_modified(self, mock_diff):
        mock_diff.change_type = "M"
        mock_diff.a_path = "test/path.py"
        mock_diff.rename_from = None
        mock_diff.rename_to = None

        # Mock the blob and data stream
        mock_blob = MagicMock()
        mock_blob.data_stream.read.return_value = b"old content"
        mock_diff.a_blob = mock_blob

        diff = DiffLite.from_git_diff(mock_diff)

        self.assertEqual(diff.change_type, ChangeType.Modified)
        self.assertEqual(diff.path, Path("test/path.py"))
        self.assertIsNone(diff.rename_from)
        self.assertIsNone(diff.rename_to)
        self.assertEqual(diff.old_content, b"old content")

    @patch("git.Diff")
    def test_from_git_diff_renamed(self, mock_diff):
        mock_diff.change_type = "R"
        mock_diff.a_path = "test/old_path.py"
        mock_diff.rename_from = "test/old_path.py"
        mock_diff.rename_to = "test/new_path.py"
        mock_diff.a_blob = None

        diff = DiffLite.from_git_diff(mock_diff)

        self.assertEqual(diff.change_type, ChangeType.Renamed)
        self.assertEqual(diff.path, Path("test/old_path.py"))
        self.assertEqual(diff.rename_from, Path("test/old_path.py"))
        self.assertEqual(diff.rename_to, Path("test/new_path.py"))
        self.assertIsNone(diff.old_content)

    def test_from_reverse_diff_added_to_removed(self):
        original = DiffLite(change_type=ChangeType.Added, path=Path("test/path.py"))

        reversed_diff = DiffLite.from_reverse_diff(original)

        self.assertEqual(reversed_diff.change_type, ChangeType.Removed)
        self.assertEqual(reversed_diff.path, Path("test/path.py"))

    def test_from_reverse_diff_removed_to_added(self):
        original = DiffLite(change_type=ChangeType.Removed, path=Path("test/path.py"))

        reversed_diff = DiffLite.from_reverse_diff(original)

        self.assertEqual(reversed_diff.change_type, ChangeType.Added)
        self.assertEqual(reversed_diff.path, Path("test/path.py"))

    def test_from_reverse_diff_renamed(self):
        original = DiffLite(
            change_type=ChangeType.Renamed,
            path=Path("test/old_path.py"),
            rename_from=Path("test/old_path.py"),
            rename_to=Path("test/new_path.py"),
        )

        reversed_diff = DiffLite.from_reverse_diff(original)

        self.assertEqual(reversed_diff.change_type, ChangeType.Renamed)
        self.assertEqual(reversed_diff.path, Path("test/old_path.py"))
        self.assertEqual(reversed_diff.rename_from, Path("test/new_path.py"))
        self.assertEqual(reversed_diff.rename_to, Path("test/old_path.py"))


if __name__ == "__main__":
    unittest.main()
