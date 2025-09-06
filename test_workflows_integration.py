#!/usr/bin/env python3
"""
Comprehensive Test Suite for Codegen Workflows-py Integration

This script validates the proper integration of workflows-py library
with Codegen's CI/CD validation system.
"""

import asyncio
import logging
import os
import sys
import traceback
from datetime import datetime
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Verify environment variables
required_env_vars = ['CODEGEN_ORG_ID', 'CODEGEN_API_TOKEN', 'GITHUB_TOKEN']
missing_vars = [var for var in required_env_vars if not os.getenv(var)]
if missing_vars:
    logger.error(f"Missing required environment variables: {missing_vars}")
    sys.exit(1)

logger.info("✅ Environment variables validated")

try:
    # Import workflows-py components
    from workflows import Context, Workflow, step
    from workflows.events import StartEvent, StopEvent, Event
    from workflows.server import WorkflowServer
    logger.info("✅ workflows-py library imported successfully")
except ImportError as e:
    logger.error(f"❌ Failed to import workflows-py: {e}")
    logger.info("Please install workflows-py: pip install -e /tmp/workflows-py")
    sys.exit(1)

try:
    # Import Codegen workflows components
    from src.codegen.workflows import (
        CodegenValidationWorkflow,
        ValidationConfig,
        ValidationStatus,
        ValidationSeverity,
        ValidationResult,
    )
    from src.codegen.workflows.events import (
        AgentRunValidationEvent,
        CodeQualityValidationEvent,
        SecurityValidationEvent,
        DeploymentValidationEvent,
        ValidationCompleteEvent,
    )
    logger.info("✅ Codegen workflows components imported successfully")
except ImportError as e:
    logger.error(f"❌ Failed to import Codegen workflows: {e}")
    logger.error(f"Traceback: {traceback.format_exc()}")
    sys.exit(1)


