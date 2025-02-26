import dataclasses
import importlib
import importlib.util
from dataclasses import dataclass
from pathlib import Path

from codegen.cli.api.webapp_routes import generate_webapp_url
from codegen.cli.utils.schema import CodemodConfig


@dataclass
class Codemod:
    """Represents a codemod in the local filesystem."""

    name: str
    path: Path
    config: CodemodConfig | None = None

    def get_url(self) -> str:
        """Get the URL for this codemod."""
        return generate_webapp_url(path=f"codemod/{self.config.codemod_id}")

    def relative_path(self) -> str:
        """Get the relative path to this codemod."""
        return self.path.relative_to(Path.cwd())

    def get_current_source(self) -> str:
        """Get the current source code for this codemod."""
        text = self.path.read_text()
        text = text.strip()
        return text

    def get_system_prompt_path(self) -> Path:
        """Get the path to the system prompt for this codemod."""
        return self.path.parent / "system-prompt.md"

    def get_system_prompt(self) -> str:
        """Get the system prompt for this codemod."""
        path = self.get_system_prompt_path()
        if not path.exists():
            return ""
        return path.read_text()


@dataclass
class DecoratedFunction:
    """Represents a function decorated with @codegen."""

    name: str
    source: str
    lint_mode: bool
    lint_user_whitelist: list[str]
    filepath: Path | None = None
    parameters: list[tuple[str, str | None]] = dataclasses.field(default_factory=list)
    arguments_type_schema: dict | None = None

    def run(self, codebase) -> str | None:
        """Import and run the actual function from its file.

        Args:
            codebase: The codebase to run the function on

        Returns:
            The result of running the function (usually a diff string)
        """
        if not self.filepath:
            msg = "Cannot run function without filepath"
            raise ValueError(msg)

        # Import the module containing the function
        spec = importlib.util.spec_from_file_location("module", self.filepath)
        if not spec or not spec.loader:
            msg = f"Could not load module from {self.filepath}"
            raise ImportError(msg)

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Find the decorated function
        for item_name in dir(module):
            item = getattr(module, item_name)
            if hasattr(item, "__codegen_name__") and item.__codegen_name__ == self.name:
                # Found our function, run it
                return item(codebase)

        msg = f"Could not find function '{self.name}' in {self.filepath}"
        raise ValueError(msg)

    def validate(self) -> None:
        """Verify that this function can be imported and accessed.

        Raises:
            ValueError: If the function can't be found or imported
        """
        if not self.filepath:
            msg = "Cannot validate function without filepath"
            raise ValueError(msg)

        # Import the module containing the function
        spec = importlib.util.spec_from_file_location("module", self.filepath)
        if not spec or not spec.loader:
            msg = f"Could not load module from {self.filepath}"
            raise ImportError(msg)

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Find the decorated function
        for item_name in dir(module):
            item = getattr(module, item_name)
            if hasattr(item, "__codegen_name__") and item.__codegen_name__ == self.name:
                return  # Found it!

        msg = f"Could not find function '{self.name}' in {self.filepath}"
        raise ValueError(msg)
