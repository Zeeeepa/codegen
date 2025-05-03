import sys
from pathlib import Path

import click
from loguru import logger

from codegen_on_oss.cache import cachedir
from codegen_on_oss.metrics import MetricsProfiler
from codegen_on_oss.outputs.csv_output import CSVOutput
from codegen_on_oss.parser import CodegenParser
from codegen_on_oss.sources import RepoSource, all_sources
from codegen_on_oss.database.service import DatabaseService, DatabaseConfig
from codegen_on_oss.events.event_bus import Event, EventType, event_bus
from codegen_on_oss.events.handlers import AnalysisHandler, SnapshotHandler
from codegen_on_oss.api.server import run_server
from codegen_on_oss.snapshot.enhanced_snapshot import (
    EnhancedCodebaseSnapshot,
    EnhancedSnapshotManager,
)
from codegen import Codebase

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


@cli.command()
@click.option(
    "--host",
    type=str,
    default="0.0.0.0",
    help="Host to run the API server on",
)
@click.option(
    "--port",
    type=int,
    default=8000,
    help="Port to run the API server on",
)
@click.option(
    "--debug",
    is_flag=True,
    help="Debug mode",
)
def serve(
    host: str = "0.0.0.0",
    port: int = 8000,
    debug: bool = False,
):
    """
    Run the API server for frontend integration.
    """
    logger.add(sys.stdout, level="DEBUG" if debug else "INFO")
    logger.info(f"Starting API server on {host}:{port}")

    # Initialize database
    db_config = DatabaseConfig()
    db_service = DatabaseService(db_config)
    db_service.create_tables()

    # Initialize event handlers
    analysis_handler = AnalysisHandler(db_service)
    snapshot_handler = SnapshotHandler(db_service)

    # Run the server
    run_server(host=host, port=port)


@cli.command()
@click.argument("url", type=str)
@click.option(
    "--commit-hash",
    type=str,
    help="Commit hash to snapshot",
)
@click.option(
    "--output-path",
    type=click.Path(dir_okay=True),
    help="Output path for the snapshot",
    default="snapshot.json",
)
@click.option(
    "--enhanced",
    is_flag=True,
    help="Use enhanced snapshot capabilities",
)
@click.option(
    "--debug",
    is_flag=True,
    help="Debug mode",
)
def snapshot(
    url: str,
    commit_hash: str | None = None,
    output_path: str = "snapshot.json",
    enhanced: bool = False,
    debug: bool = False,
):
    """
    Create a snapshot of a repository.
    """
    logger.add(sys.stdout, level="DEBUG" if debug else "INFO")

    try:
        # Create a codebase from the repository
        logger.info(f"Creating codebase from {url}")
        codebase = Codebase.from_repo(url)

        if commit_hash:
            logger.info(f"Checking out commit {commit_hash}")
            codebase.checkout(commit=commit_hash)

        # Create a snapshot
        if enhanced:
            logger.info("Creating enhanced snapshot")
            snapshot = EnhancedCodebaseSnapshot(codebase, commit_sha=commit_hash)
        else:
            logger.info("Creating basic snapshot")
            from codegen_on_oss.snapshot.codebase_snapshot import CodebaseSnapshot

            snapshot = CodebaseSnapshot(codebase, commit_sha=commit_hash)

        # Save the snapshot to a file
        logger.info(f"Saving snapshot to {output_path}")
        snapshot.save_to_file(output_path)

        logger.info(f"Snapshot created successfully: {snapshot.snapshot_id}")
        logger.info(snapshot.get_summary())

    except Exception as e:
        logger.error(f"Error creating snapshot: {e}")
        sys.exit(1)


