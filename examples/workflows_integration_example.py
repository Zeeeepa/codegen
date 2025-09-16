"""
Codegen Workflows Integration Example

This example demonstrates how to use the workflows-py integration for CI/CD completion validation.

Prerequisites:
    pip install -e /tmp/workflows-py  # Install workflows-py library
"""

import asyncio
import logging
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import workflows-py components
from workflows import Context, Workflow, step
from workflows.events import StartEvent, StopEvent
from workflows.server import WorkflowServer

# Import Codegen workflows components
from src.codegen.workflows import (
    CodegenValidationWorkflow,
    ValidationConfig,
    ValidationResult,
    CodegenWorkflowServer,
    WorkflowManager,
    WorkflowPolicy,
    create_workflow_server,
    create_workflow_manager,
)
from src.codegen.workflows.events import (
    ValidationStatus,
    ValidationSeverity,
    AgentRunValidationEvent,
)


async def basic_validation_example():
    """Example of running a basic validation workflow using workflows-py."""
    logger.info("=== Basic Validation Example ===")
    
    # Create a validation workflow with configuration
    config = ValidationConfig(
        timeout_seconds=300,
        max_retries=2,
        parallel_execution=True,
        enable_security_validation=True,
        enable_deployment_validation=False,
    )
    workflow = CodegenValidationWorkflow(config=config)
    
    # Create StartEvent with validation parameters (workflows-py pattern)
    start_event = StartEvent(
        agent_run_id="agent-run-123",
        organization_id="org-456",
        repository_id="repo-789",
        pr_number=42,
        commit_sha="abc123def456",
        agent_type="code_generation",
        prompt="Add input validation to login form",
        source_type="api",
        execution_status="completed",
        result_summary="Successfully added validation",
        output_files=["src/auth/login.py", "tests/test_login.py"],
        tokens_used=1500,
        api_calls_made=5,
    )
    
    logger.info(f"Starting validation for agent run: {start_event.agent_run_id}")
    
    try:
        # Execute validation workflow using workflows-py
        result = await workflow.run(start_event)
        
        logger.info(f"Validation completed: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Validation failed: {e}")
        raise
    
    # Simulate validation results
    validation_results = [
        ValidationResult(
            status=ValidationStatus.PASSED,
            severity=ValidationSeverity.INFO,
            message="Agent run completed successfully",
            duration_seconds=2.5,
        ),
        ValidationResult(
            status=ValidationStatus.PASSED,
            severity=ValidationSeverity.INFO,
            message="Code quality checks passed",
            duration_seconds=15.3,
            details={"files_checked": 2, "language": "python"},
        ),
        ValidationResult(
            status=ValidationStatus.PASSED,
            severity=ValidationSeverity.INFO,
            message="Security scan completed - no issues found",
            duration_seconds=8.7,
        ),
    ]
    
    # Display results
    for i, result in enumerate(validation_results, 1):
        logger.info(f"Step {i}: {result.message} ({result.status.value})")
    
    logger.info("Basic validation completed successfully!")


async def workflow_server_example():
    """Example of running a workflow server using workflows-py WorkflowServer."""
    logger.info("=== Workflow Server Example ===")
    
    try:
        # Create workflows-py server and add our validation workflow
        server = WorkflowServer()
        
        # Add different validation workflow types
        validation_config = ValidationConfig(
            timeout_seconds=300,
            max_retries=2,
            parallel_execution=True,
            enable_security_validation=True,
            enable_deployment_validation=True,
        )
        
        fast_config = ValidationConfig(
            timeout_seconds=120,
            max_retries=1,
            parallel_execution=True,
            enable_security_validation=False,
            enable_deployment_validation=False,
        )
        
        # Add workflows to server
        server.add_workflow("validation", CodegenValidationWorkflow(validation_config))
        server.add_workflow("fast-validation", CodegenValidationWorkflow(fast_config))
        
        logger.info("Workflow server created successfully")
        logger.info("Available workflows:")
        logger.info("  validation - Full validation with security and deployment checks")
        logger.info("  fast-validation - Quick validation for code quality only")
        logger.info("")
        logger.info("Example usage:")
        logger.info("  curl -X POST http://localhost:8080/workflows/validation/run \\")
        logger.info("    -H 'Content-Type: application/json' \\")
        logger.info("    -d '{\"agent_run_id\": \"agent-123\", \"organization_id\": \"org-456\"}'")
        
        # For demo purposes, we'll just show the server is ready
        # In production, you would call: await server.serve(host="localhost", port=8080)
        logger.info("Server ready to serve workflows!")
        
    except Exception as e:
        logger.error(f"Workflow server example failed: {e}")
        logger.info("This is expected if workflows-py is not installed")


async def workflow_manager_example():
    """Example of using the workflow manager with policies."""
    logger.info("=== Workflow Manager Example ===")
    
    # Create a custom policy
    policy = WorkflowPolicy(
        trigger_on_agent_completion=True,
        trigger_on_pr_creation=True,
        trigger_on_pr_update=False,  # Disable PR update triggers
        max_concurrent_workflows=5,
        required_validations={"code_quality", "security"},
        blocking_severities={ValidationSeverity.ERROR, ValidationSeverity.CRITICAL},
        notification_channels=["slack", "email"],
    )
    
    # Create workflow manager
    manager = create_workflow_manager(
        policy=policy,
        server_config={"host": "localhost", "port": 8081}
    )
    
    logger.info("Workflow manager created with custom policy")
    
    # Start a validation workflow
    try:
        result = await manager.start_validation_workflow(
            agent_run_id="agent-run-789",
            organization_id="org-123",
            workflow_type="full-validation",
            priority=8,
            pr_number=456,
            commit_sha="ghi789jkl012",
        )
        
        logger.info(f"Manager started workflow: {result}")
        
        # Get organization metrics
        org_metrics = manager.get_organization_metrics("org-123")
        logger.info(f"Organization metrics: {org_metrics}")
        
        # Update policy
        manager.update_policy({
            "max_concurrent_workflows": 8,
            "timeout_minutes": 45,
        })
        logger.info("Policy updated successfully")
        
    except Exception as e:
        logger.error(f"Workflow manager example failed: {e}")
        logger.info("This is expected if workflows-py is not installed")
    
    finally:
        # Shutdown manager
        await manager.shutdown()
        logger.info("Workflow manager shutdown complete")


