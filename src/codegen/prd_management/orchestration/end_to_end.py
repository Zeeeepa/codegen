"""
End-to-End Orchestrator - The master orchestration system that ties all components together
This is the final step (Step 30) of the 30-step PRD Management & Implementation System
"""

import asyncio
import json
import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime

from ....sdk.client import CodegenClient
from ..core.prd_template import PRDTemplate, PRDStatus, TaskStatus
from ..core.pro_mode_engine import ProModeEngine, ProModeRequest
from ..services.task_breakdown import TaskBreakdownService
from ..services.agent_orchestrator import AgentOrchestrator
from ..services.validation_engine import ValidationEngine
from ..services.enhanced.visual_testing_v2 import EnhancedVisualTestingService
from ..services.enhanced.performance_testing_v2 import EnhancedPerformanceTestingService
from ..services.enhanced.security_testing_v2 import EnhancedSecurityTestingService
from ..services.completion_verification import CompletionVerificationService
from ..services.deployment_pipeline import DeploymentPipelineService
from ..services.reporting import ReportingService
from ..services.retry_recovery import RetryRecoveryService
from ..core.prd_storage import PRDStorageService
from ..services.websocket_service import WebSocketService
from ..services.progress_tracker import ProgressTracker
from ..services.file_management import FileManagementService


@dataclass
class PRDPipelineRequest:
    user_prompt: str
    org_id: int
    repo_id: int
    deployment_config: Optional[Dict[str, Any]] = None
    pro_mode_config: Optional[Dict[str, Any]] = None


@dataclass
class ProModeConfig:
    num_generations: int = 10
    temperature: float = 0.9


@dataclass
class DeploymentConfig:
    environment: str = "staging"
    platform: str = "vercel"
    domain: Optional[str] = None
    package_manager: str = "npm"
    build_target: Optional[str] = None


@dataclass
class ImplementationResult:
    prd_id: str
    status: str
    branch_name: Optional[str] = None
    commit_hash: Optional[str] = None
    pr_url: Optional[str] = None
    duration: int = 0
    tasks_completed: int = 0
    total_tasks: int = 0
    error: Optional[str] = None


@dataclass
class ValidationReport:
    prd_id: str
    timestamp: str
    levels: Dict[str, Any]
    overall_status: str
    error: Optional[str] = None


@dataclass
class ComprehensiveValidationResult:
    validation: ValidationReport
    visual: List[Dict[str, Any]]
    performance: List[Dict[str, Any]]
    security: List[Dict[str, Any]]


@dataclass
class CompletionVerificationResult:
    prd_id: str
    overall_status: str
    verifications: Dict[str, Any]
    recommendations: List[str]
    timestamp: str


@dataclass
class DeploymentResult:
    deployment_id: str
    prd_id: str
    status: str
    environment: str
    url: Optional[str] = None
    build_info: Optional[Dict[str, Any]] = None
    health_check: Optional[Dict[str, Any]] = None
    monitoring_endpoints: Optional[List[str]] = None
    error: Optional[str] = None
    timestamp: str = ""


@dataclass
class ComprehensiveReport:
    id: str
    prd_id: str
    timestamp: str
    executive_summary: str
    implementation: Dict[str, Any]
    quality: Dict[str, Any]
    security: Dict[str, Any]
    verification: CompletionVerificationResult
    deployment: Optional[Dict[str, Any]]
    recommendations: List[str]
    metrics: Dict[str, Any]


@dataclass
class PRDPipelineResult:
    pipeline_id: str
    prd: Optional[PRDTemplate] = None
    implementation_result: Optional[ImplementationResult] = None
    validation_results: Optional[ComprehensiveValidationResult] = None
    verification_result: Optional[CompletionVerificationResult] = None
    deployment_result: Optional[DeploymentResult] = None
    comprehensive_report: Optional[ComprehensiveReport] = None
    duration: int = 0
    status: str = "pending"
    error: Optional[str] = None


