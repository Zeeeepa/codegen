import os
import sys
import logging
import argparse
from typing import List, Optional

from codegen_on_oss.config import settings, configure_logging
from codegen_on_oss.database.connection import init_db

import sys
from pathlib import Path

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
    parser.parse(url, commit_hash)


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
    "--debug",
    is_flag=True,
    help="Debug mode",
)
def run(
    source: str,
    output_path: str,
    error_output_path: str,
    cache_dir: str,
    debug: bool,
):
    """
    Run codegen parsing pipeline on repositories from a given repository source.
    """
    logger.add(
        error_output_path, format="{time: HH:mm:ss} {level} {message}", level="ERROR"
    )
    logger.add(
        sys.stdout,
        format="{time: HH:mm:ss} {level} {message}",
        level="DEBUG" if debug else "INFO",
    )

    repo_source = RepoSource.from_source_type(source)
    output = CSVOutput(MetricsProfiler.fields(), output_path)
    metrics_profiler = MetricsProfiler(output)
    parser = CodegenParser(Path(cache_dir) / "repositories", metrics_profiler)
    for repo_url, commit_hash in repo_source:
        parser.parse(repo_url, commit_hash)


def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(description="Codegen Analysis CLI")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Server command
    server_parser = subparsers.add_parser("server", help="Start the API server")
    server_parser.add_argument("--host", help="Host to bind to", default=settings.api_host)
    server_parser.add_argument("--port", type=int, help="Port to bind to", default=settings.api_port)
    server_parser.add_argument("--workers", type=int, help="Number of workers", default=settings.api_workers)
    server_parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    
    # Worker command
    worker_parser = subparsers.add_parser("worker", help="Start task queue workers")
    worker_parser.add_argument("--workers", type=int, help="Number of workers", default=settings.max_workers)
    
    # Init command
    init_parser = subparsers.add_parser("init", help="Initialize the database")
    
    # Analyze command
    analyze_parser = subparsers.add_parser("analyze", help="Analyze a repository")
    analyze_parser.add_argument("repo_url", help="URL of the repository to analyze")
    analyze_parser.add_argument("--commit", help="Commit SHA to analyze")
    analyze_parser.add_argument("--branch", help="Branch to analyze")
    analyze_parser.add_argument("--types", nargs="+", help="Analysis types to perform")
    
    # Snapshot command
    snapshot_parser = subparsers.add_parser("snapshot", help="Create a snapshot of a repository")
    snapshot_parser.add_argument("repo_url", help="URL of the repository to snapshot")
    snapshot_parser.add_argument("--commit", help="Commit SHA to snapshot")
    snapshot_parser.add_argument("--branch", help="Branch to snapshot")
    
    # Parse arguments
    args = parser.parse_args()
    
    # Configure logging
    configure_logging()
    
    # Execute command
    if args.command == "server":
        # Update settings from command line
        settings.api_host = args.host
        settings.api_port = args.port
        settings.api_workers = args.workers
        settings.debug = args.debug
        
        # Start the server
        from codegen_on_oss.api.app import start
        start()
    
    elif args.command == "worker":
        # Start task queue workers
        from codegen_on_oss.tasks.queue import task_queue
        task_queue.start_worker(args.workers)
    
    elif args.command == "init":
        # Initialize the database
        init_db(create_tables=True)
        print("Database initialized successfully")
    
    elif args.command == "analyze":
        # Run analysis synchronously
        import asyncio
        from codegen_on_oss.database.connection import get_db_session
        from codegen_on_oss.snapshot.snapshot_service import SnapshotService
        from codegen_on_oss.storage.service import StorageService
        from codegen_on_oss.analysis.analysis_service import AnalysisService
        
        async def run_analysis():
            with get_db_session() as db_session:
                storage_service = StorageService()
                snapshot_service = SnapshotService(db_session, storage_service)
                analysis_service = AnalysisService(db_session, snapshot_service)
                
                result = await analysis_service.analyze_codebase(
                    repo_url=args.repo_url,
                    commit_sha=args.commit,
                    branch=args.branch,
                    analysis_types=args.types
                )
                
                return result
        
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(run_analysis())
        
        import json
        print(json.dumps(result, indent=2))
    
    elif args.command == "snapshot":
        # Create a snapshot synchronously
        import asyncio
        from codegen_on_oss.database.connection import get_db_session
        from codegen_on_oss.snapshot.snapshot_service import SnapshotService
        from codegen_on_oss.storage.service import StorageService
        
        async def create_snapshot():
            with get_db_session() as db_session:
                storage_service = StorageService()
                snapshot_service = SnapshotService(db_session, storage_service)
                
                snapshot = await snapshot_service.create_snapshot(
                    repo_url=args.repo_url,
                    commit_sha=args.commit,
                    branch=args.branch
                )
                
                return {
                    "snapshot_id": str(snapshot.id),
                    "repository": snapshot.repository,
                    "commit_sha": snapshot.commit_sha,
                    "branch": snapshot.branch,
                    "created_at": snapshot.created_at.isoformat(),
                    "metadata": snapshot.metadata
                }
        
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(create_snapshot())
        
        import json
        print(json.dumps(result, indent=2))
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
