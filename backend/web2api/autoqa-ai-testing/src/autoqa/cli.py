"""
Command-line interface for AutoQA testing system.

Provides commands for running tests, validating specs, and generating CI configs.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from datetime import UTC
from pathlib import Path

import structlog

from autoqa import __version__
from autoqa.ci.generator import CIProvider, CITemplateGenerator
from autoqa.dsl.models import TestSpec, TestSuite
from autoqa.dsl.parser import DSLParseError, DSLParser
from autoqa.runner.self_healing import SelfHealingEngine
from autoqa.runner.test_runner import StepStatus, TestRunner, TestRunResult
from autoqa.storage.artifact_manager import ArtifactManager

logger = structlog.get_logger(__name__)


def main() -> int:
    """Main entry point for CLI."""
    parser = create_parser()
    args = parser.parse_args()

    configure_logging(args.verbose if hasattr(args, "verbose") else False)

    if not hasattr(args, "func"):
        parser.print_help()
        return 1

    try:
        return args.func(args)
    except KeyboardInterrupt:
        print("\nInterrupted by user")
        return 130
    except Exception as e:
        logger.error("Command failed", error=str(e))
        if hasattr(args, "verbose") and args.verbose:
            raise
        print(f"Error: {e}", file=sys.stderr)
        return 1


def create_parser() -> argparse.ArgumentParser:
    """Create argument parser."""
    parser = argparse.ArgumentParser(
        prog="autoqa",
        description="AutoQA AI Testing System - AI-powered test automation",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"autoqa {__version__}",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    run_parser = subparsers.add_parser("run", help="Run test specifications")
    run_parser.add_argument(
        "paths",
        nargs="+",
        help="Path(s) to test specification files or directories",
    )
    run_parser.add_argument(
        "--environment", "-e",
        default="default",
        help="Target environment",
    )
    run_parser.add_argument(
        "--parallel",
        action="store_true",
        help="Run tests in parallel",
    )
    run_parser.add_argument(
        "--max-parallel",
        type=int,
        default=5,
        help="Maximum parallel tests",
    )
    run_parser.add_argument(
        "--record-video",
        action="store_true",
        help="Record video of test execution",
    )
    run_parser.add_argument(
        "--artifacts-dir",
        default="./artifacts",
        help="Directory for test artifacts",
    )
    run_parser.add_argument(
        "--output-format",
        choices=["json", "junit", "html"],
        default="json",
        help="Output format for results",
    )
    run_parser.add_argument(
        "--output-file",
        help="Output file path",
    )
    run_parser.add_argument(
        "--var",
        action="append",
        default=[],
        dest="variables",
        metavar="KEY=VALUE",
        help="Set variable (can be repeated)",
    )
    run_parser.add_argument(
        "--healing-history",
        help="Path to self-healing history file",
    )
    run_parser.add_argument(
        "--default-timeout",
        type=int,
        default=10000,
        help="Default timeout in milliseconds (default: 10000)",
    )
    run_parser.add_argument(
        "--no-network-idle-wait",
        action="store_true",
        help="Disable waiting for network idle after navigation actions",
    )
    run_parser.add_argument(
        "--fast-mode",
        action="store_true",
        help="Enable fast mode with reduced timeouts (5000ms default, 1000ms network idle)",
    )
    run_parser.add_argument(
        "--versioned",
        action="store_true",
        help="Enable versioned test tracking (save snapshots for comparison)",
    )
    run_parser.add_argument(
        "--versioning-path",
        default=".autoqa/history",
        help="Path to store version history (default: .autoqa/history)",
    )
    run_parser.set_defaults(func=cmd_run)

    # History command - list test versions
    history_parser = subparsers.add_parser("history", help="List version history for a test")
    history_parser.add_argument(
        "test_name",
        help="Name of the test to show history for",
    )
    history_parser.add_argument(
        "--storage-path",
        default=".autoqa/history",
        help="Path to version history storage",
    )
    history_parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Maximum number of versions to show",
    )
    history_parser.add_argument(
        "--format",
        choices=["table", "json"],
        default="table",
        dest="output_format",
        help="Output format",
    )
    history_parser.set_defaults(func=cmd_history)

    # Diff command - compare versions
    diff_parser = subparsers.add_parser("diff", help="Compare two test versions")
    diff_parser.add_argument(
        "test_name",
        help="Name of the test to compare",
    )
    diff_parser.add_argument(
        "--from",
        dest="from_date",
        help="Start date (YYYY-MM-DD) or version ID",
    )
    diff_parser.add_argument(
        "--to",
        dest="to_date",
        help="End date (YYYY-MM-DD) or version ID",
    )
    diff_parser.add_argument(
        "--latest",
        type=int,
        default=0,
        help="Compare last N runs (e.g., --latest 2 compares last 2 runs)",
    )
    diff_parser.add_argument(
        "--storage-path",
        default=".autoqa/history",
        help="Path to version history storage",
    )
    diff_parser.add_argument(
        "--output",
        choices=["terminal", "html", "json"],
        default="terminal",
        help="Output format for diff report",
    )
    diff_parser.add_argument(
        "--output-file",
        help="Path to save the diff report",
    )
    diff_parser.set_defaults(func=cmd_diff)

    validate_parser = subparsers.add_parser("validate", help="Validate test specifications")
    validate_parser.add_argument(
        "paths",
        nargs="+",
        help="Path(s) to test specification files",
    )
    validate_parser.set_defaults(func=cmd_validate)

    ci_parser = subparsers.add_parser("ci", help="Generate CI/CD configuration")
    ci_parser.add_argument(
        "provider",
        choices=["github", "gitlab", "jenkins", "azure", "circleci"],
        help="CI/CD provider",
    )
    ci_parser.add_argument(
        "--test-paths",
        nargs="+",
        default=["tests/"],
        help="Paths to test specifications",
    )
    ci_parser.add_argument(
        "--output", "-o",
        help="Output file path",
    )
    ci_parser.add_argument(
        "--python-version",
        default="3.12",
        help="Python version",
    )
    ci_parser.add_argument(
        "--parallel",
        action="store_true",
        help="Enable parallel execution",
    )
    ci_parser.add_argument(
        "--nodes",
        type=int,
        default=1,
        help="Number of parallel nodes",
    )
    ci_parser.set_defaults(func=cmd_ci)

    server_parser = subparsers.add_parser("server", help="Start API server")
    server_parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Server host",
    )
    server_parser.add_argument(
        "--port",
        type=int,
        default=8080,
        help="Server port",
    )
    server_parser.set_defaults(func=cmd_server)

    # Build command - Auto Test Builder
    build_parser = subparsers.add_parser(
        "build",
        help="Auto-generate YAML test specification from a webpage",
    )
    build_parser.add_argument(
        "url",
        help="Starting page URL to analyze",
    )
    build_parser.add_argument(
        "--username", "-u",
        help="Username for authentication (optional)",
    )
    build_parser.add_argument(
        "--password", "-p",
        help="Password for authentication (optional)",
    )
    build_parser.add_argument(
        "--depth", "-d",
        type=int,
        default=1,
        help="Crawl depth for same-domain pages (default: 1)",
    )
    build_parser.add_argument(
        "--max-pages",
        type=int,
        default=10,
        help="Maximum number of pages to analyze (default: 10)",
    )
    build_parser.add_argument(
        "--output", "-o",
        help="Output file path for generated YAML (default: stdout)",
    )
    build_parser.add_argument(
        "--include-hidden",
        action="store_true",
        help="Include hidden elements in analysis",
    )
    build_parser.add_argument(
        "--timeout",
        type=int,
        default=30000,
        help="Timeout in milliseconds for page operations (default: 30000)",
    )
    build_parser.add_argument(
        "--exclude",
        action="append",
        default=[],
        dest="exclude_patterns",
        metavar="PATTERN",
        help="Regex pattern for URLs to exclude (can be repeated)",
    )
    build_parser.add_argument(
        "--include",
        action="append",
        default=[],
        dest="include_patterns",
        metavar="PATTERN",
        help="Regex pattern for URLs to include (can be repeated)",
    )
    build_parser.set_defaults(func=cmd_build)

    return parser


def configure_logging(verbose: bool) -> None:
    """Configure structured logging."""
    level = "DEBUG" if verbose else "INFO"
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.dev.ConsoleRenderer() if verbose else structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    import logging

    logging.basicConfig(level=getattr(logging, level))


def cmd_run(args: argparse.Namespace) -> int:
    """Run test specifications."""
    return asyncio.run(_cmd_run_async(args))


async def _cmd_run_async(args: argparse.Namespace) -> int:
    """Async implementation of cmd_run."""
    from dotenv import load_dotenv
    from owl_browser import OwlBrowser, RemoteConfig

    # Load environment variables from .env file
    load_dotenv()

    parser = DSLParser()
    specs: list[TestSpec | TestSuite] = []

    for path_str in args.paths:
        path = Path(path_str)
        if path.is_dir():
            specs.extend(parser.parse_directory(path))
        elif path.is_file():
            specs.append(parser.parse_file(path))
        else:
            print(f"Warning: Path not found: {path}", file=sys.stderr)

    if not specs:
        print("No test specifications found", file=sys.stderr)
        return 1

    variables = {}
    for var in args.variables:
        if "=" in var:
            key, value = var.split("=", 1)
            variables[key] = value

    healing_engine = SelfHealingEngine(
        history_path=args.healing_history,
        enable_learning=True,
    )

    ArtifactManager(storage_path=args.artifacts_dir)

    # Remote browser configuration - required
    owl_browser_url = os.getenv("OWL_BROWSER_URL")
    owl_browser_token = os.getenv("OWL_BROWSER_TOKEN")

    if not owl_browser_url:
        print("Error: OWL_BROWSER_URL environment variable is required", file=sys.stderr)
        print("Set OWL_BROWSER_URL in .env file or environment", file=sys.stderr)
        return 1

    logger.info("Connecting to remote browser", url=owl_browser_url)
    # SDK v2: api_prefix="" for direct connection without /api prefix
    remote_config = RemoteConfig(url=owl_browser_url, token=owl_browser_token, api_prefix="")
    browser = OwlBrowser(remote_config)
    await browser.connect()

    # Determine timeout settings based on CLI arguments
    if args.fast_mode:
        default_timeout = 5000
        network_idle_timeout = 1000
        wait_for_network_idle = False
    else:
        default_timeout = args.default_timeout
        network_idle_timeout = 2000
        wait_for_network_idle = not args.no_network_idle_wait

    runner = TestRunner(
        browser=browser,
        healing_engine=healing_engine,
        artifact_dir=args.artifacts_dir,
        record_video=args.record_video,
        screenshot_on_failure=True,
        wait_for_network_idle=wait_for_network_idle,
        default_timeout_ms=default_timeout,
        network_idle_timeout_ms=network_idle_timeout,
        enable_versioning=args.versioned,
        versioning_storage_path=args.versioning_path,
    )

    all_results: list[TestRunResult] = []

    try:
        for spec in specs:
            if isinstance(spec, TestSuite):
                results = await runner.run_suite(spec, variables=variables)
                all_results.extend(results)
            else:
                result = await runner.run_spec(spec, variables=variables)
                all_results.append(result)
    finally:
        await browser.close()

    output = format_results(all_results, args.output_format)

    if args.output_file:
        Path(args.output_file).write_text(output)
        print(f"Results written to {args.output_file}")
    else:
        print(output)

    passed = sum(1 for r in all_results if r.status == StepStatus.PASSED)
    failed = sum(1 for r in all_results if r.status == StepStatus.FAILED)

    print(f"\nSummary: {passed} passed, {failed} failed, {len(all_results)} total")

    return 0 if failed == 0 else 1


def format_results(results: list[TestRunResult], format_type: str) -> str:
    """Format test results."""
    if format_type == "json":
        return json.dumps(
            [
                {
                    "test_name": r.test_name,
                    "status": r.status,
                    "duration_ms": r.duration_ms,
                    "passed_steps": r.passed_steps,
                    "failed_steps": r.failed_steps,
                    "healed_steps": r.healed_steps,
                    "error": r.error,
                }
                for r in results
            ],
            indent=2,
        )

    elif format_type == "junit":
        lines = ['<?xml version="1.0" encoding="UTF-8"?>']
        lines.append(f'<testsuites tests="{len(results)}">')

        for result in results:
            lines.append(
                f'  <testsuite name="{result.test_name}" tests="{result.total_steps}" '
                f'failures="{result.failed_steps}" time="{result.duration_ms / 1000:.3f}">'
            )

            for step in result.step_results:
                lines.append(
                    f'    <testcase name="{step.step_name or step.action}" '
                    f'time="{step.duration_ms / 1000:.3f}">'
                )
                if step.status == StepStatus.FAILED and step.error:
                    lines.append(f'      <failure message="{step.error}"/>')
                lines.append("    </testcase>")

            lines.append("  </testsuite>")

        lines.append("</testsuites>")
        return "\n".join(lines)

    elif format_type == "html":
        lines = ["<!DOCTYPE html>", "<html>", "<head>", "<title>AutoQA Test Results</title>"]
        lines.append("<style>")
        lines.append("body { font-family: sans-serif; margin: 20px; }")
        lines.append(".passed { color: green; } .failed { color: red; }")
        lines.append("table { border-collapse: collapse; width: 100%; }")
        lines.append("th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }")
        lines.append("</style>")
        lines.append("</head><body>")
        lines.append("<h1>AutoQA Test Results</h1>")
        lines.append("<table>")
        lines.append("<tr><th>Test</th><th>Status</th><th>Duration</th><th>Steps</th></tr>")

        for result in results:
            status_class = "passed" if result.status == StepStatus.PASSED else "failed"
            lines.append(
                f'<tr class="{status_class}">'
                f"<td>{result.test_name}</td>"
                f"<td>{result.status}</td>"
                f"<td>{result.duration_ms}ms</td>"
                f"<td>{result.passed_steps}/{result.total_steps}</td>"
                "</tr>"
            )

        lines.append("</table>")
        lines.append("</body></html>")
        return "\n".join(lines)

    return str(results)


def cmd_validate(args: argparse.Namespace) -> int:
    """Validate test specifications."""
    parser = DSLParser()
    errors = 0

    for path_str in args.paths:
        path = Path(path_str)

        if not path.exists():
            print(f"Error: Path not found: {path}", file=sys.stderr)
            errors += 1
            continue

        try:
            if path.is_dir():
                specs = parser.parse_directory(path)
                print(f"Valid: {path} ({len(specs)} files)")
            else:
                spec = parser.parse_file(path)
                steps = len(spec.steps) if hasattr(spec, "steps") else len(spec.tests)
                print(f"Valid: {path} ({spec.name}, {steps} steps)")
        except DSLParseError as e:
            print(f"Invalid: {path}", file=sys.stderr)
            print(f"  {e}", file=sys.stderr)
            errors += 1

    if errors:
        print(f"\n{errors} file(s) with errors", file=sys.stderr)
        return 1

    print("\nAll files valid")
    return 0


def cmd_ci(args: argparse.Namespace) -> int:
    """Generate CI/CD configuration."""
    provider_map = {
        "github": CIProvider.GITHUB_ACTIONS,
        "gitlab": CIProvider.GITLAB_CI,
        "jenkins": CIProvider.JENKINS,
        "azure": CIProvider.AZURE_PIPELINES,
        "circleci": CIProvider.CIRCLECI,
    }

    provider = provider_map[args.provider]
    generator = CITemplateGenerator()

    output_files = {
        CIProvider.GITHUB_ACTIONS: ".github/workflows/autoqa.yml",
        CIProvider.GITLAB_CI: ".gitlab-ci.yml",
        CIProvider.JENKINS: "Jenkinsfile",
        CIProvider.AZURE_PIPELINES: "azure-pipelines.yml",
        CIProvider.CIRCLECI: ".circleci/config.yml",
    }

    content = generator.generate(
        provider=provider,
        test_paths=args.test_paths,
        python_version=args.python_version,
        node_count=args.nodes,
        parallel=args.parallel,
    )

    output_path = args.output or output_files[provider]

    if args.output:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        Path(output_path).write_text(content)
        print(f"Configuration written to {output_path}")
    else:
        print(content)

    return 0


def cmd_history(args: argparse.Namespace) -> int:
    """List version history for a test."""
    from autoqa.versioning.history_tracker import TestRunHistory

    tracker = TestRunHistory(storage_path=args.storage_path)
    snapshots = tracker.get_snapshots(args.test_name)

    if not snapshots:
        print(f"No version history found for test: {args.test_name}")
        print("\nAvailable tests with history:")
        for test in tracker.list_tests():
            print(f"  - {test}")
        return 0

    # Limit results
    if args.limit > 0:
        snapshots = snapshots[-args.limit:]

    if args.output_format == "json":
        output = json.dumps(
            [
                {
                    "version_id": s.version_id,
                    "timestamp": s.timestamp.isoformat(),
                    "status": s.test_status,
                    "duration_ms": s.duration_ms,
                    "has_screenshot": s.screenshot_path is not None,
                }
                for s in snapshots
            ],
            indent=2,
        )
        print(output)
    else:
        # Table format
        print(f"\nVersion History: {args.test_name}")
        print(f"Storage: {args.storage_path}")
        print("-" * 80)
        print(f"{'Version ID':<20} {'Timestamp':<22} {'Status':<10} {'Duration':<10} {'Screenshot'}")
        print("-" * 80)

        for snapshot in reversed(snapshots):  # Most recent first
            version_id = snapshot.version_id[:16] + "..." if len(snapshot.version_id) > 19 else snapshot.version_id
            timestamp = snapshot.timestamp.strftime("%Y-%m-%d %H:%M:%S")
            status = snapshot.test_status or "N/A"
            duration = f"{snapshot.duration_ms}ms" if snapshot.duration_ms else "N/A"
            has_screenshot = "Yes" if snapshot.screenshot_path else "No"
            print(f"{version_id:<20} {timestamp:<22} {status:<10} {duration:<10} {has_screenshot}")

        print("-" * 80)
        print(f"Total versions: {len(snapshots)}")

    return 0


def cmd_diff(args: argparse.Namespace) -> int:
    """Compare two test versions."""
    from autoqa.versioning.diff_analyzer import VersionDiffAnalyzer
    from autoqa.versioning.history_tracker import TestRunHistory

    tracker = TestRunHistory(storage_path=args.storage_path)
    snapshots = tracker.get_snapshots(args.test_name)

    if not snapshots:
        print(f"No version history found for test: {args.test_name}", file=sys.stderr)
        return 1

    snapshot_a = None
    snapshot_b = None

    # Determine which snapshots to compare
    if args.latest > 0:
        if len(snapshots) < args.latest:
            print(f"Not enough snapshots. Found {len(snapshots)}, requested {args.latest}", file=sys.stderr)
            return 1
        # Compare the last N runs (e.g., --latest 2 compares second-to-last with last)
        snapshot_a = snapshots[-args.latest]
        snapshot_b = snapshots[-1]
    elif args.from_date and args.to_date:
        # Parse dates or version IDs
        snapshot_a = _resolve_snapshot(tracker, args.test_name, args.from_date, snapshots)
        snapshot_b = _resolve_snapshot(tracker, args.test_name, args.to_date, snapshots)
    elif args.from_date:
        # Compare from_date to latest
        snapshot_a = _resolve_snapshot(tracker, args.test_name, args.from_date, snapshots)
        snapshot_b = snapshots[-1]
    else:
        # Default: compare last 2 runs
        if len(snapshots) < 2:
            print("Need at least 2 snapshots to compare", file=sys.stderr)
            return 1
        snapshot_a = snapshots[-2]
        snapshot_b = snapshots[-1]

    if not snapshot_a or not snapshot_b:
        print("Could not resolve snapshots to compare", file=sys.stderr)
        return 1

    # Perform comparison
    analyzer = VersionDiffAnalyzer(reports_dir=f"{args.storage_path}/../reports/diffs")
    diff = analyzer.compare_versions(snapshot_a, snapshot_b)

    # Output results
    if args.output == "json":
        output = json.dumps(diff.to_dict(), indent=2, default=str)
        if args.output_file:
            Path(args.output_file).write_text(output)
            print(f"Diff report saved to {args.output_file}")
        else:
            print(output)

    elif args.output == "html":
        html = analyzer.generate_diff_report(diff, args.output_file)
        if args.output_file:
            print(f"HTML report saved to {args.output_file}")
        else:
            # Save to default location
            default_path = Path(f"{args.storage_path}/../reports/diffs") / f"diff_{args.test_name}.html"
            default_path.parent.mkdir(parents=True, exist_ok=True)
            default_path.write_text(html)
            print(f"HTML report saved to {default_path}")

    else:
        # Terminal output
        summary = analyzer.get_change_summary(diff)
        print(summary)

        if diff.has_changes():
            print("\n" + "=" * 60)
            print("CHANGES DETECTED")
            print("=" * 60)

            if diff.visual_changes:
                vc = diff.visual_changes
                print(f"\nVisual: {vc.diff_percentage:.2%} difference [{vc.severity}]")
                if vc.diff_image_path:
                    print(f"  Diff image: {vc.diff_image_path}")

            if diff.text_changes:
                print(f"\nText Changes ({len(diff.text_changes)}):")
                for tc in diff.text_changes[:10]:
                    change_indicator = {"added": "+", "removed": "-", "modified": "~"}.get(tc.change_type, "?")
                    print(f"  {change_indicator} [{tc.severity}] {tc.key or tc.selector}")

            if diff.element_changes:
                print(f"\nElement Changes ({len(diff.element_changes)}):")
                for ec in diff.element_changes[:10]:
                    change_indicator = {"added": "+", "removed": "-", "modified": "~"}.get(ec.change_type, "?")
                    print(f"  {change_indicator} [{ec.severity}] {ec.selector}")

            if diff.layout_changes:
                print(f"\nLayout Shifts ({len(diff.layout_changes)}):")
                for lc in diff.layout_changes[:10]:
                    print(f"  [{lc.severity}] {lc.selector}: {lc.shift_distance:.1f}px")

            if diff.network_changes:
                print(f"\nNetwork Changes ({len(diff.network_changes)}):")
                for nc in diff.network_changes[:10]:
                    change_indicator = {"added": "+", "removed": "-", "modified": "~"}.get(nc.change_type, "?")
                    url_short = nc.url_pattern[:50] + "..." if len(nc.url_pattern) > 50 else nc.url_pattern
                    print(f"  {change_indicator} [{nc.severity}] {url_short}")

            print("\n" + "-" * 60)
            print("Use --output html for detailed report")
        else:
            print("\nNo changes detected between versions.")

    return 0


def _resolve_snapshot(
    tracker: TestRunHistory,  # noqa: F821
    test_name: str,
    identifier: str,
    snapshots: list,
) -> TestSnapshot | None:  # noqa: F821
    """Resolve a snapshot from date string or version ID."""
    from datetime import datetime

    from autoqa.versioning.models import TestSnapshot  # noqa: F401

    # Try as version ID first
    for snapshot in snapshots:
        if snapshot.version_id == identifier or snapshot.version_id.startswith(identifier):
            return snapshot

    # Try as date
    try:
        # Try various date formats
        for fmt in ["%Y-%m-%d", "%Y-%m-%d_%H-%M-%S", "%Y%m%d"]:
            try:
                target_date = datetime.strptime(identifier, fmt).replace(tzinfo=UTC)
                return tracker.get_by_date(test_name, target_date)
            except ValueError:
                continue
    except Exception:
        pass

    return None


def cmd_server(args: argparse.Namespace) -> int:
    """Start API server."""
    from autoqa.api.main import run_server

    print(f"Starting AutoQA API server on {args.host}:{args.port}")
    run_server(host=args.host, port=args.port)
    return 0


def cmd_build(args: argparse.Namespace) -> int:
    """Auto-generate YAML test specification from a webpage."""
    return asyncio.run(_cmd_build_async(args))


async def _cmd_build_async(args: argparse.Namespace) -> int:
    """Async implementation of cmd_build."""
    from dotenv import load_dotenv
    from owl_browser import OwlBrowser, RemoteConfig

    from autoqa.builder.test_builder import AutoTestBuilder, BuilderConfig

    # Load environment variables from .env file
    load_dotenv()

    # Remote browser configuration - required
    owl_browser_url = os.getenv("OWL_BROWSER_URL")
    owl_browser_token = os.getenv("OWL_BROWSER_TOKEN")

    if not owl_browser_url:
        print("Error: OWL_BROWSER_URL environment variable is required", file=sys.stderr)
        print("Set OWL_BROWSER_URL in .env file or environment", file=sys.stderr)
        return 1

    logger.info("Connecting to remote browser", url=owl_browser_url)
    # SDK v2: api_prefix="" for direct connection without /api prefix
    remote_config = RemoteConfig(url=owl_browser_url, token=owl_browser_token, api_prefix="")
    browser = OwlBrowser(remote_config)
    await browser.connect()

    try:
        # Create builder configuration
        config = BuilderConfig(
            url=args.url,
            username=args.username,
            password=args.password,
            depth=args.depth,
            max_pages=args.max_pages,
            include_hidden=args.include_hidden,
            timeout_ms=args.timeout,
            exclude_patterns=args.exclude_patterns,
            include_patterns=args.include_patterns,
        )

        # Run the builder
        builder = AutoTestBuilder(browser=browser, config=config)
        yaml_content = await builder.build()

        # Output results
        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(yaml_content)
            print(f"Test specification written to {args.output}")
        else:
            print(yaml_content)

        return 0

    except Exception as e:
        logger.error("Build failed", error=str(e))
        print(f"Error: {e}", file=sys.stderr)
        return 1

    finally:
        await browser.close()


if __name__ == "__main__":
    sys.exit(main())