@cli.command()
@click.argument("snapshot1", type=click.Path(exists=True))
@click.argument("snapshot2", type=click.Path(exists=True))
@click.option(
    "--output-path",
    type=click.Path(dir_okay=True),
    help="Output path for the comparison",
    default="comparison.json",
)
@click.option(
    "--detail-level",
    type=click.Choice(["summary", "detailed", "full"]),
    default="summary",
    help="Level of detail for the comparison",
)
@click.option(
    "--debug",
    is_flag=True,
    help="Debug mode",
)
def compare(
    snapshot1: str,
    snapshot2: str,
    output_path: str = "comparison.json",
    detail_level: str = "summary",
    debug: bool = False,
):
    """
    Compare two snapshots.
    """
    import json

    logger.add(sys.stdout, level="DEBUG" if debug else "INFO")

    try:
        # Load the snapshots
        logger.info(f"Loading snapshots: {snapshot1} and {snapshot2}")

        # Check if these are enhanced snapshots
        with open(snapshot1, "r") as f:
            data1 = json.load(f)

        with open(snapshot2, "r") as f:
            data2 = json.load(f)

        is_enhanced = "enhanced_metadata" in data1 and "enhanced_metadata" in data2

        if is_enhanced:
            logger.info("Using enhanced snapshot comparison")
            from codegen_on_oss.snapshot.enhanced_snapshot import (
                EnhancedCodebaseSnapshot,
            )

            # We would need to reconstruct the codebases to fully deserialize
            # For now, just use the metadata for comparison
            comparison = {
                "snapshot1": {
                    "id": data1["metadata"]["snapshot_id"],
                    "commit_sha": data1["metadata"]["commit_sha"],
                    "timestamp": data1["metadata"]["timestamp"],
                },
                "snapshot2": {
                    "id": data2["metadata"]["snapshot_id"],
                    "commit_sha": data2["metadata"]["commit_sha"],
                    "timestamp": data2["metadata"]["timestamp"],
                },
                "detail_level": detail_level,
                "files": {
                    "added": [],
                    "removed": [],
                    "modified": [],
                    "unchanged": [],
                    "total_added": 0,
                    "total_removed": 0,
                    "total_modified": 0,
                    "total_unchanged": 0,
                },
            }
        else:
            logger.info("Using basic snapshot comparison")
            from codegen_on_oss.snapshot.codebase_snapshot import CodebaseSnapshot

            snapshot1_obj = CodebaseSnapshot.load_from_file(snapshot1)
            snapshot2_obj = CodebaseSnapshot.load_from_file(snapshot2)

            # Basic comparison
            files1 = {
                filepath: metrics
                for filepath, metrics in snapshot1_obj.file_metrics.items()
            }
            files2 = {
                filepath: metrics
                for filepath, metrics in snapshot2_obj.file_metrics.items()
            }

            added_files = [filepath for filepath in files2 if filepath not in files1]
            removed_files = [filepath for filepath in files1 if filepath not in files2]
            modified_files = []

            for filepath in files1:
                if (
                    filepath in files2
                    and files1[filepath]["content_hash"]
                    != files2[filepath]["content_hash"]
                ):
                    modified_files.append(filepath)

            comparison = {
                "snapshot1": {
                    "id": snapshot1_obj.snapshot_id,
                    "commit_sha": snapshot1_obj.commit_sha,
                    "timestamp": snapshot1_obj.timestamp.isoformat(),
                },
                "snapshot2": {
                    "id": snapshot2_obj.snapshot_id,
                    "commit_sha": snapshot2_obj.commit_sha,
                    "timestamp": snapshot2_obj.timestamp.isoformat(),
                },
                "files": {
                    "added": added_files,
                    "removed": removed_files,
                    "modified": modified_files,
                    "unchanged": [
                        filepath
                        for filepath in files1
                        if filepath in files2
                        and files1[filepath]["content_hash"]
                        == files2[filepath]["content_hash"]
                    ],
                    "total_added": len(added_files),
                    "total_removed": len(removed_files),
                    "total_modified": len(modified_files),
                    "total_unchanged": len(
                        [
                            filepath
                            for filepath in files1
                            if filepath in files2
                            and files1[filepath]["content_hash"]
                            == files2[filepath]["content_hash"]
                        ]
                    ),
                },
            }

        # Save the comparison to a file
        logger.info(f"Saving comparison to {output_path}")
        with open(output_path, "w") as f:
            json.dump(comparison, f, indent=2)

        # Print a summary
        logger.info(f"Comparison created successfully")
        logger.info(f"Added files: {comparison['files']['total_added']}")
        logger.info(f"Removed files: {comparison['files']['total_removed']}")
        logger.info(f"Modified files: {comparison['files']['total_modified']}")
        logger.info(f"Unchanged files: {comparison['files']['total_unchanged']}")

    except Exception as e:
        logger.error(f"Error comparing snapshots: {e}")
        sys.exit(1)


