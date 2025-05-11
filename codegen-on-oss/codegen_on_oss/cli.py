import os
import sys
from pathlib import Path
from typing import Optional

import click
from loguru import logger

from .metrics import MetricsProfiler
from .parser import CodegenParser, ParseRunError
from .sources import CSVInputSource, GithubSource, RepoSource

# Add import for the codebase analyzer
from .analysis.codebase_analyzer import CodebaseAnalyzer

logger.remove(0)


@click.group()
def cli():
    """Codegen OSS Parser CLI."""
    pass


@cli.command()
@click.option(
    "--source",
    type=click.Choice(["csv", "github"]),
    default="csv",
    help="Source of repository URLs",
)
@click.option(
    "--output-path",
    type=click.Path(dir_okay=False, writable=True),
    default="metrics.csv",
    help="Path to write metrics CSV",
)
@click.option(
    "--error-output-path",
    type=click.Path(dir_okay=False, writable=True),
    default="errors.log",
    help="Path to write error logs",
)
@click.option(
    "--cache-dir",
    type=click.Path(file_okay=False, writable=True),
    default=Path.home() / ".cache" / "codegen-on-oss",
    help="Directory to cache repositories",
)
def run(
    source: str,
    output_path: str,
    error_output_path: str,
    cache_dir: Path,
) -> None:
    """Run the parser on multiple repositories."""
    logger.add(
        error_output_path, format="{time: HH:mm:ss} {level} {message}", level="ERROR"
    )
    logger.add(
        sys.stdout,
        format="{time: HH:mm:ss} {level} {message}",
        level="DEBUG",
    )

    repo_source = RepoSource.from_source_type(source)
    output = CSVOutput(MetricsProfiler.fields(), output_path)
    metrics_profiler = MetricsProfiler(output)
    parser = CodegenParser(Path(cache_dir) / "repositories", metrics_profiler)
    for repo_url, commit_hash in repo_source:
        parser.parse(repo_url, commit_hash)


@cli.command()
@click.option(
    "--repo-url",
    type=str,
    required=True,
    help="URL of the repository to parse",
)
@click.option(
    "--output-path",
    type=click.Path(dir_okay=False, writable=True),
    default="metrics.csv",
    help="Path to write metrics CSV",
)
@click.option(
    "--error-output-path",
    type=click.Path(dir_okay=False, writable=True),
    default="errors.log",
    help="Path to write error logs",
)
@click.option(
    "--cache-dir",
    type=click.Path(file_okay=False, writable=True),
    default=Path.home() / ".cache" / "codegen-on-oss",
    help="Directory to cache repositories",
)
def run_one(
    repo_url: str,
    output_path: str,
    error_output_path: str,
    cache_dir: Path,
) -> None:
    """Run the parser on a single repository."""
    logger.add(error_output_path, level="ERROR")
    logger.add(sys.stdout, level="DEBUG")
    output = CSVOutput(MetricsProfiler.fields(), output_path)
    metrics_profiler = MetricsProfiler(output)
    parser = CodegenParser(Path(cache_dir) / "repositories", metrics_profiler)
    parser.parse(repo_url)


@cli.command()
@click.option(
    "--repo-url",
    type=str,
    help="URL of the repository to analyze",
)
@click.option(
    "--repo-path",
    type=click.Path(exists=True, file_okay=False),
    help="Local path to the repository to analyze",
)
@click.option(
    "--language",
    type=str,
    help="Programming language of the codebase (auto-detected if not provided)",
)
@click.option(
    "--categories",
    multiple=True,
    help="Categories to analyze (default: all)",
)
@click.option(
    "--output-format",
    type=click.Choice(["json", "html", "console"]),
    default="console",
    help="Output format",
)
@click.option(
    "--output-file",
    type=click.Path(dir_okay=False, writable=True),
    help="Path to the output file",
)
def analyze(
    repo_url: Optional[str],
    repo_path: Optional[str],
    language: Optional[str],
    categories: Optional[tuple],
    output_format: str,
    output_file: Optional[str],
) -> None:
    """Analyze a codebase and generate a report."""
    if not repo_url and not repo_path:
        click.echo("Error: Either --repo-url or --repo-path must be provided")
        sys.exit(1)
    
    try:
        # Initialize the analyzer
        analyzer = CodebaseAnalyzer(
            repo_url=repo_url,
            repo_path=repo_path,
            language=language
        )
        
        # Perform the analysis
        results = analyzer.analyze(
            categories=list(categories) if categories else None,
            output_format=output_format,
            output_file=output_file
        )
        
        # Print success message
        if output_format == "json" and output_file:
            click.echo(f"Analysis results saved to {output_file}")
        elif output_format == "html":
            click.echo(f"HTML report saved to {output_file or 'codebase_analysis_report.html'}")
        
    except Exception as e:
        click.echo(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    cli()
