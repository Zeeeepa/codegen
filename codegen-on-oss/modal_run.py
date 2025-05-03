import os
import re
import sys
from pathlib import Path
from typing import Any

import modal
from codegen_on_oss.bucket_store import BucketStore
from codegen_on_oss.cache import cachedir
from codegen_on_oss.metrics import MetricsProfiler
from codegen_on_oss.parser import CodegenParser
from codegen_on_oss.sources import RepoSource
from loguru import logger

parse_app = modal.App("codegen-oss-parse")


codegen_repo_volume = modal.Volume.from_name(
    os.getenv("CODEGEN_MODAL_REPO_VOLUME", "codegen-oss-repo-volume"),
    create_if_missing=True,
)


codegen_input_volume = modal.Volume.from_name(
    os.getenv("CODEGEN_MODAL_INPUT_VOLUME", "codegen-oss-input-volume"),
    create_if_missing=True,
)

try:
    aws_secrets = modal.Secret.from_name(
        os.getenv("CODEGEN_MODAL_SECRET_NAME", "codegen-oss-bucket-credentials")
    )
except modal.exception.NotFoundError:
    if Path(".env").exists():
        aws_secrets = modal.Secret.from_dotenv()
    else:
        aws_secrets = modal.Secret.from_dict({
            "AWS_ACCESS_KEY_ID": os.getenv("AWS_ACCESS_KEY_ID"),
            "AWS_SECRET_ACCESS_KEY": os.getenv("AWS_SECRET_ACCESS_KEY"),
            "BUCKET_NAME": os.getenv("BUCKET_NAME"),
            "GITHUB_TOKEN": os.getenv("GITHUB_TOKEN"),
        })


@parse_app.function(
    cpu=4,
    memory=16384,
    timeout=3600 * 8,
    secrets=[aws_secrets],
    volumes={
        str(cachedir.absolute()): codegen_repo_volume,
        "/app/inputs": codegen_input_volume,
    },
    image=modal.Image.debian_slim(python_version="3.13")
    .pip_install("uv")
    .apt_install("git")  # required by codegen sdk
    .workdir("/app")
    .add_local_file("uv.lock", remote_path="/app/uv.lock", copy=True)
    .add_local_file("pyproject.toml", remote_path="/app/pyproject.toml", copy=True)
    .run_commands("uv sync --frozen --no-install-project")
    .env({"PATH": "/app/.venv/bin:$PATH"})
    .add_local_python_source("codegen_on_oss")
    .add_local_dir("codegen_on_oss", remote_path="/app/codegen_on_oss"),
)
def parse_repo_on_modal(
    source: str,
    env: dict[str, str],
    log_output_path: str = "output.logs",
    metrics_output_path: str = "metrics.csv",
):
    """Parse repositories on Modal.

    Args:
        source: The source of the repositories to parse.
        env: The environment variables to use.
        log_output_path: The path to the log file.
        metrics_output_path: The path to the metrics file.
    """
    os.environ.update(env)

    logger.add(
        log_output_path,
        format="{time: HH:mm:ss} {level} {message}",
        level="INFO",
    )
    logger.add(sys.stdout, format="{time: HH:mm:ss} {level} {message}", level="DEBUG")

    repo_source = RepoSource.from_source_type(source)
    metrics_profiler = MetricsProfiler(metrics_output_path)

    parser = CodegenParser(Path(cachedir) / "repositories", metrics_profiler)
    for repo_url, commit_hash in repo_source:
        # Refresh any updating repo data from other instances
        codegen_repo_volume.reload()
        try:
            parser.parse(repo_url, commit_hash)
        except Exception as e:
            logger.exception(f"Error parsing repository {repo_url}: {e}")
        finally:
            # Commit any cache changes to the repo volume
            codegen_repo_volume.commit()

    store = BucketStore(bucket_name=os.getenv("BUCKET_NAME", "codegen-oss-parse"))
    log_key = store.upload_file(log_output_path, "output.logs")
    metrics_key = store.upload_file(metrics_output_path, "metrics.csv")

    logger.info(f"Uploaded logs to {log_key} in bucket {store.bucket_name}")
    logger.info(f"Uploaded metrics to {metrics_key} in bucket {store.bucket_name}")


@parse_app.local_entrypoint()
def main(
    source: str = "single",
    csv_file: str = "",
    single_url: str = "",
    single_commit: str = "",
    github_language: str = "",
    github_heuristic: str = "",
    github_num_repos: int = 10,
):
    """Main entrypoint for the parse app."""
    if source == "csv":
        input_path = Path(csv_file).relative_to(".")
        with codegen_input_volume.batch_upload(force=True) as b:
            b.put_file(csv_file, input_path)

        env = {
            "CSV_FILE_PATH": f"/app/inputs/{input_path}",
        }
    elif source == "single":
        env = {"SINGLE_URL": single_url}
        if single_commit:
            env["SINGLE_COMMIT"] = single_commit
    elif source == "github":
        env = {
            "GITHUB_LANGUAGE": github_language,
            "GITHUB_HEURISTIC": github_heuristic,
            "GITHUB_NUM_REPOS": str(github_num_repos),
        }
    else:
        msg = f"Invalid source: {source}"
        raise ValueError(msg)

    return parse_repo_on_modal.remote(
        source=source,
        env=env,
    )


def parse_repo(source: str, env: dict[str, str] | None = None) -> dict[str, Any]:
    """Parse a repository using Modal.

    Args:
        source: Repository source (URL or local path)
        env: Environment variables to pass to the parser

    Returns:
        Parsed repository data
    """
    if env is None:
        env = {}

    # Check if source is a URL
    if source.startswith("http://") or source.startswith("https://"):
        # It's a URL, use it directly
        pass
    # Check if source is a local path
    elif os.path.exists(source):
        # It's a local path, convert to absolute path
        source = os.path.abspath(source)
    # Check if source is a GitHub repo in the format owner/repo
    elif re.match(r"^[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+$", source):
        # It's a GitHub repo, convert to URL
        source = f"https://github.com/{source}"
    else:
        # Invalid source
        msg = f"Invalid source: {source}"
        raise ValueError(msg)

    return parse_repo_on_modal.remote(
        source=source,
        env=env,
    )