@cli.command()
@click.argument("url", type=str)
@click.option(
    "--commit-hash",
    type=str,
    help="Commit hash to analyze",
)
@click.option(
    "--analysis-type",
    type=click.Choice(["dependency", "complexity", "security", "all"]),
    default="all",
    help="Type of analysis to perform",
)
@click.option(
    "--output-path",
    type=click.Path(dir_okay=True),
    help="Output path for the analysis results",
    default="analysis.json",
)
@click.option(
    "--debug",
    is_flag=True,
    help="Debug mode",
)
def analyze(
    url: str,
    commit_hash: str | None = None,
    analysis_type: str = "all",
    output_path: str = "analysis.json",
    debug: bool = False,
):
    """
    Analyze a repository.
    """
    import json
    from datetime import datetime

    logger.add(sys.stdout, level="DEBUG" if debug else "INFO")

    try:
        # Create a codebase from the repository
        logger.info(f"Creating codebase from {url}")
        codebase = Codebase.from_repo(url)

        if commit_hash:
            logger.info(f"Checking out commit {commit_hash}")
            codebase.checkout(commit=commit_hash)

        # Create a snapshot
        logger.info("Creating snapshot")
        from codegen_on_oss.snapshot.enhanced_snapshot import EnhancedCodebaseSnapshot

        snapshot = EnhancedCodebaseSnapshot(codebase, commit_sha=commit_hash)

        # Perform analysis
        results = {}

        if analysis_type in ["dependency", "all"]:
            logger.info("Performing dependency analysis")
            results["dependency"] = {
                "timestamp": datetime.utcnow().isoformat(),
                "data": {
                    "dependency_graph": snapshot.dependency_graph,
                    "import_metrics": snapshot.import_metrics,
                },
                "summary": "Dependency analysis completed successfully.",
            }

        if analysis_type in ["complexity", "all"]:
            logger.info("Performing complexity analysis")
            results["complexity"] = {
                "timestamp": datetime.utcnow().isoformat(),
                "data": {
                    "function_metrics": snapshot.function_metrics,
                    "average_complexity": sum(
                        func["cyclomatic_complexity"]
                        for func in snapshot.function_metrics.values()
                    )
                    / max(1, len(snapshot.function_metrics)),
                    "max_complexity": (
                        max(
                            [
                                func["cyclomatic_complexity"]
                                for func in snapshot.function_metrics.values()
                            ]
                        )
                        if snapshot.function_metrics
                        else 0
                    ),
                },
                "summary": "Complexity analysis completed successfully.",
            }

        if analysis_type in ["security", "all"]:
            logger.info("Performing security analysis")
            results["security"] = {
                "timestamp": datetime.utcnow().isoformat(),
                "data": snapshot.security_metrics,
                "summary": "Security analysis completed successfully.",
            }

        # Save the analysis results to a file
        logger.info(f"Saving analysis results to {output_path}")
        with open(output_path, "w") as f:
            json.dump(results, f, indent=2)

        logger.info(f"Analysis completed successfully")

    except Exception as e:
        logger.error(f"Error analyzing repository: {e}")
        sys.exit(1)


@cli.command()
@click.option(
    "--db-host",
    type=str,
    default="localhost",
    help="Database host",
)
@click.option(
    "--db-port",
    type=int,
    default=5432,
    help="Database port",
)
@click.option(
    "--db-user",
    type=str,
    default="postgres",
    help="Database user",
)
@click.option(
    "--db-password",
    type=str,
    default="postgres",
    help="Database password",
)
@click.option(
    "--db-name",
    type=str,
    default="codegen_oss",
    help="Database name",
)
@click.option(
    "--debug",
    is_flag=True,
    help="Debug mode",
)
def init_db(
    db_host: str = "localhost",
    db_port: int = 5432,
    db_user: str = "postgres",
    db_password: str = "postgres",
    db_name: str = "codegen_oss",
    debug: bool = False,
):
    """
    Initialize the database.
    """
    logger.add(sys.stdout, level="DEBUG" if debug else "INFO")

    try:
        # Create database configuration
        db_config = DatabaseConfig(
            host=db_host,
            port=db_port,
            username=db_user,
            password=db_password,
            database=db_name,
            echo=debug,
        )

        # Create database service
        db_service = DatabaseService(db_config)

        # Create tables
        logger.info("Creating database tables")
        db_service.create_tables()

        logger.info("Database initialized successfully")

    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        sys.exit(1)


if __name__ == "__main__":
    cli()
