from pathlib import Path
from unittest.mock import patch

from codegen.cli.auth.constants import AUTH_FILE, CODEGEN_DIR, CONFIG_DIR, DOCS_DIR, EXAMPLES_DIR, PROMPTS_DIR


class TestConstants:
    def test_constants_paths(self):
        """Test that the constants define the expected paths."""
        # Verify the base directories
        assert CONFIG_DIR == Path("~/.config/codegen-sh").expanduser()
        assert CODEGEN_DIR == Path(".codegen")
        assert PROMPTS_DIR == CODEGEN_DIR / "prompts"

        # Verify the subdirectories
        assert DOCS_DIR == CODEGEN_DIR / "docs"
        assert EXAMPLES_DIR == CODEGEN_DIR / "examples"

        # Verify the files
        assert AUTH_FILE == CONFIG_DIR / "auth.json"

    def test_expanduser_called(self):
        """Test that expanduser is called on the CONFIG_DIR path."""
        with patch.object(Path, "expanduser", return_value=Path("/home/user/.config/codegen-sh")) as mock_expanduser:
            from importlib import reload

            import codegen.cli.auth.constants

            reload(codegen.cli.auth.constants)

            # Verify expanduser was called
            mock_expanduser.assert_called_once()
