import sys
from pathlib import Path
from typing import Optional

import click
from loguru import logger

from codegen_on_oss.cache import cachedir
from codegen_on_oss.metrics import MetricsProfiler
from codegen_on_oss.outputs.csv_output import CSVOutput
from codegen_on_oss.parser import CodegenParser
from codegen_on_oss.sources import RepoSource, all_sources

logger.remove(0)


@click.group()
def cli():
    pass


@cli.command(name="run-one")
@click.argument("url", type=str)
@click.option(
    "--cache-dir",
    type=click.Path(dir_okay=True),
    help="Cache directory",
    default=cachedir,
)
@click.option(
    "--output-path",
    type=click.Path(dir_okay=True),
    help="Output path",
    default="metrics.csv",
)
@click.option(
    "--commit-hash",
    type=str,
    help="Commit hash to parse",
)
@click.option(
    "--language",
    type=str,
    help="Programming language of the repository",
)
@click.option(
    "--error-output-path",
    type=click.Path(dir_okay=True),
    help="Error output path",
    default=cachedir / "errors.log",
)
@click.option(
    "--debug",
    is_flag=True,
    help="Debug mode",
)
def run_one(
    url: str,
    cache_dir: str | Path = str(cachedir),
    output_path: str = "metrics.csv",
    commit_hash: str | None = None,
    language: str | None = None,
    error_output_path: Path = str(cachedir / "errors.log"),
    debug: bool = False,
):
    """
    Parse a repository with codegen
    """
    logger.add(error_output_path, level="ERROR")
    logger.add(sys.stdout, level="DEBUG" if debug else "INFO")
    output = CSVOutput(MetricsProfiler.fields(), output_path)
    metrics_profiler = MetricsProfiler(output)

    parser = CodegenParser(Path(cache_dir) / "repositories", metrics_profiler)
    success, metrics, error = parser.parse(url, language, commit_hash)
    
    if success:
        logger.info(f"Successfully parsed repository: {url}")
        if metrics:
            logger.info(f"Metrics: {metrics}")
    else:
        logger.error(f"Failed to parse repository: {url}")
        if error:
            logger.error(f"Error: {error}")
    
    return success


@cli.command()
@click.option(
    "--source",
    type=click.Choice(list(all_sources.keys())),
    default="csv",
)
@click.option(
    "--output-path",
    type=click.Path(dir_okay=True),
    help="Output path",
    default="metrics.csv",
)
@click.option(
    "--error-output-path",
    type=click.Path(dir_okay=True),
    help="Error output path",
    default="errors.log",
)
@click.option(
    "--cache-dir",
    type=click.Path(dir_okay=True),
    help="Cache directory",
    default=cachedir,
)
@click.option(
    "--language",
    type=str,
    help="Programming language of the repositories",
)
@click.option(
    "--debug",
    is_flag=True,
    help="Debug mode",
)
def run(
    source: str,
    output_path: str,
    error_output_path: str,
    cache_dir: str,
    language: Optional[str] = None,
    debug: bool = False,
):
    """
    Run codegen parsing pipeline on repositories from a given repository source.
    """
    logger.add(error_output_path, format="{time: HH:mm:ss} {level} {message}", level="ERROR")
    logger.add(
        sys.stdout,
        format="{time: HH:mm:ss} {level} {message}",
        level="DEBUG" if debug else "INFO",
    )

    repo_source = RepoSource.from_source_type(source)
    output = CSVOutput(MetricsProfiler.fields(), output_path)
    metrics_profiler = MetricsProfiler(output)
    parser = CodegenParser(Path(cache_dir) / "repositories", metrics_profiler)
    
    success_count = 0
    failure_count = 0
    
    for repo_url, commit_hash in repo_source:
        logger.info(f"Processing repository: {repo_url} (commit: {commit_hash or 'latest'})")
        success, metrics, error = parser.parse(repo_url, language, commit_hash)
        
        if success:
            success_count += 1
            logger.info(f"Successfully parsed repository: {repo_url}")
        else:
            failure_count += 1
            logger.error(f"Failed to parse repository: {repo_url}")
            if error:
                logger.error(f"Error: {error}")
    
    logger.info(f"Processing complete. Successes: {success_count}, Failures: {failure_count}")


if __name__ == "__main__":
    cli()
