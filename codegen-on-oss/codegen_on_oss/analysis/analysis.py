"""
Analysis module for the codegen-on-oss system.

This module provides functionality for analyzing codebases, including:
- Code quality metrics
- Dependency analysis
- Security analysis
- File and symbol analysis
"""

import json
import logging
import os
import re
import shutil
import subprocess
import tempfile
import uuid
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union

import networkx as nx
from sqlalchemy import select
from sqlalchemy.orm import Session

from codegen import Codebase
from codegen.sdk.core.file import SourceFile
from codegen_on_oss.analysis.codebase_context import CodebaseContext
from codegen_on_oss.analysis.commit_analysis import CommitAnalysisResult
from codegen_on_oss.analysis.commit_analyzer import CommitAnalyzer

# Import new analysis modules
from codegen_on_oss.database.models import (
    AnalysisJob,
    ClassAnalysis,
    CodeIssue,
    CodeMetrics,
    CodebaseSnapshot,
    DependencyAnalysis,
    FileAnalysis,
    FileManifest,
    FunctionAnalysis,
    SecurityAnalysis,
)
from codegen_on_oss.snapshot.snapshot_service import SnapshotService

logger = logging.getLogger(__name__)


class AnalysisService:
    """Coordinates analysis operations across components"""

    def __init__(self, db_session: Session, snapshot_service: SnapshotService):
        """
        Initialize the analysis service.

        Args:
            db_session: SQLAlchemy database session
            snapshot_service: Snapshot service for creating and retrieving snapshots
        """
        self.db_session = db_session
        self.snapshot_service = snapshot_service

    async def analyze_codebase(
        self,
        repo_url: str,
        commit_sha: Optional[str] = None,
        branch: Optional[str] = None,
        analysis_types: Optional[List[str]] = None,
        repo_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Perform comprehensive analysis on a codebase.

        Args:
            repo_url: URL of the repository to analyze
            commit_sha: Optional commit SHA to analyze
            branch: Optional branch name
            analysis_types: Optional list of analysis types to perform
            repo_path: Optional local path to repository (to avoid cloning)

        Returns:
            Dict[str, Any]: Analysis results
        """
        # Create a job record
        job_id = uuid.uuid4()
        job = AnalysisJob(
            id=job_id,
            repository=repo_url,
            commit_sha=commit_sha,
            branch=branch,
            analysis_types=analysis_types or ["code_quality", "dependencies", "security"],
            status="pending",
            created_at=datetime.now(),
        )
        self.db_session.add(job)
        await self.db_session.commit()

        try:
            # Update job status
            job.status = "running"
            job.started_at = datetime.now()
            await self.db_session.commit()

            # Create snapshot
            snapshot = await self.snapshot_service.create_snapshot(
                repo_url=repo_url,
                commit_sha=commit_sha,
                branch=branch,
                repo_path=repo_path,
            )

            # Update job with snapshot ID
            job.snapshot_id = snapshot.id
            await self.db_session.commit()

            # Perform requested analyses
            results = {}
            analysis_types = analysis_types or ["code_quality", "dependencies", "security"]

            if "code_quality" in analysis_types:
                job.progress = 20
                await self.db_session.commit()
                results["code_quality"] = await self.analyze_code_quality(snapshot.id)

            if "dependencies" in analysis_types:
                job.progress = 40
                await self.db_session.commit()
                results["dependencies"] = await self.analyze_dependencies(snapshot.id)

            if "security" in analysis_types:
                job.progress = 60
                await self.db_session.commit()
                results["security"] = await self.analyze_security(snapshot.id)

            if "file_analysis" in analysis_types:
                job.progress = 80
                await self.db_session.commit()
                results["file_analysis"] = await self.analyze_files(snapshot.id)

            # Store results in database
            job.status = "completed"
            job.completed_at = datetime.now()
            job.progress = 100
            job.result_data = results
            await self.db_session.commit()

            return {
                "job_id": str(job_id),
                "snapshot_id": str(snapshot.id),
                "status": "completed",
                "results": results,
            }

        except Exception as e:
            logger.exception(f"Error analyzing codebase: {e!s}")

            # Update job status
            job.status = "failed"
            job.error_message = str(e)
            job.completed_at = datetime.now()
            await self.db_session.commit()

            return {"job_id": str(job_id), "status": "failed", "error": str(e)}

    async def analyze_code_quality(self, snapshot_id: uuid.UUID) -> dict[str, Any]:
        """Analyze code quality for a snapshot.

        Args:
            snapshot_id: ID of the snapshot to analyze

        Returns:
            Dict[str, Any]: Code quality analysis results
        """
        logger.info(f"Analyzing code quality for snapshot: {snapshot_id}")

        # Get snapshot
        snapshot = await self.db_session.get(CodebaseSnapshot, snapshot_id)
        if not snapshot:
            msg = f"Snapshot not found: {snapshot_id}"
            raise ValueError(msg)

        # Get file manifests
        files = await self.snapshot_service.get_snapshot_files(snapshot_id, limit=100000)

        # Compute metrics
        total_lines = 0
        code_lines = 0
        comment_lines = 0
        blank_lines = 0
        complexity = 0.0
        language_breakdown = {}

        for file in files:
            if not file.language:
                continue

            # Update language breakdown
            language_breakdown[file.language] = language_breakdown.get(file.language, 0) + 1

            # Get file content
            content = await self.snapshot_service.get_file_content(snapshot_id, file.file_path)
            if not content:
                continue

            # Convert bytes to string if needed
            if isinstance(content, bytes):
                try:
                    content = content.decode("utf-8")
                except UnicodeDecodeError:
                    # Skip binary files
                    continue

            # Count lines
            lines = content.splitlines()
            total_lines += len(lines)

            # Count code, comment, and blank lines
            for line in lines:
                line = line.strip()
                if not line:
                    blank_lines += 1
                elif line.startswith(("#", "//", "/*", "*", "'")):
                    comment_lines += 1
                else:
                    code_lines += 1

        # Compute maintainability index (simplified version)
        maintainability_index = 100.0
        if total_lines > 0:
            # Lower is worse
            maintainability_index = max(0, 100 - (total_lines / 1000) * 10)

        # Create code metrics record
        metrics = CodeMetrics(
            snapshot_id=snapshot_id,
            total_lines=total_lines,
            code_lines=code_lines,
            comment_lines=comment_lines,
            blank_lines=blank_lines,
            complexity=complexity,
            maintainability_index=maintainability_index,
            language_breakdown=language_breakdown,
        )

        self.db_session.add(metrics)
        await self.db_session.commit()

        return {
            "total_lines": total_lines,
            "code_lines": code_lines,
            "comment_lines": comment_lines,
            "blank_lines": blank_lines,
            "complexity": complexity,
            "maintainability_index": maintainability_index,
            "language_breakdown": language_breakdown,
        }

    async def analyze_dependencies(self, snapshot_id: uuid.UUID) -> dict[str, Any]:
        """Analyze dependencies for a snapshot.

        Args:
            snapshot_id: ID of the snapshot to analyze

        Returns:
            Dict[str, Any]: Dependency analysis results
        """
        logger.info(f"Analyzing dependencies for snapshot: {snapshot_id}")

        # Get snapshot
        snapshot = await self.db_session.get(CodebaseSnapshot, snapshot_id)
        if not snapshot:
            msg = f"Snapshot not found: {snapshot_id}"
            raise ValueError(msg)

        # Look for dependency files
        dependency_files = {
            "python": ["requirements.txt", "setup.py", "pyproject.toml"],
            "javascript": ["package.json", "yarn.lock", "package-lock.json"],
            "java": ["pom.xml", "build.gradle"],
            "ruby": ["Gemfile", "Gemfile.lock"],
            "php": ["composer.json", "composer.lock"],
            "go": ["go.mod", "go.sum"],
            "rust": ["Cargo.toml", "Cargo.lock"],
            "dotnet": ["*.csproj", "*.fsproj", "packages.config"],
        }

        # Get file manifests
        files = await self.snapshot_service.get_snapshot_files(snapshot_id, limit=100000)

        # Find dependency files
        found_dependency_files = []
        for file in files:
            for language, patterns in dependency_files.items():
                for pattern in patterns:
                    if pattern.startswith("*"):
                        if file.file_path.endswith(pattern[1:]):
                            found_dependency_files.append((language, file.file_path))
                    elif file.file_path.endswith(pattern):
                        found_dependency_files.append((language, file.file_path))

        # Extract dependencies
        direct_dependencies = []
        for language, file_path in found_dependency_files:
            content = await self.snapshot_service.get_file_content(snapshot_id, file_path)
            if not content:
                continue

            # Convert bytes to string if needed
            if isinstance(content, bytes):
                try:
                    content = content.decode("utf-8")
                except UnicodeDecodeError:
                    continue

            # Extract dependencies based on file type
            if file_path.endswith("requirements.txt"):
                for line in content.splitlines():
                    line = line.strip()
                    if line and not line.startswith("#"):
                        parts = line.split("==")
                        name = parts[0].strip()
                        version = parts[1].strip() if len(parts) > 1 else None
                        direct_dependencies.append({"name": name, "version": version, "language": "python", "source": file_path})

            elif file_path.endswith("package.json"):
                import json

                try:
                    data = json.loads(content)
                    deps = data.get("dependencies", {})
                    dev_deps = data.get("devDependencies", {})

                    for name, version in deps.items():
                        direct_dependencies.append({"name": name, "version": version, "language": "javascript", "source": file_path, "dev": False})

                    for name, version in dev_deps.items():
                        direct_dependencies.append({"name": name, "version": version, "language": "javascript", "source": file_path, "dev": True})
                except json.JSONDecodeError:
                    pass

        # Create dependency analysis record
        analysis = DependencyAnalysis(
            snapshot_id=snapshot_id,
            dependencies_count=len(direct_dependencies),
            direct_dependencies=direct_dependencies,
            transitive_dependencies=[],
            outdated_dependencies=[],
            vulnerable_dependencies=[],
        )

        self.db_session.add(analysis)
        await self.db_session.commit()

        return {"dependencies_count": len(direct_dependencies), "direct_dependencies": direct_dependencies, "dependency_files": [file_path for _, file_path in found_dependency_files]}

    async def analyze_security(self, snapshot_id: uuid.UUID) -> dict[str, Any]:
        """Analyze security for a snapshot.

        Args:
            snapshot_id: ID of the snapshot to analyze

        Returns:
            Dict[str, Any]: Security analysis results
        """
        logger.info(f"Analyzing security for snapshot: {snapshot_id}")

        # Get snapshot
        snapshot = await self.db_session.get(CodebaseSnapshot, snapshot_id)
        if not snapshot:
            msg = f"Snapshot not found: {snapshot_id}"
            raise ValueError(msg)

        # Simple security checks
        security_issues = []

        # Get file manifests
        files = await self.snapshot_service.get_snapshot_files(snapshot_id, limit=100000)

        # Check for potential security issues
        for file in files:
            # Skip non-code files
            if not file.language:
                continue

            # Get file content
            content = await self.snapshot_service.get_file_content(snapshot_id, file.file_path)
            if not content:
                continue

            # Convert bytes to string if needed
            if isinstance(content, bytes):
                try:
                    content = content.decode("utf-8")
                except UnicodeDecodeError:
                    continue

            # Check for hardcoded secrets
            lines = content.splitlines()
            for i, line in enumerate(lines):
                # Check for API keys, tokens, passwords
                if any(pattern in line.lower() for pattern in ["api_key", "apikey", "api-key", "token", "password", "secret"]):
                    if any(pattern in line for pattern in ["=", ":", "'"]) and not line.strip().startswith("#"):
                        security_issues.append({"file": file.file_path, "line": i + 1, "issue": "Potential hardcoded secret", "severity": "high", "code": line.strip()})

                # Check for SQL injection vulnerabilities in Python
                if file.language == "python" and "execute" in line and "%" in line:
                    security_issues.append({"file": file.file_path, "line": i + 1, "issue": "Potential SQL injection vulnerability", "severity": "high", "code": line.strip()})

                # Check for XSS vulnerabilities in JavaScript
                if file.language in ["javascript", "typescript"] and "innerHTML" in line:
                    security_issues.append({"file": file.file_path, "line": i + 1, "issue": "Potential XSS vulnerability", "severity": "medium", "code": line.strip()})

        # Count issues by severity
        high_severity = sum(1 for issue in security_issues if issue["severity"] == "high")
        medium_severity = sum(1 for issue in security_issues if issue["severity"] == "medium")
        low_severity = sum(1 for issue in security_issues if issue["severity"] == "low")

        # Create security analysis record
        analysis = SecurityAnalysis(
            snapshot_id=snapshot_id,
            vulnerabilities_count=len(security_issues),
            high_severity_count=high_severity,
            medium_severity_count=medium_severity,
            low_severity_count=low_severity,
            analysis_data={"issues": security_issues},
        )

        self.db_session.add(analysis)
        await self.db_session.commit()

        return {
            "vulnerabilities_count": len(security_issues),
            "high_severity_count": high_severity,
            "medium_severity_count": medium_severity,
            "low_severity_count": low_severity,
            "issues": security_issues,
        }

    async def analyze_files(self, snapshot_id: uuid.UUID) -> Dict[str, Any]:
        """
        Analyze individual files for a snapshot.

        Args:
            snapshot_id: ID of the snapshot to analyze

        Returns:
            Dict[str, Any]: File analysis results
        """
        logger.info(f"Analyzing files for snapshot: {snapshot_id}")

        # Get snapshot
        snapshot = await self.db_session.get(CodebaseSnapshot, snapshot_id)
        if not snapshot:
            raise ValueError(f"Snapshot not found: {snapshot_id}")

        # Get file manifests
        files = await self.snapshot_service.get_snapshot_files(snapshot_id, limit=100000)

        # Analyze each file
        file_analyses = []
        for file in files:
            # Skip non-code files
            if not file.language:
                continue

            # Get file content
            content = await self.snapshot_service.get_file_content(snapshot_id, file.file_path)
            if not content:
                continue

            # Convert bytes to string if needed
            if isinstance(content, bytes):
                try:
                    content = content.decode("utf-8")
                except UnicodeDecodeError:
                    continue

            # Count lines
            lines = content.splitlines()

            # Compute complexity (simplified)
            complexity = 1.0

            # Create file analysis record
            file_analysis = FileAnalysis(
                snapshot_id=snapshot_id,
                file_path=file.file_path,
                language=file.language,
                lines=len(lines),
                complexity=complexity,
                analysis_data={},
            )

            self.db_session.add(file_analysis)
            file_analyses.append(file_analysis)

        await self.db_session.commit()

        return {
            "file_count": len(file_analyses),
            "analyzed_files": [f.file_path for f in file_analyses],
        }

    def analyze_import_structure(self, codebase: Codebase) -> Dict[str, Any]:
        """
        Analyze the import structure of a codebase.

        Args:
            codebase: The codebase to analyze

        Returns:
            A dictionary containing import analysis results
        """
        # This is a placeholder for the actual implementation
        # In a real implementation, we would:
        # 1. Extract all imports from Python files
        # 2. Build a dependency graph
        # 3. Analyze for cycles and other issues
        return {
            "import_count": 0,
            "cycles": [],
            "problematic_imports": [],
        }

    def analyze_code_complexity(self, codebase: Codebase) -> Dict[str, Any]:
        """
        Analyze the complexity of code in a codebase.

        Args:
            codebase: The codebase to analyze

        Returns:
            A dictionary containing complexity metrics
        """
        # This is a placeholder for the actual implementation
        # In a real implementation, we would:
        # 1. Calculate cyclomatic complexity for functions
        # 2. Identify overly complex functions
        # 3. Calculate maintainability index
        return {
            "average_complexity": 0.0,
            "complex_functions": [],
            "maintainability_index": 0.0,
        }

    def analyze_code_duplication(self, codebase: Codebase) -> Dict[str, Any]:
        """
        Analyze code duplication in a codebase.

        Args:
            codebase: The codebase to analyze

        Returns:
            A dictionary containing duplication metrics
        """
        # This is a placeholder for the actual implementation
        # In a real implementation, we would:
        # 1. Identify duplicate code blocks
        # 2. Calculate duplication percentage
        # 3. Suggest refactoring opportunities
        return {
            "duplication_percentage": 0.0,
            "duplicate_blocks": [],
            "refactoring_suggestions": [],
        }

    def get_file_changes(self, commits, limit=10) -> Dict[str, int]:
        """
        Get the most frequently changed files across a set of commits.

        Args:
            commits: List of commits to analyze
            limit: Maximum number of files to return

        Returns:
            Dict[str, int]: Dictionary mapping file paths to change counts
        """
        try:
            # Count changes per file
            file_changes = {}
            for commit in commits:
                for file in commit.files:
                    if file.filename in file_changes:
                        file_changes[file.filename] += 1
                    else:
                        file_changes[file.filename] = 1

            # Sort by change count and limit results
            sorted_files = sorted(file_changes.items(), key=lambda x: x[1], reverse=True)[:limit]
            return dict(sorted_files)
        except Exception as e:
            return {"error": str(e)}

    def create_snapshot(self, commit_sha: Optional[str] = None) -> CodebaseSnapshot:
        """
        Create a snapshot of the codebase at a specific commit.

        Args:
            commit_sha: Optional commit SHA to snapshot

        Returns:
            CodebaseSnapshot: A snapshot of the codebase
        """
        # This is a placeholder for the actual implementation
        # In a real implementation, we would:
        # 1. Clone the repository at the specified commit
        # 2. Create a snapshot of the files
        # 3. Store metadata about the snapshot
        return CodebaseSnapshot(self.codebase, commit_sha)

    def get_monthly_commits(repo_path: str) -> Dict[str, int]:
        """
        Get the number of commits per month for a repository.

        Args:
            repo_path: Path to the repository

        Returns:
            Dict[str, int]: Dictionary mapping month strings to commit counts
        """
        try:
            # Run git log to get commit dates
            result = subprocess.run(
                ["git", "log", "--format=%ai"],
                cwd=repo_path,
                capture_output=True,
                text=True,
                check=True,
            )

            # Parse dates and count by month
            monthly_counts = defaultdict(int)
            for line in result.stdout.splitlines():
                if line.strip():
                    date_str = line.split()[0]  # Format: YYYY-MM-DD
                    year_month = date_str[:7]  # Extract YYYY-MM
                    monthly_counts[year_month] += 1

            return dict(sorted(monthly_counts.items()))
        except Exception as e:
            print(f"Error analyzing commit history: {str(e)}")
            return {}


# Helper functions for complexity analysis
def calculate_cyclomatic_complexity(source_code: str) -> int:
    """
    Calculate cyclomatic complexity of a Python function.

    Args:
        source_code: Source code of the function

    Returns:
        int: Cyclomatic complexity score
    """
    # This is a simplified implementation
    # In a real implementation, we would use a proper parser
    complexity = 1  # Base complexity

    # Count decision points
    keywords = ["if", "elif", "for", "while", "and", "or", "except", "with", "assert"]
    for keyword in keywords:
        complexity += source_code.count(f" {keyword} ")

    return complexity


def calculate_maintainability_index(
    cyclomatic_complexity: int, lines_of_code: int, comment_percentage: float
) -> float:
    """
    Calculate maintainability index for a code unit.

    Args:
        cyclomatic_complexity: Cyclomatic complexity score
        lines_of_code: Number of lines of code
        comment_percentage: Percentage of comments in the code

    Returns:
        float: Maintainability index score
    """
    # This is a simplified implementation of the maintainability index formula
    # MI = 171 - 5.2 * ln(V) - 0.23 * G - 16.2 * ln(L) + 50 * sin(sqrt(2.4 * C))
    # Where:
    # V = Halstead Volume (simplified here)
    # G = Cyclomatic Complexity
    # L = Lines of Code
    # C = Comment Percentage (0-1)

    import math

    halstead_volume = lines_of_code * 3  # Simplified approximation
    mi = (
        171
        - 5.2 * math.log(halstead_volume + 1)
        - 0.23 * cyclomatic_complexity
        - 16.2 * math.log(lines_of_code + 1)
        + 50 * math.sin(math.sqrt(2.4 * comment_percentage))
    )

    # Normalize to 0-100 scale
    return max(0, min(100, mi))


def clone_repository(repo_url: str, target_dir: str, commit_sha: Optional[str] = None) -> str:
    """
    Clone a repository to a local directory.

    Args:
        repo_url: URL of the repository to clone
        target_dir: Directory to clone into
        commit_sha: Optional commit SHA to checkout

    Returns:
        str: Path to the cloned repository
    """
    # Clone the repository
    subprocess.run(
        ["git", "clone", "--depth=1", repo_url, target_dir],
        capture_output=True,
        text=True,
    )

    # Checkout specific commit if provided
    if commit_sha:
        subprocess.run(
            ["git", "fetch", "--depth=1", "origin", commit_sha],
            cwd=target_dir,
            capture_output=True,
            text=True,
        )
        subprocess.run(
            ["git", "checkout", commit_sha],
            cwd=target_dir,
            capture_output=True,
            text=True,
        )

    return target_dir

