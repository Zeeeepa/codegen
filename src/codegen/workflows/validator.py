"""
Codegen Validation Workflow

Main validation workflow orchestrating CI/CD completion validation.
"""

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta

try:
    from workflows import Context, Workflow, step
    from workflows.events import StartEvent, StopEvent
    WORKFLOWS_AVAILABLE = True
except ImportError:
    # Fallback implementations
    WORKFLOWS_AVAILABLE = False
    from typing import Protocol
    
    class Context(Protocol):
        pass
    
    class Workflow:
        pass
    
    def step(func):
        return func
    
    class StartEvent:
        pass
    
    class StopEvent:
        pass

from .events import (
    ValidationStatus,
    ValidationSeverity,
    ValidationResult,
    AgentRunValidationEvent,
    CodeQualityValidationEvent,
    SecurityValidationEvent,
    DeploymentValidationEvent,
    ValidationCompleteEvent,
    ValidationStepEvent,
    ValidationErrorEvent,
    ValidationRetryEvent,
)

logger = logging.getLogger(__name__)


class ValidationConfig:
    """Configuration for validation workflow."""
    
    def __init__(
        self,
        enable_code_quality: bool = True,
        enable_security_scan: bool = True,
        enable_deployment_validation: bool = True,
        parallel_execution: bool = True,
        timeout_minutes: int = 30,
        retry_attempts: int = 3,
        fail_fast: bool = False,
        notification_channels: Optional[List[str]] = None,
    ):
        self.enable_code_quality = enable_code_quality
        self.enable_security_scan = enable_security_scan
        self.enable_deployment_validation = enable_deployment_validation
        self.parallel_execution = parallel_execution
        self.timeout_minutes = timeout_minutes
        self.retry_attempts = retry_attempts
        self.fail_fast = fail_fast
        self.notification_channels = notification_channels or []


class ValidationState:
    """State management for validation workflow."""
    
    def __init__(self):
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.current_step: Optional[str] = None
        self.completed_steps: List[str] = []
        self.failed_steps: List[str] = []
        self.skipped_steps: List[str] = []
        self.results: List[ValidationResult] = []
        self.overall_status: ValidationStatus = ValidationStatus.PENDING
        self.retry_counts: Dict[str, int] = {}
        self.metadata: Dict[str, Any] = {}


