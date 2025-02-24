import subprocess
from importlib.metadata import version
from pathlib import Path

import click
import rich
from rich.box import ROUNDED
from rich.panel import Panel

from codegen.configs.models.secrets import SecretsConfig
from codegen.git.repo_operator.local_git_repo import LocalGitRepo
from codegen.git.schemas.repo_config import RepoConfig
from codegen.shared.network.port import get_free_port


@click.command(name="start")
@click.option("--platform", "-t", type=click.Choice(["linux/amd64", "linux/arm64", "linux/amd64,linux/arm64"]), default="linux/amd64,linux/arm64", help="Target platform(s) for the Docker image")
@click.option("--port", "-p", type=int, default=None, help="Port to run the server on")
@click.option("--detached", "-d", is_flag=True, default=False, help="Starts up the server as detached background process")
@click.option("--local", is_flag=True, default=False, help="If true, interacts with the mounted local repository. If false, interacts with the repository copied into the image.")
def start_command(port: int | None, platform: str, detached: bool, local: bool):
    """Starts a local codegen server"""
    codegen_version = version("codegen")
    rich.print(f"[bold green]Codegen version:[/bold green] {codegen_version}")
    codegen_root = Path(__file__).parent.parent.parent.parent.parent.parent
    if port is None:
        port = get_free_port()

    try:
        repo_path = Path.cwd().resolve()
        repo_config = RepoConfig.from_repo_path(repo_path)
        rich.print("[bold blue]Building Docker image...[/bold blue]")
        _build_docker_image(repo_config, codegen_root, platform, local)
        rich.print("[bold blue]Starting Docker container...[/bold blue]")
        _run_docker_container(repo_config, port, detached, local)
        rich.print(Panel(f"[green]Server started successfully![/green]\nAccess the server at: [bold]http://0.0.0.0:{port}[/bold]", box=ROUNDED, title="Codegen Server"))
    except subprocess.CalledProcessError as e:
        rich.print(f"[bold red]Error:[/bold red] Failed to {e.cmd[0]} Docker container")
        raise click.Abort()
    except Exception as e:
        rich.print(f"[bold red]Error:[/bold red] {e!s}")
        raise click.Abort()


def _build_docker_image(repo_config: RepoConfig, codegen_root: Path, platform: str, local: bool):
    build_arg = [] if local else ["--build-arg", f"LOCAL_REPO_PATH={repo_config.repo_path}", "--build-arg", f"REPO_NAME={repo_config.name}"]
    dockerfile = "Dockerfile-runner-mount" if local else "Dockerfile-runner"
    build_cmd = [
        "docker",
        "buildx",
        "build",
        *build_arg,
        "--platform",
        platform,
        "-f",
        str(codegen_root / dockerfile),
        "-t",
        "codegen-runner",
        "--load",
        str(codegen_root),
    ]
    rich.print(f"build_cmd: {str.join(' ', build_cmd)}")
    subprocess.run(build_cmd, check=True)


def _run_docker_container(repo_config: RepoConfig, port: int, detached: bool, local: bool):
    container_repo_path = f"/app/git/{repo_config.name}"
    envvars = {
        "REPOSITORY_LANGUAGE": repo_config.language.value,
        "REPOSITORY_OWNER": LocalGitRepo(repo_config.repo_path).owner,
        "REPOSITORY_PATH": container_repo_path,
        "GITHUB_TOKEN": SecretsConfig().github_token,
    }
    envvars_args = [arg for k, v in envvars.items() for arg in ("--env", f"{k}={v}")]
    mount_args = ["-v", f"{repo_config.repo_path}:{container_repo_path}"] if local else []
    run_mode = "-d" if detached else "-it"
    entry_point = f"uv run --frozen uvicorn codegen.runner.sandbox.server:app --host 0.0.0.0 --port {port}"
    run_cmd = ["docker", "run", run_mode, "-p", f"{port}:{port}", *mount_args, *envvars_args, "codegen-runner", entry_point]

    rich.print(f"run_cmd: {str.join(' ', run_cmd)}")
    subprocess.run(run_cmd, check=True)
