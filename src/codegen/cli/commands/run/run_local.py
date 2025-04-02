from pathlib import Path
import gc
import os
import psutil
import time
from typing import Optional

import rich
from rich.panel import Panel
from rich.status import Status

from codegen.cli.auth.session import CodegenSession
from codegen.cli.utils.function_finder import DecoratedFunction
from codegen.git.repo_operator.repo_operator import RepoOperator
from codegen.git.schemas.repo_config import RepoConfig
from codegen.git.utils.language import determine_project_language
from codegen.sdk.codebase.config import ProjectConfig
from codegen.sdk.core.codebase import Codebase
from codegen.shared.enums.programming_language import ProgrammingLanguage


def parse_codebase(
    repo_path: Path,
    subdirectories: list[str] | None = None,
    language: ProgrammingLanguage | None = None,
) -> Codebase:
    """Parse the codebase at the given root.

    Args:
        repo_root: Path to the repository root

    Returns:
        Parsed Codebase object
    """
    # Force garbage collection before parsing to free up memory
    gc.collect()
    
    codebase = Codebase(
        projects=[
            ProjectConfig(
                repo_operator=RepoOperator(repo_config=RepoConfig.from_repo_path(repo_path=repo_path)),
                subdirectories=subdirectories,
                programming_language=language or determine_project_language(repo_path),
            )
        ]
    )
    return codebase


def run_local(
    session: CodegenSession,
    function: DecoratedFunction,
    diff_preview: int | None = None,
) -> None:
    """Run a function locally against the codebase.

    Args:
        session: The current codegen session
        function: The function to run
        diff_preview: Number of lines of diff to preview (None for all)
    """
    # Get initial memory usage
    process = psutil.Process(os.getpid())
    initial_memory = process.memory_info().rss / (1024 * 1024)  # Convert to MB
    
    # Parse codebase and run
    with Status(f"[bold]Parsing codebase at {session.repo_path} with subdirectories {function.subdirectories or 'ALL'} and language {function.language or 'AUTO'} ...", spinner="dots") as status:
        start_time = time.time()
        codebase = parse_codebase(repo_path=session.repo_path, subdirectories=function.subdirectories, language=function.language)
        parse_time = time.time() - start_time
        status.update(f"[bold green]✓ Parsed codebase in {parse_time:.2f}s")

        # Memory usage after parsing
        post_parse_memory = process.memory_info().rss / (1024 * 1024)
        
        status.update("[bold]Running codemod...")
        start_time = time.time()
        function.run(codebase)  # Run the function
        run_time = time.time() - start_time
        status.update(f"[bold green]✓ Completed codemod in {run_time:.2f}s")

    # Get the diff from the codebase
    result = codebase.get_diff()
    
    # Final memory usage
    final_memory = process.memory_info().rss / (1024 * 1024)
    
    # Handle no changes case
    if not result:
        rich.print("\n[yellow]No changes were produced by this codemod[/yellow]")
        rich.print(f"\n[dim]Memory usage: {initial_memory:.2f}MB → {final_memory:.2f}MB (Δ {final_memory - initial_memory:.2f}MB)[/dim]")
        return

    # Show diff preview if requested
    if diff_preview:
        rich.print("")  # Add spacing
        diff_lines = result.splitlines()
        truncated = len(diff_lines) > diff_preview
        limited_diff = "\n".join(diff_lines[:diff_preview])

        if truncated:
            limited_diff += f"\n\n...\n\n[yellow]diff truncated to {diff_preview} lines[/yellow]"

        panel = Panel(limited_diff, title="[bold]Diff Preview[/bold]", border_style="blue", padding=(1, 2), expand=False)
        rich.print(panel)

    # Apply changes
    rich.print("")
    rich.print("[green]✓ Changes have been applied to your local filesystem[/green]")
    
    # Print memory usage statistics
    rich.print(f"\n[dim]Memory usage: {initial_memory:.2f}MB → {final_memory:.2f}MB (Δ {final_memory - initial_memory:.2f}MB)[/dim]")
    rich.print(f"[dim]Parsing: {parse_time:.2f}s, Execution: {run_time:.2f}s[/dim]")
    
    # Clean up to free memory
    del codebase
    gc.collect()