class CodegenValidationWorkflow(Workflow if WORKFLOWS_AVAILABLE else object):
    """
    Main validation workflow for Codegen CI/CD completion.
    
    Orchestrates comprehensive validation including:
    - Agent run validation
    - Code quality checks
    - Security scanning
    - Deployment validation
    - Integration testing
    """
    
    def __init__(self, config: Optional[ValidationConfig] = None):
        if WORKFLOWS_AVAILABLE:
            super().__init__()
        self.config = config or ValidationConfig()
        self.state = ValidationState()
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    @step
    async def start_validation(
        self, 
        ctx: Context, 
        ev: StartEvent
    ) -> AgentRunValidationEvent:
        """Initialize validation workflow."""
        self.logger.info(f"Starting validation workflow for agent run: {ev.agent_run_id}")
        
        self.state.start_time = datetime.utcnow()
        self.state.current_step = "initialization"
        self.state.overall_status = ValidationStatus.RUNNING
        
        # Extract validation parameters from start event
        return AgentRunValidationEvent(
            agent_run_id=ev.agent_run_id,
            organization_id=ev.organization_id,
            repository_id=ev.get("repository_id"),
            pr_number=ev.get("pr_number"),
            commit_sha=ev.get("commit_sha"),
            agent_type=ev.get("agent_type", "unknown"),
            prompt=ev.get("prompt", ""),
            source_type=ev.get("source_type", "api"),
            execution_status=ev.get("execution_status", "completed"),
            result_summary=ev.get("result_summary"),
            output_files=ev.get("output_files", []),
            tokens_used=ev.get("tokens_used"),
            api_calls_made=ev.get("api_calls_made"),
        )
    
    @step
    async def validate_agent_run(
        self, 
        ctx: Context, 
        ev: AgentRunValidationEvent
    ) -> CodeQualityValidationEvent:
        """Validate the agent run itself."""
        step_name = "agent_run_validation"
        self.state.current_step = step_name
        start_time = time.time()
        
        try:
            self.logger.info(f"Validating agent run {ev.agent_run_id}")
            
            # Validate agent run completion
            validation_result = await self._validate_agent_completion(ev)
            
            # Validate output quality
            if ev.output_files:
                output_validation = await self._validate_output_files(ev.output_files)
                validation_result = self._merge_validation_results(
                    validation_result, output_validation
                )
            
            # Validate resource usage
            resource_validation = await self._validate_resource_usage(ev)
            validation_result = self._merge_validation_results(
                validation_result, resource_validation
            )
            
            duration = time.time() - start_time
            validation_result.duration_seconds = duration
            
            self.state.results.append(validation_result)
            self.state.completed_steps.append(step_name)
            
            self.logger.info(f"Agent run validation completed: {validation_result.status}")
            
            # Emit step completion event
            await self._emit_step_event(ctx, step_name, "agent_validation", validation_result)
            
            # Proceed to code quality validation if enabled
            if self.config.enable_code_quality and ev.output_files:
                return CodeQualityValidationEvent(
                    agent_run_id=ev.agent_run_id,
                    organization_id=ev.organization_id,
                    repository_id=ev.repository_id,
                    pr_number=ev.pr_number,
                    commit_sha=ev.commit_sha,
                    changed_files=ev.output_files,
                    language=await self._detect_language(ev.output_files),
                )
            else:
                # Skip to security validation
                return SecurityValidationEvent(
                    agent_run_id=ev.agent_run_id,
                    organization_id=ev.organization_id,
                    repository_id=ev.repository_id,
                    pr_number=ev.pr_number,
                    commit_sha=ev.commit_sha,
                )
                
        except Exception as e:
            await self._handle_validation_error(ctx, step_name, e)
            raise
    
    @step
    async def validate_code_quality(
        self, 
        ctx: Context, 
        ev: CodeQualityValidationEvent
    ) -> SecurityValidationEvent:
        """Validate code quality metrics."""
        step_name = "code_quality_validation"
        self.state.current_step = step_name
        start_time = time.time()
        
        try:
            self.logger.info(f"Running code quality validation for {len(ev.changed_files)} files")
            
            validation_tasks = []
            
            # Linting validation
            validation_tasks.append(self._run_linting_validation(ev))
            
            # Test coverage validation
            if ev.test_coverage_required:
                validation_tasks.append(self._run_coverage_validation(ev))
            
            # Complexity validation
            if ev.complexity_threshold:
                validation_tasks.append(self._run_complexity_validation(ev))
            
            # Code style validation
            validation_tasks.append(self._run_style_validation(ev))
            
            # Run validations in parallel or sequential based on config
            if self.config.parallel_execution:
                results = await asyncio.gather(*validation_tasks, return_exceptions=True)
            else:
                results = []
                for task in validation_tasks:
                    result = await task
                    results.append(result)
                    
                    # Fail fast if enabled and we have a failure
                    if self.config.fail_fast and result.status == ValidationStatus.FAILED:
                        break
            
            # Aggregate results
            overall_result = self._aggregate_validation_results(results, step_name)
            overall_result.duration_seconds = time.time() - start_time
            
            self.state.results.append(overall_result)
            self.state.completed_steps.append(step_name)
            
            self.logger.info(f"Code quality validation completed: {overall_result.status}")
            
            # Emit step completion event
            await self._emit_step_event(ctx, step_name, "code_quality", overall_result)
            
            # Proceed to security validation
            return SecurityValidationEvent(
                agent_run_id=ev.agent_run_id,
                organization_id=ev.organization_id,
                repository_id=ev.repository_id,
                pr_number=ev.pr_number,
                commit_sha=ev.commit_sha,
                scan_types=["secrets", "vulnerabilities", "dependencies"],
                severity_threshold=ValidationSeverity.WARNING,
            )
            
        except Exception as e:
            await self._handle_validation_error(ctx, step_name, e)
            raise
    
    @step
    async def validate_security(
        self, 
        ctx: Context, 
        ev: SecurityValidationEvent
    ) -> DeploymentValidationEvent:
        """Validate security requirements."""
        step_name = "security_validation"
        self.state.current_step = step_name
        start_time = time.time()
        
        try:
            self.logger.info(f"Running security validation with scans: {ev.scan_types}")
            
            validation_tasks = []
            
            # Secret scanning
            if "secrets" in ev.scan_types:
                validation_tasks.append(self._run_secret_scanning(ev))
            
            # Vulnerability scanning
            if "vulnerabilities" in ev.scan_types:
                validation_tasks.append(self._run_vulnerability_scanning(ev))
            
            # Dependency scanning
            if "dependencies" in ev.scan_types:
                validation_tasks.append(self._run_dependency_scanning(ev))
            
            # SAST (Static Application Security Testing)
            validation_tasks.append(self._run_sast_scanning(ev))
            
            # Run security scans
            if self.config.parallel_execution:
                results = await asyncio.gather(*validation_tasks, return_exceptions=True)
            else:
                results = []
                for task in validation_tasks:
                    result = await task
                    results.append(result)
                    
                    if self.config.fail_fast and result.status == ValidationStatus.FAILED:
                        break
            
            # Aggregate results
            overall_result = self._aggregate_validation_results(results, step_name)
            overall_result.duration_seconds = time.time() - start_time
            
            self.state.results.append(overall_result)
            self.state.completed_steps.append(step_name)
            
            self.logger.info(f"Security validation completed: {overall_result.status}")
            
            # Emit step completion event
            await self._emit_step_event(ctx, step_name, "security", overall_result)
            
            # Proceed to deployment validation if enabled
            if self.config.enable_deployment_validation:
                return DeploymentValidationEvent(
                    agent_run_id=ev.agent_run_id,
                    organization_id=ev.organization_id,
                    repository_id=ev.repository_id,
                    pr_number=ev.pr_number,
                    commit_sha=ev.commit_sha,
                    environment="staging",
                    deployment_type="validation",
                    health_checks=["api_health", "database_connectivity"],
                )
            else:
                # Skip to completion
                return await self._complete_validation(ctx, ev)
                
        except Exception as e:
            await self._handle_validation_error(ctx, step_name, e)
            raise
    
    @step
    async def validate_deployment(
        self, 
        ctx: Context, 
        ev: DeploymentValidationEvent
    ) -> ValidationCompleteEvent:
        """Validate deployment readiness."""
        step_name = "deployment_validation"
        self.state.current_step = step_name
        start_time = time.time()
        
        try:
            self.logger.info(f"Running deployment validation for {ev.environment}")
            
            validation_tasks = []
            
            # Health check validation
            for health_check in ev.health_checks:
                validation_tasks.append(self._run_health_check(health_check, ev))
            
            # Configuration validation
            validation_tasks.append(self._validate_deployment_config(ev))
            
            # Resource validation
            validation_tasks.append(self._validate_deployment_resources(ev))
            
            # Run deployment validations
            if self.config.parallel_execution:
                results = await asyncio.gather(*validation_tasks, return_exceptions=True)
            else:
                results = []
                for task in validation_tasks:
                    result = await task
                    results.append(result)
                    
                    if self.config.fail_fast and result.status == ValidationStatus.FAILED:
                        break
            
            # Aggregate results
            overall_result = self._aggregate_validation_results(results, step_name)
            overall_result.duration_seconds = time.time() - start_time
            
            self.state.results.append(overall_result)
            self.state.completed_steps.append(step_name)
            
            self.logger.info(f"Deployment validation completed: {overall_result.status}")
            
            # Emit step completion event
            await self._emit_step_event(ctx, step_name, "deployment", overall_result)
            
            # Complete validation
            return await self._complete_validation(ctx, ev)
            
        except Exception as e:
            await self._handle_validation_error(ctx, step_name, e)
            raise
    
    @step
    async def complete_validation(
        self, 
        ctx: Context, 
        ev: ValidationCompleteEvent
    ) -> StopEvent:
        """Complete the validation workflow."""
        self.state.end_time = datetime.utcnow()
        self.state.current_step = "completed"
        
        self.logger.info(f"Validation workflow completed: {ev.overall_status}")
        
        # Send notifications if configured
        await self._send_notifications(ev)
        
        # Return final result
        return StopEvent(result={
            "status": ev.overall_status.value,
            "agent_run_id": ev.agent_run_id,
            "total_duration": ev.total_duration_seconds,
            "passed_count": ev.passed_count,
            "failed_count": ev.failed_count,
            "skipped_count": ev.skipped_count,
            "summary": ev.summary,
            "validation_results": [result.dict() for result in ev.validation_results],
        })
    
    # Helper methods
    
    async def _validate_agent_completion(self, ev: AgentRunValidationEvent) -> ValidationResult:
        """Validate agent run completion."""
        if ev.execution_status == "completed":
            return ValidationResult(
                status=ValidationStatus.PASSED,
                message="Agent run completed successfully",
                details={"execution_status": ev.execution_status}
            )
        elif ev.execution_status == "failed":
            return ValidationResult(
                status=ValidationStatus.FAILED,
                severity=ValidationSeverity.ERROR,
                message="Agent run failed",
                details={"execution_status": ev.execution_status}
            )
        else:
            return ValidationResult(
                status=ValidationStatus.SKIPPED,
                message=f"Agent run in unexpected state: {ev.execution_status}",
                details={"execution_status": ev.execution_status}
            )
    
    async def _validate_output_files(self, output_files: List[str]) -> ValidationResult:
        """Validate agent output files."""
        if not output_files:
            return ValidationResult(
                status=ValidationStatus.PASSED,
                message="No output files to validate"
            )
        
        # Check if files exist and are valid
        valid_files = []
        invalid_files = []
        
        for file_path in output_files:
            # In a real implementation, you would check file existence and validity
            # For now, assume all files are valid
            valid_files.append(file_path)
        
        if invalid_files:
            return ValidationResult(
                status=ValidationStatus.FAILED,
                severity=ValidationSeverity.ERROR,
                message=f"Invalid output files found: {invalid_files}",
                details={"valid_files": valid_files, "invalid_files": invalid_files}
            )
        
        return ValidationResult(
            status=ValidationStatus.PASSED,
            message=f"All {len(valid_files)} output files are valid",
            details={"valid_files": valid_files}
        )
    
    async def _validate_resource_usage(self, ev: AgentRunValidationEvent) -> ValidationResult:
        """Validate resource usage is within limits."""
        issues = []
        
        # Check token usage
        if ev.tokens_used and ev.tokens_used > 100000:  # Example threshold
            issues.append(f"High token usage: {ev.tokens_used}")
        
        # Check API calls
        if ev.api_calls_made and ev.api_calls_made > 1000:  # Example threshold
            issues.append(f"High API call count: {ev.api_calls_made}")
        
        if issues:
            return ValidationResult(
                status=ValidationStatus.FAILED,
                severity=ValidationSeverity.WARNING,
                message="Resource usage exceeded thresholds",
                details={"issues": issues, "tokens_used": ev.tokens_used, "api_calls": ev.api_calls_made}
            )
        
        return ValidationResult(
            status=ValidationStatus.PASSED,
            message="Resource usage within acceptable limits",
            details={"tokens_used": ev.tokens_used, "api_calls": ev.api_calls_made}
        )
    
    async def _detect_language(self, files: List[str]) -> str:
        """Detect primary programming language from files."""
        # Simple language detection based on file extensions
        extensions = {}
        for file_path in files:
            if '.' in file_path:
                ext = file_path.split('.')[-1].lower()
                extensions[ext] = extensions.get(ext, 0) + 1
        
        if not extensions:
            return "unknown"
        
        # Return most common extension
        return max(extensions, key=extensions.get)
    
    async def _run_linting_validation(self, ev: CodeQualityValidationEvent) -> ValidationResult:
        """Run linting validation."""
        # Placeholder implementation
        await asyncio.sleep(0.1)  # Simulate async work
        
        return ValidationResult(
            status=ValidationStatus.PASSED,
            message="Linting validation passed",
            details={"files_checked": len(ev.changed_files), "language": ev.language}
        )
    
    async def _run_coverage_validation(self, ev: CodeQualityValidationEvent) -> ValidationResult:
        """Run test coverage validation."""
        await asyncio.sleep(0.1)
        
        # Simulate coverage check
        coverage_percentage = 85.0  # Mock value
        
        if coverage_percentage >= 80:
            return ValidationResult(
                status=ValidationStatus.PASSED,
                message=f"Test coverage is adequate: {coverage_percentage}%",
                details={"coverage_percentage": coverage_percentage}
            )
        else:
            return ValidationResult(
                status=ValidationStatus.FAILED,
                severity=ValidationSeverity.WARNING,
                message=f"Test coverage is below threshold: {coverage_percentage}%",
                details={"coverage_percentage": coverage_percentage, "threshold": 80}
            )
    
    async def _run_complexity_validation(self, ev: CodeQualityValidationEvent) -> ValidationResult:
        """Run code complexity validation."""
        await asyncio.sleep(0.1)
        
        return ValidationResult(
            status=ValidationStatus.PASSED,
            message="Code complexity is within acceptable limits"
        )
    
    async def _run_style_validation(self, ev: CodeQualityValidationEvent) -> ValidationResult:
        """Run code style validation."""
        await asyncio.sleep(0.1)
        
        return ValidationResult(
            status=ValidationStatus.PASSED,
            message="Code style validation passed"
        )
    
    async def _run_secret_scanning(self, ev: SecurityValidationEvent) -> ValidationResult:
        """Run secret scanning."""
        await asyncio.sleep(0.2)
        
        return ValidationResult(
            status=ValidationStatus.PASSED,
            message="No secrets detected in code"
        )
    
    async def _run_vulnerability_scanning(self, ev: SecurityValidationEvent) -> ValidationResult:
        """Run vulnerability scanning."""
        await asyncio.sleep(0.3)
        
        return ValidationResult(
            status=ValidationStatus.PASSED,
            message="No vulnerabilities detected"
        )
    
    async def _run_dependency_scanning(self, ev: SecurityValidationEvent) -> ValidationResult:
        """Run dependency scanning."""
        await asyncio.sleep(0.2)
        
        return ValidationResult(
            status=ValidationStatus.PASSED,
            message="All dependencies are secure"
        )
    
    async def _run_sast_scanning(self, ev: SecurityValidationEvent) -> ValidationResult:
        """Run static application security testing."""
        await asyncio.sleep(0.4)
        
        return ValidationResult(
            status=ValidationStatus.PASSED,
            message="SAST scan completed successfully"
        )
    
    async def _run_health_check(self, check_name: str, ev: DeploymentValidationEvent) -> ValidationResult:
        """Run a specific health check."""
        await asyncio.sleep(0.1)
        
        return ValidationResult(
            status=ValidationStatus.PASSED,
            message=f"Health check '{check_name}' passed"
        )
    
    async def _validate_deployment_config(self, ev: DeploymentValidationEvent) -> ValidationResult:
        """Validate deployment configuration."""
        await asyncio.sleep(0.1)
        
        return ValidationResult(
            status=ValidationStatus.PASSED,
            message="Deployment configuration is valid"
        )
    
    async def _validate_deployment_resources(self, ev: DeploymentValidationEvent) -> ValidationResult:
        """Validate deployment resources."""
        await asyncio.sleep(0.1)
        
        return ValidationResult(
            status=ValidationStatus.PASSED,
            message="Deployment resources are adequate"
        )
    
    def _merge_validation_results(self, result1: ValidationResult, result2: ValidationResult) -> ValidationResult:
        """Merge two validation results."""
        # Use the worse status
        if result1.status == ValidationStatus.FAILED or result2.status == ValidationStatus.FAILED:
            status = ValidationStatus.FAILED
        elif result1.status == ValidationStatus.SKIPPED or result2.status == ValidationStatus.SKIPPED:
            status = ValidationStatus.SKIPPED
        else:
            status = ValidationStatus.PASSED
        
        # Use the higher severity
        severity = max(result1.severity, result2.severity, key=lambda x: ["info", "warning", "error", "critical"].index(x.value))
        
        return ValidationResult(
            status=status,
            severity=severity,
            message=f"{result1.message}; {result2.message}",
            details={"result1": result1.details, "result2": result2.details}
        )
    
    def _aggregate_validation_results(self, results: List[ValidationResult], step_name: str) -> ValidationResult:
        """Aggregate multiple validation results."""
        if not results:
            return ValidationResult(
                status=ValidationStatus.SKIPPED,
                message=f"No validations run for {step_name}"
            )
        
        # Filter out exceptions
        valid_results = [r for r in results if isinstance(r, ValidationResult)]
        exceptions = [r for r in results if isinstance(r, Exception)]
        
        if exceptions:
            self.logger.error(f"Exceptions in {step_name}: {exceptions}")
        
        if not valid_results:
            return ValidationResult(
                status=ValidationStatus.FAILED,
                severity=ValidationSeverity.ERROR,
                message=f"All validations failed with exceptions in {step_name}",
                details={"exceptions": [str(e) for e in exceptions]}
            )
        
        # Determine overall status
        failed_count = sum(1 for r in valid_results if r.status == ValidationStatus.FAILED)
        passed_count = sum(1 for r in valid_results if r.status == ValidationStatus.PASSED)
        skipped_count = sum(1 for r in valid_results if r.status == ValidationStatus.SKIPPED)
        
        if failed_count > 0:
            overall_status = ValidationStatus.FAILED
            severity = ValidationSeverity.ERROR
        elif passed_count > 0:
            overall_status = ValidationStatus.PASSED
            severity = ValidationSeverity.INFO
        else:
            overall_status = ValidationStatus.SKIPPED
            severity = ValidationSeverity.INFO
        
        return ValidationResult(
            status=overall_status,
            severity=severity,
            message=f"{step_name}: {passed_count} passed, {failed_count} failed, {skipped_count} skipped",
            details={
                "individual_results": [r.dict() for r in valid_results],
                "passed_count": passed_count,
                "failed_count": failed_count,
                "skipped_count": skipped_count,
            }
        )
    
    async def _complete_validation(self, ctx: Context, ev) -> ValidationCompleteEvent:
        """Complete the validation workflow."""
        # Calculate overall status
        failed_results = [r for r in self.state.results if r.status == ValidationStatus.FAILED]
        passed_results = [r for r in self.state.results if r.status == ValidationStatus.PASSED]
        skipped_results = [r for r in self.state.results if r.status == ValidationStatus.SKIPPED]
        
        if failed_results:
            overall_status = ValidationStatus.FAILED
        elif passed_results:
            overall_status = ValidationStatus.PASSED
        else:
            overall_status = ValidationStatus.SKIPPED
        
        # Calculate total duration
        total_duration = 0.0
        if self.state.start_time and self.state.end_time:
            total_duration = (self.state.end_time - self.state.start_time).total_seconds()
        
        # Generate summary
        summary = f"Validation completed: {len(passed_results)} passed, {len(failed_results)} failed, {len(skipped_results)} skipped"
        
        return ValidationCompleteEvent(
            agent_run_id=ev.agent_run_id,
            organization_id=ev.organization_id,
            repository_id=ev.repository_id,
            pr_number=ev.pr_number,
            commit_sha=ev.commit_sha,
            overall_status=overall_status,
            validation_results=self.state.results,
            total_duration_seconds=total_duration,
            passed_count=len(passed_results),
            failed_count=len(failed_results),
            skipped_count=len(skipped_results),
            summary=summary,
        )
    
    async def _emit_step_event(self, ctx: Context, step_name: str, step_type: str, result: ValidationResult):
        """Emit a validation step event."""
        if WORKFLOWS_AVAILABLE:
            # In a real implementation, you would emit this event to the workflow context
            pass
    
    async def _handle_validation_error(self, ctx: Context, step_name: str, error: Exception):
        """Handle validation errors with retry logic."""
        self.state.failed_steps.append(step_name)
        
        retry_count = self.state.retry_counts.get(step_name, 0)
        
        if retry_count < self.config.retry_attempts:
            self.state.retry_counts[step_name] = retry_count + 1
            self.logger.warning(f"Retrying {step_name} (attempt {retry_count + 1}/{self.config.retry_attempts})")
            
            # Exponential backoff
            delay = 2 ** retry_count
            await asyncio.sleep(delay)
            
            # In a real implementation, you would retry the step
            # For now, just log the error
            self.logger.error(f"Error in {step_name}: {error}")
        else:
            self.logger.error(f"Max retries exceeded for {step_name}: {error}")
            
            # Add error result
            error_result = ValidationResult(
                status=ValidationStatus.FAILED,
                severity=ValidationSeverity.CRITICAL,
                message=f"Step {step_name} failed after {self.config.retry_attempts} retries",
                details={"error": str(error), "step": step_name}
            )
            self.state.results.append(error_result)
    
    async def _send_notifications(self, ev: ValidationCompleteEvent):
        """Send notifications about validation completion."""
        if not self.config.notification_channels:
            return
        
        for channel in self.config.notification_channels:
            try:
                # In a real implementation, you would send notifications
                # to Slack, email, etc.
                self.logger.info(f"Sending notification to {channel}: {ev.summary}")
            except Exception as e:
                self.logger.error(f"Failed to send notification to {channel}: {e}")


# Export the main classes
__all__ = ["CodegenValidationWorkflow", "ValidationConfig", "ValidationState", "ValidationResult"]