class ServiceDependencies:
    """Container for all service dependencies"""
    
    def __init__(self, codegen_client: CodegenClient):
        self.codegen_client = codegen_client
        self.websocket = WebSocketService()
        self.prd_storage = PRDStorageService()
        self.progress_tracker = ProgressTracker(self.websocket)
        
        # Core engines
        self.pro_mode_engine = ProModeEngine(codegen_client)
        
        # Services
        self.task_breakdown_service = TaskBreakdownService(codegen_client, self.pro_mode_engine)
        self.agent_orchestrator = AgentOrchestrator(codegen_client, self.progress_tracker, self.websocket)
        self.validation_engine = ValidationEngine(codegen_client, self.websocket)
        
        # Enhanced testing services
        self.visual_testing_service = EnhancedVisualTestingService(codegen_client, self._get_visual_config())
        self.performance_testing_service = EnhancedPerformanceTestingService(codegen_client, self._get_performance_config())
        self.security_testing_service = EnhancedSecurityTestingService(codegen_client, self._get_security_config())
        
        # Completion and deployment
        self.completion_verification_service = CompletionVerificationService(codegen_client, self.pro_mode_engine)
        self.deployment_pipeline_service = DeploymentPipelineService(codegen_client, self.websocket)
        self.reporting_service = ReportingService(self.prd_storage, self.websocket)
        self.retry_recovery_service = RetryRecoveryService(codegen_client, self.pro_mode_engine, self.websocket)
        self.file_management_service = FileManagementService(codegen_client)
    
    def _get_visual_config(self):
        """Get visual testing configuration"""
        from ..services.enhanced.visual_testing_v2 import (
            EnhancedVisualTestingConfig, CypressConfig, StorybookConfig, VisualRegressionConfig
        )
        return EnhancedVisualTestingConfig(
            cypress=CypressConfig(),
            storybook=StorybookConfig(),
            visual_regression=VisualRegressionConfig()
        )
    
    def _get_performance_config(self):
        """Get performance testing configuration"""
        return {}  # Will be implemented in performance service
    
    def _get_security_config(self):
        """Get security testing configuration"""
        return {}  # Will be implemented in security service


