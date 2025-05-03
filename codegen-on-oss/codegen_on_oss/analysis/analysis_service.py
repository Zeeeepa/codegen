"""
Analysis service for the codegen-on-oss system.

This module provides a service for coordinating analysis operations across components,
including code quality, dependencies, and security analyses.
"""

import logging
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Set, Union

from sqlalchemy.orm import Session

from codegen import Codebase
from codegen.sdk.core.file import SourceFile
from codegen.sdk.core.function import Function
from codegen.sdk.core.class_definition import Class

from codegen_on_oss.config import settings
from codegen_on_oss.database.models import (
    CodebaseSnapshot, CodeMetrics, FileAnalysis, FunctionAnalysis,
    ClassAnalysis, DependencyAnalysis, SecurityAnalysis, AnalysisJob,
    CodeIssue
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
        repo_path: Optional[str] = None
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
            analysis_types=analysis_types or settings.default_analysis_types,
            status="pending",
            created_at=datetime.now()
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
                repo_path=repo_path
            )
            
            # Update job with snapshot ID
            job.snapshot_id = snapshot.id
            await self.db_session.commit()
            
            # Perform requested analyses
            results = {}
            analysis_types = analysis_types or settings.default_analysis_types
            
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
                "results": results
            }
        
        except Exception as e:
            logger.exception(f"Error analyzing codebase: {str(e)}")
            
            # Update job status
            job.status = "failed"
            job.error_message = str(e)
            job.completed_at = datetime.now()
            await self.db_session.commit()
            
            return {
                "job_id": str(job_id),
                "status": "failed",
                "error": str(e)
            }
    
    async def analyze_code_quality(self, snapshot_id: uuid.UUID) -> Dict[str, Any]:
        """
        Analyze code quality for a snapshot.
        
        Args:
            snapshot_id: ID of the snapshot to analyze
            
        Returns:
            Dict[str, Any]: Code quality analysis results
        """
        logger.info(f"Analyzing code quality for snapshot: {snapshot_id}")
        
        # Get snapshot
        snapshot = await self.db_session.get(CodebaseSnapshot, snapshot_id)
        if not snapshot:
            raise ValueError(f"Snapshot not found: {snapshot_id}")
        
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
            language_breakdown=language_breakdown
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
            "language_breakdown": language_breakdown
        }
    
    async def analyze_dependencies(self, snapshot_id: uuid.UUID) -> Dict[str, Any]:
        """
        Analyze dependencies for a snapshot.
        
        Args:
            snapshot_id: ID of the snapshot to analyze
            
        Returns:
            Dict[str, Any]: Dependency analysis results
        """
        logger.info(f"Analyzing dependencies for snapshot: {snapshot_id}")
        
        # Get snapshot
        snapshot = await self.db_session.get(CodebaseSnapshot, snapshot_id)
        if not snapshot:
            raise ValueError(f"Snapshot not found: {snapshot_id}")
        
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
                        direct_dependencies.append({
                            "name": name,
                            "version": version,
                            "language": "python",
                            "source": file_path
                        })
            
            elif file_path.endswith("package.json"):
                import json
                try:
                    data = json.loads(content)
                    deps = data.get("dependencies", {})
                    dev_deps = data.get("devDependencies", {})
                    
                    for name, version in deps.items():
                        direct_dependencies.append({
                            "name": name,
                            "version": version,
                            "language": "javascript",
                            "source": file_path,
                            "dev": False
                        })
                    
                    for name, version in dev_deps.items():
                        direct_dependencies.append({
                            "name": name,
                            "version": version,
                            "language": "javascript",
                            "source": file_path,
                            "dev": True
                        })
                except json.JSONDecodeError:
                    pass
        
        # Create dependency analysis record
        analysis = DependencyAnalysis(
            snapshot_id=snapshot_id,
            dependencies_count=len(direct_dependencies),
            direct_dependencies=direct_dependencies,
            transitive_dependencies=[],
            outdated_dependencies=[],
            vulnerable_dependencies=[]
        )
        
        self.db_session.add(analysis)
        await self.db_session.commit()
        
        return {
            "dependencies_count": len(direct_dependencies),
            "direct_dependencies": direct_dependencies,
            "dependency_files": [file_path for _, file_path in found_dependency_files]
        }
    
    async def analyze_security(self, snapshot_id: uuid.UUID) -> Dict[str, Any]:
        """
        Analyze security for a snapshot.
        
        Args:
            snapshot_id: ID of the snapshot to analyze
            
        Returns:
            Dict[str, Any]: Security analysis results
        """
        logger.info(f"Analyzing security for snapshot: {snapshot_id}")
        
        # Get snapshot
        snapshot = await self.db_session.get(CodebaseSnapshot, snapshot_id)
        if not snapshot:
            raise ValueError(f"Snapshot not found: {snapshot_id}")
        
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
                if any(pattern in line.lower() for pattern in [
                    "api_key", "apikey", "api-key", "token", "password", "secret"
                ]):
                    if any(pattern in line for pattern in ["=", ":", "'"]) and not line.strip().startswith("#"):
                        security_issues.append({
                            "file": file.file_path,
                            "line": i + 1,
                            "issue": "Potential hardcoded secret",
                            "severity": "high",
                            "code": line.strip()
                        })
                
                # Check for SQL injection vulnerabilities in Python
                if file.language == "python" and "execute" in line and "%" in line:
                    security_issues.append({
                        "file": file.file_path,
                        "line": i + 1,
                        "issue": "Potential SQL injection vulnerability",
                        "severity": "high",
                        "code": line.strip()
                    })
                
                # Check for XSS vulnerabilities in JavaScript
                if file.language in ["javascript", "typescript"] and "innerHTML" in line:
                    security_issues.append({
                        "file": file.file_path,
                        "line": i + 1,
                        "issue": "Potential XSS vulnerability",
                        "severity": "medium",
                        "code": line.strip()
                    })
        
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
            analysis_data={
                "issues": security_issues
            }
        )
        
        self.db_session.add(analysis)
        await self.db_session.commit()
        
        return {
            "vulnerabilities_count": len(security_issues),
            "high_severity_count": high_severity,
            "medium_severity_count": medium_severity,
            "low_severity_count": low_severity,
            "issues": security_issues
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
                analysis_data={}
            )
            
            self.db_session.add(file_analysis)
            await self.db_session.flush()
            
            # Analyze functions and classes if using Codegen SDK
            try:
                # Use Codegen SDK to analyze the file
                codebase = Codebase(snapshot.repository)
                source_file = SourceFile(file.file_path, content)
                
                # Extract functions
                functions = source_file.functions
                for func in functions:
                    function_analysis = FunctionAnalysis(
                        file_analysis_id=file_analysis.id,
                        name=func.name,
                        start_line=func.start_line,
                        end_line=func.end_line,
                        complexity=1.0,
                        parameters=[p.name for p in func.parameters],
                        return_type=func.return_type,
                        docstring=func.docstring
                    )
                    self.db_session.add(function_analysis)
                
                # Extract classes
                classes = source_file.classes
                for cls in classes:
                    class_analysis = ClassAnalysis(
                        file_analysis_id=file_analysis.id,
                        name=cls.name,
                        start_line=cls.start_line,
                        end_line=cls.end_line,
                        methods_count=len(cls.methods),
                        attributes_count=len(cls.attributes),
                        inheritance=[base.name for base in cls.bases],
                        docstring=cls.docstring
                    )
                    self.db_session.add(class_analysis)
            
            except Exception as e:
                logger.warning(f"Error analyzing file with Codegen SDK: {file.file_path} - {str(e)}")
            
            file_analyses.append({
                "file_path": file.file_path,
                "language": file.language,
                "lines": len(lines)
            })
        
        await self.db_session.commit()
        
        return {
            "files_analyzed": len(file_analyses),
            "files": file_analyses[:10]  # Return only the first 10 for brevity
        }
    
    async def get_analysis_job(self, job_id: uuid.UUID) -> Optional[Dict[str, Any]]:
        """
        Get the status and results of an analysis job.
        
        Args:
            job_id: ID of the job to retrieve
            
        Returns:
            Optional[Dict[str, Any]]: Job status and results if found, None otherwise
        """
        job = await self.db_session.get(AnalysisJob, job_id)
        if not job:
            return None
        
        return {
            "job_id": str(job.id),
            "snapshot_id": str(job.snapshot_id) if job.snapshot_id else None,
            "repository": job.repository,
            "commit_sha": job.commit_sha,
            "branch": job.branch,
            "analysis_types": job.analysis_types,
            "status": job.status,
            "created_at": job.created_at.isoformat() if job.created_at else None,
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
            "error_message": job.error_message,
            "progress": job.progress,
            "results": job.result_data
        }