async def quality_gates_example():
    """Example of quality gate enforcement."""
    logger.info("=== Quality Gates Example ===")
    
    # Create manager with strict quality gates
    strict_policy = WorkflowPolicy(
        required_validations={"code_quality", "security", "deployment"},
        blocking_severities={ValidationSeverity.WARNING, ValidationSeverity.ERROR, ValidationSeverity.CRITICAL},
        notify_on_failure=True,
    )
    
    manager = create_workflow_manager(policy=strict_policy)
    
    # Simulate validation results
    validation_results = [
        {
            "step_name": "code_quality",
            "step_type": "code_quality",
            "status": ValidationStatus.PASSED.value,
            "severity": ValidationSeverity.INFO.value,
            "message": "Code quality checks passed",
        },
        {
            "step_name": "security_scan",
            "step_type": "security",
            "status": ValidationStatus.FAILED.value,
            "severity": ValidationSeverity.WARNING.value,
            "message": "Found potential security issue",
        },
        {
            "step_name": "deployment_check",
            "step_type": "deployment",
            "status": ValidationStatus.PASSED.value,
            "severity": ValidationSeverity.INFO.value,
            "message": "Deployment validation passed",
        },
    ]
    
    # Enforce quality gates
    quality_result = await manager.enforce_quality_gates(
        workflow_id="test-workflow-123",
        validation_results=validation_results
    )
    
    logger.info(f"Quality gates result: {quality_result}")
    
    if quality_result["passed"]:
        logger.info("✅ All quality gates passed!")
    else:
        logger.warning(f"❌ Quality gates failed: {quality_result['reason']}")
    
    await manager.shutdown()


async def integration_scenarios_example():
    """Example of different integration scenarios."""
    logger.info("=== Integration Scenarios Example ===")
    
    scenarios = [
        {
            "name": "Agent Run Completion",
            "description": "Triggered when an agent run completes",
            "workflow_type": "validation",
            "priority": 7,
        },
        {
            "name": "PR Creation",
            "description": "Triggered when a PR is created",
            "workflow_type": "full-validation",
            "priority": 8,
        },
        {
            "name": "PR Update",
            "description": "Triggered when a PR is updated",
            "workflow_type": "fast-validation",
            "priority": 6,
        },
        {
            "name": "GitHub Check Suite",
            "description": "Triggered by GitHub check suite request",
            "workflow_type": "security-validation",
            "priority": 9,
        },
    ]
    
    for scenario in scenarios:
        logger.info(f"Scenario: {scenario['name']}")
        logger.info(f"  Description: {scenario['description']}")
        logger.info(f"  Workflow Type: {scenario['workflow_type']}")
        logger.info(f"  Priority: {scenario['priority']}")
        logger.info("")


def workflow_types_overview():
    """Overview of available workflow types."""
    logger.info("=== Workflow Types Overview ===")
    
    workflow_types = {
        "validation": {
            "description": "Default validation workflow",
            "includes": ["agent_run", "code_quality", "security"],
            "duration": "~10-15 minutes",
            "use_case": "Standard agent run validation",
        },
        "fast-validation": {
            "description": "Quick validation for PR updates",
            "includes": ["code_quality"],
            "duration": "~2-5 minutes",
            "use_case": "PR updates and quick checks",
        },
        "security-validation": {
            "description": "Security-focused validation",
            "includes": ["security", "secrets", "vulnerabilities"],
            "duration": "~5-10 minutes",
            "use_case": "GitHub check suites and security reviews",
        },
        "full-validation": {
            "description": "Comprehensive validation with deployment",
            "includes": ["agent_run", "code_quality", "security", "deployment"],
            "duration": "~15-30 minutes",
            "use_case": "PR creation and production deployments",
        },
    }
    
    for workflow_type, details in workflow_types.items():
        logger.info(f"Workflow Type: {workflow_type}")
        logger.info(f"  Description: {details['description']}")
        logger.info(f"  Includes: {', '.join(details['includes'])}")
        logger.info(f"  Duration: {details['duration']}")
        logger.info(f"  Use Case: {details['use_case']}")
        logger.info("")


async def main():
    """Run all examples."""
    logger.info("🚀 Starting Codegen Workflows Integration Examples")
    logger.info("=" * 60)
    
    # Run examples
    await basic_validation_example()
    logger.info("")
    
    await workflow_server_example()
    logger.info("")
    
    await workflow_manager_example()
    logger.info("")
    
    await quality_gates_example()
    logger.info("")
    
    await integration_scenarios_example()
    logger.info("")
    
    workflow_types_overview()
    
    logger.info("=" * 60)
    logger.info("✅ All examples completed!")
    logger.info("")
    logger.info("Next Steps:")
    logger.info("1. Install workflows-py: pip install llama-index-workflows")
    logger.info("2. Configure your validation policies")
    logger.info("3. Start the workflow server")
    logger.info("4. Integrate with your CI/CD pipeline")


if __name__ == "__main__":
    asyncio.run(main())