class EndToEndOrchestrator:
    """
    Master orchestration system that coordinates the complete PRD pipeline
    This is the culmination of all 30 steps working together
    """
    
    def __init__(self, codegen_client: CodegenClient):
        self.services = ServiceDependencies(codegen_client)
        self.codegen_client = codegen_client
    
    async def execute_prd_pipeline(self, request: PRDPipelineRequest) -> PRDPipelineResult:
        """
        MASTER ORCHESTRATION METHOD
        Execute the complete end-to-end PRD pipeline
        """
        pipeline_id = f"pipeline-{int(time.time())}"
        start_time = time.time()
        
        try:
            # Phase 1: PRD Generation using Pro Mode
            self.services.websocket.send('pipeline_phase', {
                'pipeline_id': pipeline_id,
                'phase': 'prd_generation',
                'status': 'started'
            })
            
            prd = await self._execute_with_retry(
                lambda: self._generate_prd_with_pro_mode(request),
                f"{pipeline_id}-prd-gen",
                "prd_generation",
                request.org_id,
                request.repo_id,
                {"prd_request": request}
            )
            
            # Store the generated PRD
            await self.services.prd_storage.save_prd(prd)
            
            # Phase 2: Task Breakdown
            self.services.websocket.send('pipeline_phase', {
                'pipeline_id': pipeline_id,
                'phase': 'task_breakdown',
                'status': 'started'
            })
            
            tasks = await self._execute_with_retry(
                lambda: self.services.task_breakdown_service.breakdown_prd_into_tasks(
                    prd, request.org_id, request.repo_id
                ),
                f"{pipeline_id}-breakdown",
                "task_breakdown",
                request.org_id,
                request.repo_id,
                {"prd": prd}
            )
            
            prd.implementation.tasks = tasks
            await self.services.prd_storage.save_prd(prd)
            
            # Phase 3: Implementation
            self.services.websocket.send('pipeline_phase', {
                'pipeline_id': pipeline_id,
                'phase': 'implementation',
                'status': 'started'
            })
            
            implementation_result = await self._execute_with_retry(
                lambda: self._execute_implementation(prd, tasks, request.org_id, request.repo_id),
                f"{pipeline_id}-implementation",
                "implementation",
                request.org_id,
                request.repo_id,
                {"prd": prd, "tasks": tasks}
            )
            
            # Phase 4: Comprehensive Validation
            self.services.websocket.send('pipeline_phase', {
                'pipeline_id': pipeline_id,
                'phase': 'validation',
                'status': 'started'
            })
            
            validation_results = await self._run_comprehensive_validation(
                prd, request.org_id, request.repo_id
            )
            
            # Phase 5: Completion Verification
            self.services.websocket.send('pipeline_phase', {
                'pipeline_id': pipeline_id,
                'phase': 'verification',
                'status': 'started'
            })
            
            verification_result = await self.services.completion_verification_service.verify_prd_completion(
                prd, implementation_result, validation_results.validation, request.org_id, request.repo_id
            )
            
            # Phase 6: Deployment (if requested)
            deployment_result = None
            if request.deployment_config:
                self.services.websocket.send('pipeline_phase', {
                    'pipeline_id': pipeline_id,
                    'phase': 'deployment',
                    'status': 'started'
                })
                
                deployment_config = DeploymentConfig(**request.deployment_config)
                deployment_result = await self._execute_with_retry(
                    lambda: self.services.deployment_pipeline_service.deploy_implementation(
                        prd, implementation_result, verification_result,
                        request.org_id, request.repo_id, deployment_config
                    ),
                    f"{pipeline_id}-deployment",
                    "deployment",
                    request.org_id,
                    request.repo_id,
                    {"prd": prd, "implementation_result": implementation_result, "verification_result": verification_result}
                )
            
            # Phase 7: Comprehensive Reporting
            self.services.websocket.send('pipeline_phase', {
                'pipeline_id': pipeline_id,
                'phase': 'reporting',
                'status': 'started'
            })
            
            comprehensive_report = await self.services.reporting_service.generate_comprehensive_report(
                prd, implementation_result, validation_results.validation,
                validation_results.security, verification_result, deployment_result
            )
            
            # Final Result
            pipeline_result = PRDPipelineResult(
                pipeline_id=pipeline_id,
                prd=prd,
                implementation_result=implementation_result,
                validation_results=validation_results,
                verification_result=verification_result,
                deployment_result=deployment_result,
                comprehensive_report=comprehensive_report,
                duration=int(time.time() - start_time),
                status=self._determine_pipeline_status(
                    implementation_result, verification_result, deployment_result
                )
            )
            
            # Broadcast completion
            self.services.websocket.send('pipeline_complete', {
                'pipeline_id': pipeline_id,
                'status': pipeline_result.status,
                'duration': pipeline_result.duration,
                'report_id': comprehensive_report.id
            })
            
            return pipeline_result
            
        except Exception as error:
            # Pipeline failed
            failed_result = PRDPipelineResult(
                pipeline_id=pipeline_id,
                status='failed',
                error=str(error),
                duration=int(time.time() - start_time)
            )
            
            self.services.websocket.send('pipeline_failed', {
                'pipeline_id': pipeline_id,
                'error': str(error),
                'duration': failed_result.duration
            })
            
            return failed_result
    
    async def _generate_prd_with_pro_mode(self, request: PRDPipelineRequest) -> PRDTemplate:
        """Generate PRD using Pro Mode engine"""
        
        # Build comprehensive PRD generation prompt
        prd_prompt = self._build_prd_generation_prompt(request)
        
        # Configure Pro Mode
        pro_mode_config = request.pro_mode_config or {}
        num_gens = pro_mode_config.get('num_generations', 10)
        temperature = pro_mode_config.get('temperature', 0.9)
        
        # Use Pro Mode to generate multiple PRD candidates and synthesize the best one
        pro_mode_request = ProModeRequest(
            prompt=prd_prompt,
            num_gens=num_gens,
            temperature=temperature,
            org_id=request.org_id,
            repo_id=request.repo_id
        )
        
        pro_mode_result = await self.services.pro_mode_engine.execute_pro_mode(pro_mode_request)
        
        # Parse the synthesized PRD
        prd = self._parse_prd_from_response(pro_mode_result.final, request)
        
        # Validate PRD structure
        self._validate_prd_structure(prd)
        
        return prd
    
    def _build_prd_generation_prompt(self, request: PRDPipelineRequest) -> str:
        """Build comprehensive PRD generation prompt"""
        return f"""
# Generate Comprehensive PRD using Base PRP Template v2

## User Input
{request.user_prompt}

## Project Context
Organization: {request.org_id}
Repository: {request.repo_id}

## Requirements
Generate a complete PRD following the Base PRP Template v2 structure:

1. **Goal**: Clear, specific end state
2. **Why**: Business value and user impact
3. **What**: User-visible behavior and technical requirements
4. **Success Criteria**: Measurable outcomes
5. **Context**: Documentation, codebase trees, gotchas
6. **Implementation**: Data models, tasks, pseudocode, integration points
7. **Validation**: Syntax checks, unit tests, integration tests, checklist

## Output Format
Provide a complete, structured PRD in JSON format:

{{
  "title": "PRD Title",
  "goal": "What needs to be built...",
  "why": ["Business value 1", "Business value 2"],
  "what": "User-visible behavior...",
  "successCriteria": ["Measurable outcome 1", "Measurable outcome 2"],
  "context": {{
    "documentation": [],
    "codebaseTree": "Current structure...",
    "desiredTree": "Desired structure...",
    "gotchas": ["Known issue 1", "Known issue 2"]
  }},
  "implementation": {{
    "dataModels": "Data model definitions...",
    "tasks": [],
    "pseudocode": "Implementation pseudocode...",
    "integrationPoints": []
  }},
  "validation": {{
    "syntaxChecks": ["ruff check .", "mypy ."],
    "unitTests": ["pytest tests/"],
    "integrationTests": ["pytest tests/integration/"],
    "checklist": ["All tests pass", "No linting errors"]
  }}
}}

Make the PRD comprehensive, actionable, and ready for implementation.
"""
    
    def _parse_prd_from_response(self, response: str, request: PRDPipelineRequest) -> PRDTemplate:
        """Parse PRD from Pro Mode response"""
        try:
            # Extract JSON from response
            json_match = response.find('{')
            if json_match == -1:
                raise ValueError("No JSON found in PRD response")
            
            json_end = response.rfind('}') + 1
            json_str = response[json_match:json_end]
            parsed_prd = json.loads(json_str)
            
            # Create complete PRD template
            prd = PRDTemplate.create_new(
                title=parsed_prd.get('title', 'Generated PRD'),
                goal=parsed_prd.get('goal', ''),
                what=parsed_prd.get('what', '')
            )
            
            # Populate from parsed data
            prd.why = parsed_prd.get('why', [])
            prd.success_criteria = parsed_prd.get('successCriteria', [])
            
            # Context
            context_data = parsed_prd.get('context', {})
            prd.context.codebase_tree = context_data.get('codebaseTree', '')
            prd.context.desired_tree = context_data.get('desiredTree', '')
            prd.context.gotchas = context_data.get('gotchas', [])
            
            # Implementation
            impl_data = parsed_prd.get('implementation', {})
            prd.implementation.data_models = impl_data.get('dataModels', '')
            prd.implementation.pseudocode = impl_data.get('pseudocode', '')
            
            # Validation
            val_data = parsed_prd.get('validation', {})
            prd.validation.syntax_checks = val_data.get('syntaxChecks', ['npm run lint'])
            prd.validation.unit_tests = val_data.get('unitTests', ['npm test'])
            prd.validation.integration_tests = val_data.get('integrationTests', ['npm run test:integration'])
            prd.validation.checklist = val_data.get('checklist', ['All tests pass'])
            
            return prd
            
        except Exception as e:
            raise Exception(f"Failed to parse PRD from response: {str(e)}")
    
    def _validate_prd_structure(self, prd: PRDTemplate) -> None:
        """Validate PRD has required fields"""
        required_fields = ['goal', 'what', 'success_criteria']
        
        for field in required_fields:
            value = getattr(prd, field)
            if not value or (isinstance(value, list) and len(value) == 0):
                raise ValueError(f"PRD missing required field: {field}")
    
    async def _execute_implementation(
        self,
        prd: PRDTemplate,
        tasks: List[Any],
        org_id: int,
        repo_id: int
    ) -> ImplementationResult:
        """Execute implementation using agent orchestrator"""
        
        # Create git branch for implementation
        branch_name = await self.services.file_management_service.create_git_branch(
            prd.id, org_id, repo_id
        )
        
        # Execute implementation using agent orchestrator
        await self.services.agent_orchestrator.execute_implementation(
            prd, tasks, org_id, repo_id
        )
        
        # Commit changes
        commit_hash = await self.services.file_management_service.commit_changes(
            prd.id, f"Implement PRD: {prd.title}", org_id, repo_id
        )
        
        # Create pull request
        pr_url = await self._create_pull_request(prd, branch_name, org_id, repo_id)
        
        return ImplementationResult(
            prd_id=prd.id,
            status='completed',
            branch_name=branch_name,
            commit_hash=commit_hash,
            pr_url=pr_url,
            duration=0,  # Will be calculated by orchestrator
            tasks_completed=len([t for t in tasks if t.status == TaskStatus.COMPLETED]),
            total_tasks=len(tasks)
        )
    
    async def _run_comprehensive_validation(
        self,
        prd: PRDTemplate,
        org_id: int,
        repo_id: int
    ) -> ComprehensiveValidationResult:
        """Run all validation types in parallel"""
        
        # Run all validation types concurrently for efficiency
        validation_tasks = [
            self.services.validation_engine.validate_implementation(prd, org_id, repo_id),
            self.services.visual_testing_service.run_comprehensive_visual_tests(prd, org_id, repo_id),
            self.services.performance_testing_service.run_comprehensive_performance_tests(prd, org_id, repo_id),
            self.services.security_testing_service.run_comprehensive_security_tests(prd, org_id, repo_id)
        ]
        
        results = await asyncio.gather(*validation_tasks)
        
        return ComprehensiveValidationResult(
            validation=results[0],
            visual=[results[1]],  # Convert to list format
            performance=[results[2]],
            security=[results[3]]
        )
    
    async def _create_pull_request(
        self,
        prd: PRDTemplate,
        branch_name: str,
        org_id: int,
        repo_id: int
    ) -> str:
        """Create pull request for the implementation"""
        
        pr_prompt = f"""
Create a pull request for the implemented PRD:

Title: Implement PRD: {prd.title}
Branch: {branch_name}

Description:
## PRD Implementation: {prd.title}

### Goal
{prd.goal}

### What Was Built
{prd.what}

### Success Criteria
{chr(10).join(f"- [ ] {criteria}" for criteria in prd.success_criteria)}

### Tasks Completed
{chr(10).join(f"- [{'x' if task.status == TaskStatus.COMPLETED else ' '}] {task.title}" for task in prd.implementation.tasks)}

---
*This PR was automatically generated by the Codegen PRD Implementation System*
"""
        
        agent_run = await self.codegen_client.create_agent_run(
            org_id=org_id,
            prompt=pr_prompt,
            repo_id=repo_id
        )
        
        result = await self._poll_completion(org_id, agent_run.id)
        return result.get('pr_url', 'unknown')
    
    def _determine_pipeline_status(
        self,
        implementation_result: ImplementationResult,
        verification_result: CompletionVerificationResult,
        deployment_result: Optional[DeploymentResult]
    ) -> str:
        """Determine overall pipeline status"""
        
        if implementation_result.status == 'failed':
            return 'failed'
        
        if verification_result.overall_status == 'failed':
            return 'failed'
        
        if deployment_result and deployment_result.status == 'failed':
            return 'failed'
        
        if verification_result.overall_status == 'partial':
            return 'partial_success'
        
        return 'success'
    
    async def _execute_with_retry(
        self,
        operation,
        operation_id: str,
        operation_type: str,
        org_id: int,
        repo_id: int,
        metadata: Dict[str, Any]
    ):
        """Execute operation with retry logic"""
        
        from ..services.retry_recovery import RetryContext
        
        context = RetryContext(
            operation_id=operation_id,
            operation_type=operation_type,
            org_id=org_id,
            repo_id=repo_id,
            metadata=metadata
        )
        
        return await self.services.retry_recovery_service.execute_with_retry(operation, context)
    
    async def _poll_completion(self, org_id: int, agent_run_id: str) -> Dict[str, Any]:
        """Poll for agent run completion"""
        timeout = 300  # 5 minutes
        poll_interval = 10  # 10 seconds
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                agent_run = await self.codegen_client.get_agent_run(org_id, agent_run_id)
                
                if agent_run.status == "COMPLETE":
                    return agent_run.result or {}
                elif agent_run.status == "FAILED":
                    raise Exception(f"Operation failed: {agent_run.error}")
                
                await asyncio.sleep(poll_interval)
                
            except Exception as e:
                print(f"Polling error: {e}")
                await asyncio.sleep(poll_interval)
        
        raise Exception("Operation timed out")
    
    # Convenience method for UI integration
    async def execute_prd_from_ui(
        self,
        user_prompt: str,
        org_id: int,
        repo_id: int,
        options: Dict[str, Any] = None
    ) -> PRDPipelineResult:
        """Convenience method for UI integration"""
        
        options = options or {}
        
        request = PRDPipelineRequest(
            user_prompt=user_prompt,
            org_id=org_id,
            repo_id=repo_id,
            deployment_config=options.get('deployment_config'),
            pro_mode_config=options.get('pro_mode_config')
        )
        
        return await self.execute_prd_pipeline(request)


# Main Application Integration
class CodegenPRDApp:
    """
    Main application class that provides the complete PRD management system
    """
    
    def __init__(self, codegen_client: CodegenClient):
        self.orchestrator = EndToEndOrchestrator(codegen_client)
    
    async def execute_prd(
        self,
        user_prompt: str,
        org_id: int,
        repo_id: int,
        options: Dict[str, Any] = None
    ) -> PRDPipelineResult:
        """
        Main entry point for the complete system
        
        Args:
            user_prompt: User's request for what to build
            org_id: Organization ID
            repo_id: Repository ID
            options: Optional configuration for deployment and Pro Mode
            
        Returns:
            Complete pipeline result with PRD, implementation, validation, and deployment
        """
        return await self.orchestrator.execute_prd_from_ui(
            user_prompt, org_id, repo_id, options
        )
    
    # Synchronous wrapper for backward compatibility
    def execute_prd_sync(
        self,
        user_prompt: str,
        org_id: int,
        repo_id: int,
        options: Dict[str, Any] = None
    ) -> PRDPipelineResult:
        """Synchronous wrapper for execute_prd"""
        return asyncio.run(self.execute_prd(user_prompt, org_id, repo_id, options))