class TestValidationWorkflow(Workflow):
    """Simple test workflow to validate workflows-py integration."""
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    @step
    async def start_test(self, ctx: Context, ev: StartEvent) -> StopEvent:
        """Test step that validates basic workflow functionality."""
        self.logger.info("Starting test workflow")
        
        # Extract test parameters
        test_name = getattr(ev, 'test_name', 'unknown')
        organization_id = getattr(ev, 'organization_id', os.getenv('CODEGEN_ORG_ID'))
        
        self.logger.info(f"Running test: {test_name}")
        self.logger.info(f"Organization ID: {organization_id}")
        
        # Store in context
        ctx.data['test_name'] = test_name
        ctx.data['organization_id'] = organization_id
        ctx.data['start_time'] = datetime.utcnow().isoformat()
        
        # Simulate some work
        await asyncio.sleep(0.1)
        
        result = {
            'test_name': test_name,
            'status': 'passed',
            'organization_id': organization_id,
            'duration': 0.1,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        self.logger.info(f"Test completed: {result}")
        return StopEvent(result=result)


async def test_basic_workflow():
    """Test 1: Basic workflow execution using workflows-py."""
    logger.info("🧪 Test 1: Basic Workflow Execution")
    
    try:
        # Create test workflow
        workflow = TestValidationWorkflow()
        
        # Create start event with test parameters
        start_event = StartEvent(
            test_name="basic_workflow_test",
            organization_id=os.getenv('CODEGEN_ORG_ID'),
            timestamp=datetime.utcnow().isoformat()
        )
        
        # Execute workflow
        result = await workflow.run(start_event)
        
        # Validate result
        assert isinstance(result, StopEvent), f"Expected StopEvent, got {type(result)}"
        assert hasattr(result, 'result'), "StopEvent should have result attribute"
        assert result.result['status'] == 'passed', f"Expected passed status, got {result.result['status']}"
        
        logger.info("✅ Test 1 PASSED: Basic workflow execution successful")
        return True
        
    except Exception as e:
        logger.error(f"❌ Test 1 FAILED: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False


async def test_codegen_validation_workflow():
    """Test 2: Codegen validation workflow initialization."""
    logger.info("🧪 Test 2: Codegen Validation Workflow")
    
    try:
        # Create validation configuration
        config = ValidationConfig(
            timeout_seconds=300,
            max_retries=2,
            parallel_execution=True,
            enable_security_validation=True,
            enable_deployment_validation=False,
        )
        
        # Create validation workflow
        workflow = CodegenValidationWorkflow(config=config)
        
        # Verify workflow is properly initialized
        assert isinstance(workflow, Workflow), "CodegenValidationWorkflow should inherit from Workflow"
        assert workflow.config is not None, "Workflow should have config"
        assert workflow.config.timeout_seconds == 300, "Config should be properly set"
        
        logger.info("✅ Test 2 PASSED: Codegen validation workflow initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Test 2 FAILED: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False


async def test_workflow_server():
    """Test 3: Workflow server integration."""
    logger.info("🧪 Test 3: Workflow Server Integration")
    
    try:
        # Create workflows-py server
        server = WorkflowServer()
        
        # Create test workflows
        test_workflow = TestValidationWorkflow()
        validation_config = ValidationConfig(enable_security_validation=False)
        validation_workflow = CodegenValidationWorkflow(config=validation_config)
        
        # Add workflows to server
        server.add_workflow("test", test_workflow)
        server.add_workflow("validation", validation_workflow)
        
        # Verify workflows are added
        assert "test" in server._workflows, "Test workflow should be added to server"
        assert "validation" in server._workflows, "Validation workflow should be added to server"
        
        logger.info("✅ Test 3 PASSED: Workflow server integration successful")
        return True
        
    except Exception as e:
        logger.error(f"❌ Test 3 FAILED: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False


async def test_event_system():
    """Test 4: Event system validation."""
    logger.info("🧪 Test 4: Event System Validation")
    
    try:
        # Test event creation
        agent_run_event = AgentRunValidationEvent(
            agent_run_id="test-agent-run-123",
            organization_id=os.getenv('CODEGEN_ORG_ID'),
            repository_id="test-repo-456",
            pr_number=42,
            commit_sha="abc123def456",
            agent_type="test_agent",
            prompt="Test validation",
            source_type="api",
            execution_status="completed",
        )
        
        # Verify event properties
        assert isinstance(agent_run_event, Event), "AgentRunValidationEvent should inherit from Event"
        assert agent_run_event.agent_run_id == "test-agent-run-123", "Event should have correct agent_run_id"
        assert agent_run_event.organization_id == os.getenv('CODEGEN_ORG_ID'), "Event should have correct organization_id"
        
        # Test other event types
        code_quality_event = CodeQualityValidationEvent(
            agent_run_id="test-agent-run-123",
            organization_id=os.getenv('CODEGEN_ORG_ID'),
            linting_results=[],
            test_coverage=85.5,
            complexity_score=7.2,
        )
        
        assert isinstance(code_quality_event, Event), "CodeQualityValidationEvent should inherit from Event"
        assert code_quality_event.test_coverage == 85.5, "Event should have correct test_coverage"
        
        logger.info("✅ Test 4 PASSED: Event system validation successful")
        return True
        
    except Exception as e:
        logger.error(f"❌ Test 4 FAILED: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False


async def test_validation_workflow_execution():
    """Test 5: Full validation workflow execution."""
    logger.info("🧪 Test 5: Full Validation Workflow Execution")
    
    try:
        # Create validation workflow
        config = ValidationConfig(
            timeout_seconds=60,  # Shorter timeout for testing
            max_retries=1,
            parallel_execution=False,  # Sequential for easier testing
            enable_security_validation=False,  # Disable for faster testing
            enable_deployment_validation=False,
        )
        workflow = CodegenValidationWorkflow(config=config)
        
        # Create start event with validation parameters
        start_event = StartEvent(
            agent_run_id="test-validation-123",
            organization_id=os.getenv('CODEGEN_ORG_ID'),
            repository_id="test-repo-789",
            pr_number=99,
            commit_sha="test123abc456",
            agent_type="validation_test",
            prompt="Test full validation workflow",
            source_type="test",
            execution_status="completed",
            result_summary="Test validation execution",
            output_files=["test_file.py"],
            tokens_used=100,
            api_calls_made=5,
        )
        
        # Execute workflow (this will test the actual step execution)
        logger.info("Executing validation workflow...")
        result = await workflow.run(start_event)
        
        # Validate result
        assert isinstance(result, StopEvent), f"Expected StopEvent, got {type(result)}"
        logger.info(f"Workflow result: {result}")
        
        logger.info("✅ Test 5 PASSED: Full validation workflow execution successful")
        return True
        
    except Exception as e:
        logger.error(f"❌ Test 5 FAILED: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False


async def test_environment_integration():
    """Test 6: Environment and API integration."""
    logger.info("🧪 Test 6: Environment and API Integration")
    
    try:
        # Test environment variables
        org_id = os.getenv('CODEGEN_ORG_ID')
        api_token = os.getenv('CODEGEN_API_TOKEN')
        github_token = os.getenv('GITHUB_TOKEN')
        
        assert org_id == '323', f"Expected org_id 323, got {org_id}"
        assert api_token.startswith('sk-'), f"API token should start with 'sk-', got {api_token[:10]}..."
        assert github_token.startswith('github_pat_'), f"GitHub token should start with 'github_pat_', got {github_token[:15]}..."
        
        # Test token format validation
        assert len(api_token) > 20, "API token should be longer than 20 characters"
        assert len(github_token) > 30, "GitHub token should be longer than 30 characters"
        
        logger.info("✅ Test 6 PASSED: Environment and API integration successful")
        return True
        
    except Exception as e:
        logger.error(f"❌ Test 6 FAILED: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False


async def run_all_tests():
    """Run all validation tests."""
    logger.info("🚀 Starting Comprehensive Workflows-py Integration Tests")
    logger.info("=" * 60)
    
    tests = [
        ("Basic Workflow Execution", test_basic_workflow),
        ("Codegen Validation Workflow", test_codegen_validation_workflow),
        ("Workflow Server Integration", test_workflow_server),
        ("Event System Validation", test_event_system),
        ("Full Validation Workflow", test_validation_workflow_execution),
        ("Environment Integration", test_environment_integration),
    ]
    
    results = []
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        logger.info(f"\n{'='*20} {test_name} {'='*20}")
        try:
            result = await test_func()
            results.append((test_name, result))
            if result:
                passed += 1
            else:
                failed += 1
        except Exception as e:
            logger.error(f"❌ Test '{test_name}' crashed: {e}")
            results.append((test_name, False))
            failed += 1
        
        # Small delay between tests
        await asyncio.sleep(0.1)
    
    # Print summary
    logger.info("\n" + "=" * 60)
    logger.info("🏁 TEST SUMMARY")
    logger.info("=" * 60)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        logger.info(f"{status}: {test_name}")
    
    logger.info(f"\nTotal Tests: {len(tests)}")
    logger.info(f"Passed: {passed}")
    logger.info(f"Failed: {failed}")
    logger.info(f"Success Rate: {(passed/len(tests)*100):.1f}%")
    
    if failed == 0:
        logger.info("\n🎉 ALL TESTS PASSED! Workflows-py integration is working correctly!")
        return True
    else:
        logger.error(f"\n💥 {failed} TESTS FAILED! Please review the errors above.")
        return False


if __name__ == "__main__":
    try:
        success = asyncio.run(run_all_tests())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("\n⏹️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"💥 Test suite crashed: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        sys.exit(1)
