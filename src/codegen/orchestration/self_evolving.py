"""
Self-Evolving CI/CD Flow Manager

This module provides intelligent, self-adapting CI/CD workflows that learn from
execution patterns, automatically optimize pipeline configurations, and evolve
based on project characteristics and success metrics.
"""

import asyncio
import json
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from pathlib import Path
import yaml

from .schemas import (
    PipelineDefinition, StageDefinition, StageType, AgentTaskConfig,
    ExecutionStatus, TriggerType, PipelineExecution
)
from .engine import OrchestrationEngine
from .parallel_executor import ParallelAgentExecutor
from ..agents.agent import Agent

logger = logging.getLogger(__name__)


@dataclass
class ProjectAnalysis:
    """Analysis results for a project to inform pipeline evolution."""
    project_type: str  # "web", "api", "library", "data", "mobile", etc.
    languages: List[str]
    frameworks: List[str]
    complexity_score: float  # 0-10
    test_coverage: Optional[float] = None
    dependencies_count: int = 0
    file_count: int = 0
    has_database: bool = False
    has_frontend: bool = False
    has_backend: bool = False
    deployment_targets: List[str] = field(default_factory=list)
    

@dataclass
class PipelineMetrics:
    """Metrics for pipeline performance analysis."""
    execution_id: str
    success_rate: float
    average_duration: float
    stage_success_rates: Dict[str, float]
    stage_durations: Dict[str, float]
    failure_patterns: List[str]
    resource_usage: Dict[str, float]
    timestamp: datetime


@dataclass
class EvolutionConfig:
    """Configuration for self-evolution behavior."""
    learning_window_days: int = 30
    min_executions_for_evolution: int = 10
    success_rate_threshold: float = 0.85
    performance_improvement_threshold: float = 0.15
    auto_apply_optimizations: bool = False
    analyze_external_repos: bool = True
    max_pipeline_complexity: int = 20


class ProjectAnalyzer:
    """Analyzes project characteristics to inform pipeline creation."""
    
    async def analyze_project(self, project_path: Path) -> ProjectAnalysis:
        """Analyze a project directory to understand its characteristics."""
        logger.info(f"Analyzing project at {project_path}")
        
        analysis = ProjectAnalysis(
            project_type="unknown",
            languages=[],
            frameworks=[],
            complexity_score=0.0,
            file_count=0
        )
        
        # Analyze file structure and languages
        file_extensions = {}
        framework_indicators = {
            "react": ["package.json", "src/App.js", "src/App.tsx"],
            "vue": ["package.json", "src/App.vue"],
            "angular": ["package.json", "angular.json"],
            "django": ["manage.py", "settings.py"],
            "flask": ["app.py", "flask_app.py"],
            "fastapi": ["main.py", "app.py"],
            "spring": ["pom.xml", "build.gradle"],
            "rails": ["Gemfile", "config/application.rb"],
            "laravel": ["composer.json", "artisan"]
        }
        
        # Walk through project files
        for file_path in project_path.rglob("*"):
            if file_path.is_file():
                analysis.file_count += 1
                
                # Count file extensions
                ext = file_path.suffix.lower()
                file_extensions[ext] = file_extensions.get(ext, 0) + 1
                
                # Check for framework indicators
                relative_path = str(file_path.relative_to(project_path))
                for framework, indicators in framework_indicators.items():
                    if any(indicator in relative_path for indicator in indicators):
                        if framework not in analysis.frameworks:
                            analysis.frameworks.append(framework)
        
        # Determine languages from file extensions
        language_mapping = {
            ".py": "Python",
            ".js": "JavaScript", 
            ".ts": "TypeScript",
            ".java": "Java",
            ".go": "Go",
            ".rs": "Rust",
            ".cpp": "C++",
            ".c": "C",
            ".rb": "Ruby",
            ".php": "PHP",
            ".cs": "C#",
            ".swift": "Swift",
            ".kt": "Kotlin"
        }
        
        for ext, count in file_extensions.items():
            if ext in language_mapping and count > 0:
                analysis.languages.append(language_mapping[ext])
        
        # Determine project type
        if "react" in analysis.frameworks or "vue" in analysis.frameworks or "angular" in analysis.frameworks:
            analysis.project_type = "web"
            analysis.has_frontend = True
        elif "django" in analysis.frameworks or "flask" in analysis.frameworks or "fastapi" in analysis.frameworks:
            analysis.project_type = "api"
            analysis.has_backend = True
        elif "spring" in analysis.frameworks:
            analysis.project_type = "enterprise"
            analysis.has_backend = True
        elif "Python" in analysis.languages and analysis.file_count < 50:
            analysis.project_type = "library"
        else:
            analysis.project_type = "application"
        
        # Calculate complexity score
        complexity_factors = {
            "file_count": min(analysis.file_count / 1000, 1.0) * 3,
            "language_diversity": min(len(analysis.languages) / 5, 1.0) * 2,
            "framework_count": min(len(analysis.frameworks) / 3, 1.0) * 2,
            "has_database": 1.0 if analysis.has_database else 0,
            "full_stack": 2.0 if (analysis.has_frontend and analysis.has_backend) else 0
        }
        
        analysis.complexity_score = sum(complexity_factors.values())
        
        # Check for database usage
        db_files = [".sql", ".db", ".sqlite", "migrations/", "models/"]
        analysis.has_database = any(
            any(indicator in str(f) for indicator in db_files)
            for f in project_path.rglob("*")
        )
        
        logger.info(f"Project analysis complete: {analysis.project_type}, complexity: {analysis.complexity_score}")
        return analysis


class PipelineEvolver:
    """Evolves pipeline configurations based on performance data and best practices."""
    
    def __init__(self, config: EvolutionConfig):
        self.config = config
        self.metrics_history: List[PipelineMetrics] = []
        
    async def analyze_performance(self, executions: List[PipelineExecution]) -> List[PipelineMetrics]:
        """Analyze pipeline execution performance."""
        metrics = []
        
        for execution in executions:
            if not execution.completed_at or not execution.started_at:
                continue
                
            # Calculate success rates and durations
            total_stages = len(execution.tasks)
            successful_stages = sum(1 for task in execution.tasks.values() 
                                  if task.status == ExecutionStatus.SUCCESS)
            
            stage_success_rates = {}
            stage_durations = {}
            
            for stage_id, task in execution.tasks.items():
                stage_success_rates[stage_id] = 1.0 if task.status == ExecutionStatus.SUCCESS else 0.0
                stage_durations[stage_id] = task.duration_seconds or 0.0
            
            metrics.append(PipelineMetrics(
                execution_id=execution.id,
                success_rate=successful_stages / total_stages if total_stages > 0 else 0.0,
                average_duration=execution.duration_seconds or 0.0,
                stage_success_rates=stage_success_rates,
                stage_durations=stage_durations,
                failure_patterns=[],
                resource_usage={},
                timestamp=execution.completed_at
            ))
        
        return metrics
    
    async def suggest_optimizations(self, 
                                  pipeline: PipelineDefinition, 
                                  metrics: List[PipelineMetrics],
                                  project_analysis: ProjectAnalysis) -> Dict[str, Any]:
        """Suggest pipeline optimizations based on performance analysis."""
        
        if len(metrics) < self.config.min_executions_for_evolution:
            return {"status": "insufficient_data", "suggestions": []}
        
        suggestions = []
        
        # Analyze success rates
        recent_metrics = [m for m in metrics 
                         if m.timestamp > datetime.now() - timedelta(days=self.config.learning_window_days)]
        
        if recent_metrics:
            avg_success_rate = sum(m.success_rate for m in recent_metrics) / len(recent_metrics)
            
            if avg_success_rate < self.config.success_rate_threshold:
                suggestions.append({
                    "type": "reliability",
                    "description": f"Success rate ({avg_success_rate:.2%}) below threshold",
                    "action": "add_retry_logic",
                    "priority": "high"
                })
        
        # Analyze stage performance
        stage_metrics = {}
        for metric in recent_metrics:
            for stage_id, duration in metric.stage_durations.items():
                if stage_id not in stage_metrics:
                    stage_metrics[stage_id] = []
                stage_metrics[stage_id].append(duration)
        
        # Identify slow stages
        for stage_id, durations in stage_metrics.items():
            avg_duration = sum(durations) / len(durations)
            if avg_duration > 300:  # 5 minutes threshold
                suggestions.append({
                    "type": "performance",
                    "description": f"Stage '{stage_id}' averages {avg_duration:.1f}s",
                    "action": "optimize_stage_or_parallelize",
                    "priority": "medium",
                    "stage_id": stage_id
                })
        
        # Suggest additional stages based on project analysis
        existing_stage_types = set(stage.stage_type for stage in pipeline.stages)
        
        if project_analysis.project_type == "web" and StageType.DOCKER_RUN not in existing_stage_types:
            suggestions.append({
                "type": "enhancement",
                "description": "Web project could benefit from containerization",
                "action": "add_docker_stage",
                "priority": "low"
            })
        
        if project_analysis.has_database and "migration" not in [s.name.lower() for s in pipeline.stages]:
            suggestions.append({
                "type": "enhancement", 
                "description": "Database project missing migration stage",
                "action": "add_migration_stage",
                "priority": "medium"
            })
        
        return {
            "status": "analysis_complete",
            "suggestions": suggestions,
            "metrics_analyzed": len(recent_metrics),
            "avg_success_rate": avg_success_rate if recent_metrics else 0.0
        }


class SelfEvolvingFlowManager:
    """
    Main manager for self-evolving CI/CD flows.
    
    This class orchestrates the entire self-evolution process:
    1. Analyzes project characteristics
    2. Creates intelligent pipeline templates
    3. Monitors execution performance
    4. Suggests and applies optimizations
    5. Learns from patterns across projects
    """
    
    def __init__(self, 
                 orchestration_engine: OrchestrationEngine,
                 evolution_config: Optional[EvolutionConfig] = None):
        self.engine = orchestration_engine
        self.config = evolution_config or EvolutionConfig()
        self.analyzer = ProjectAnalyzer()
        self.evolver = PipelineEvolver(self.config)
        self.templates_cache: Dict[str, PipelineDefinition] = {}
        
    async def create_intelligent_pipeline(self, 
                                        project_path: Path,
                                        pipeline_name: str,
                                        custom_requirements: Optional[Dict[str, Any]] = None) -> PipelineDefinition:
        """Create an intelligent pipeline based on project analysis."""
        
        logger.info(f"Creating intelligent pipeline for {project_path}")
        
        # Analyze the project
        analysis = await self.analyzer.analyze_project(project_path)
        
        # Get or create template for this project type
        template = await self._get_or_create_template(analysis, custom_requirements)
        
        # Customize the template for this specific project
        pipeline = await self._customize_pipeline(template, analysis, pipeline_name)
        
        # Register the pipeline with the orchestration engine
        self.engine.register_pipeline(pipeline)
        
        logger.info(f"Created intelligent pipeline: {pipeline.name}")
        return pipeline
    
    async def _get_or_create_template(self, 
                                    analysis: ProjectAnalysis,
                                    custom_requirements: Optional[Dict[str, Any]] = None) -> PipelineDefinition:
        """Get existing template or create a new one based on project analysis."""
        
        template_key = f"{analysis.project_type}_{'-'.join(sorted(analysis.frameworks))}"
        
        if template_key in self.templates_cache:
            return self.templates_cache[template_key]
        
        # Create template based on project characteristics
        stages = []
        
        # Always start with initialization
        stages.append(StageDefinition(
            id="init",
            name="Initialize Environment", 
            stage_type=StageType.AGENT_TASK,
            agent_config=AgentTaskConfig(
                prompt=f"Initialize {analysis.project_type} project environment with {', '.join(analysis.languages)} support",
                timeout=300
            ),
            depends_on=[],
            can_run_parallel=True,
            tags=["init", "setup"]
        ))
        
        # Add language-specific setup
        if "Python" in analysis.languages:
            stages.append(StageDefinition(
                id="python_setup",
                name="Python Environment Setup",
                stage_type=StageType.AGENT_TASK,
                agent_config=AgentTaskConfig(
                    prompt="Set up Python virtual environment, install dependencies from requirements.txt or pyproject.toml",
                    timeout=600
                ),
                depends_on=["init"],
                can_run_parallel=True,
                tags=["python", "dependencies"]
            ))
        
        if "JavaScript" in analysis.languages or "TypeScript" in analysis.languages:
            stages.append(StageDefinition(
                id="node_setup",
                name="Node.js Environment Setup", 
                stage_type=StageType.AGENT_TASK,
                agent_config=AgentTaskConfig(
                    prompt="Set up Node.js environment, install npm/yarn dependencies from package.json",
                    timeout=600
                ),
                depends_on=["init"],
                can_run_parallel=True,
                tags=["nodejs", "dependencies"]
            ))
        
        # Add testing stages
        test_depends = []
        if "Python" in analysis.languages:
            test_depends.append("python_setup")
        if any(lang in analysis.languages for lang in ["JavaScript", "TypeScript"]):
            test_depends.append("node_setup")
        if not test_depends:
            test_depends = ["init"]
        
        stages.append(StageDefinition(
            id="run_tests",
            name="Run Test Suite",
            stage_type=StageType.AGENT_TASK,
            agent_config=AgentTaskConfig(
                prompt=f"Run comprehensive test suite for {analysis.project_type} project. Include unit tests, integration tests, and code quality checks.",
                timeout=1200
            ),
            depends_on=test_depends,
            can_run_parallel=True,
            tags=["testing", "quality"]
        ))
        
        # Add build stage for web projects
        if analysis.project_type == "web":
            stages.append(StageDefinition(
                id="build",
                name="Build Application",
                stage_type=StageType.AGENT_TASK,
                agent_config=AgentTaskConfig(
                    prompt="Build the web application for production deployment",
                    timeout=900
                ),
                depends_on=["run_tests"],
                can_run_parallel=True,
                tags=["build", "production"]
            ))
        
        # Add deployment stages based on complexity
        if analysis.complexity_score > 5.0:
            # Complex projects get staging deployment
            build_deps = ["build"] if analysis.project_type == "web" else ["run_tests"]
            
            stages.append(StageDefinition(
                id="deploy_staging",
                name="Deploy to Staging",
                stage_type=StageType.AGENT_TASK,
                agent_config=AgentTaskConfig(
                    prompt="Deploy application to staging environment for final testing",
                    timeout=600
                ),
                depends_on=build_deps,
                can_run_parallel=False,  # Deployment should be sequential
                tags=["deployment", "staging"]
            ))
            
            stages.append(StageDefinition(
                id="integration_tests",
                name="Integration Tests",
                stage_type=StageType.AGENT_TASK,
                agent_config=AgentTaskConfig(
                    prompt="Run integration tests against staging environment",
                    timeout=900
                ),
                depends_on=["deploy_staging"],
                can_run_parallel=True,
                tags=["testing", "integration"]
            ))
            
            stages.append(StageDefinition(
                id="deploy_production",
                name="Deploy to Production",
                stage_type=StageType.AGENT_TASK,
                agent_config=AgentTaskConfig(
                    prompt="Deploy application to production environment with proper monitoring and rollback capabilities",
                    timeout=900
                ),
                depends_on=["integration_tests"],
                can_run_parallel=False,
                tags=["deployment", "production"]
            ))
        
        # Create the template pipeline
        template = PipelineDefinition(
            id=f"template_{template_key}",
            name=f"Template for {analysis.project_type} projects",
            description=f"Intelligent template for {analysis.project_type} projects using {', '.join(analysis.frameworks)}",
            stages=stages,
            max_parallel_stages=min(len(stages), 5),
            tags=["template", analysis.project_type] + analysis.frameworks
        )
        
        # Cache the template
        self.templates_cache[template_key] = template
        
        return template
    
    async def _customize_pipeline(self, 
                                template: PipelineDefinition,
                                analysis: ProjectAnalysis, 
                                pipeline_name: str) -> PipelineDefinition:
        """Customize a template pipeline for a specific project."""
        
        # Create a customized copy
        customized_stages = []
        for stage in template.stages:
            # Customize agent prompts with project-specific context
            if stage.agent_config:
                customized_prompt = f"{stage.agent_config.prompt}\n\nProject Context:\n"
                customized_prompt += f"- Project Type: {analysis.project_type}\n"
                customized_prompt += f"- Languages: {', '.join(analysis.languages)}\n"
                customized_prompt += f"- Frameworks: {', '.join(analysis.frameworks)}\n"
                customized_prompt += f"- Complexity: {analysis.complexity_score:.1f}/10\n"
                
                if analysis.has_database:
                    customized_prompt += "- Has Database: Yes\n"
                if analysis.has_frontend:
                    customized_prompt += "- Has Frontend: Yes\n" 
                if analysis.has_backend:
                    customized_prompt += "- Has Backend: Yes\n"
                
                new_agent_config = AgentTaskConfig(
                    prompt=customized_prompt,
                    timeout=stage.agent_config.timeout,
                    agent_type=stage.agent_config.agent_type,
                    org_id=stage.agent_config.org_id,
                    api_token=stage.agent_config.api_token,
                    context=stage.agent_config.context
                )
                
                customized_stage = StageDefinition(
                    id=stage.id,
                    name=stage.name,
                    stage_type=stage.stage_type,
                    description=stage.description,
                    depends_on=stage.depends_on,
                    can_run_parallel=stage.can_run_parallel,
                    continue_on_failure=stage.continue_on_failure,
                    agent_config=new_agent_config,
                    resource_limits=stage.resource_limits,
                    retry_attempts=stage.retry_attempts,
                    variables=stage.variables,
                    tags=stage.tags
                )
                customized_stages.append(customized_stage)
            else:
                customized_stages.append(stage)
        
        return PipelineDefinition(
            id=f"pipeline_{pipeline_name.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            name=pipeline_name,
            description=f"Intelligent CI/CD pipeline for {analysis.project_type} project",
            stages=customized_stages,
            global_variables={
                "project_type": analysis.project_type,
                "languages": analysis.languages,
                "frameworks": analysis.frameworks,
                "complexity_score": analysis.complexity_score
            },
            max_parallel_stages=template.max_parallel_stages,
            created_at=datetime.now(),
            tags=["intelligent", "self-evolving"] + template.tags
        )
    
    async def monitor_and_evolve(self, pipeline_id: str) -> Dict[str, Any]:
        """Monitor pipeline performance and suggest/apply evolution."""
        
        # Get recent executions for this pipeline
        all_executions = self.engine.get_all_pipeline_statuses()
        pipeline_executions = [
            exec for exec in all_executions.values() 
            if exec.pipeline_id == pipeline_id and exec.completed_at
        ]
        
        if not pipeline_executions:
            return {"status": "no_executions", "message": "No completed executions found"}
        
        # Analyze performance
        metrics = await self.evolver.analyze_performance(pipeline_executions)
        
        # Get pipeline definition
        pipeline_def = self.engine.pipeline_definitions.get(pipeline_id)
        if not pipeline_def:
            return {"status": "pipeline_not_found"}
        
        # Create mock project analysis for evolution (in real implementation, this would be persisted)
        mock_analysis = ProjectAnalysis(
            project_type=pipeline_def.global_variables.get("project_type", "application"),
            languages=pipeline_def.global_variables.get("languages", []),
            frameworks=pipeline_def.global_variables.get("frameworks", []),
            complexity_score=pipeline_def.global_variables.get("complexity_score", 5.0)
        )
        
        # Get optimization suggestions
        optimization_result = await self.evolver.suggest_optimizations(
            pipeline_def, metrics, mock_analysis
        )
        
        # Apply optimizations if auto-apply is enabled
        if self.config.auto_apply_optimizations and optimization_result["suggestions"]:
            applied_optimizations = await self._apply_optimizations(
                pipeline_def, optimization_result["suggestions"]
            )
            optimization_result["applied_optimizations"] = applied_optimizations
        
        return optimization_result
    
    async def _apply_optimizations(self, 
                                 pipeline: PipelineDefinition, 
                                 suggestions: List[Dict[str, Any]]) -> List[str]:
        """Apply optimization suggestions to a pipeline."""
        applied = []
        
        for suggestion in suggestions:
            if suggestion["action"] == "add_retry_logic":
                # Add retry logic to failing stages
                for stage in pipeline.stages:
                    if stage.retry_attempts == 0:
                        stage.retry_attempts = 3
                        stage.retry_delay = 10
                applied.append("Added retry logic to stages")
            
            elif suggestion["action"] == "optimize_stage_or_parallelize":
                # Find stages that can be parallelized
                stage_id = suggestion.get("stage_id")
                if stage_id:
                    for stage in pipeline.stages:
                        if stage.id == stage_id and not stage.can_run_parallel:
                            stage.can_run_parallel = True
                            applied.append(f"Enabled parallel execution for {stage_id}")
            
            elif suggestion["action"] == "add_docker_stage":
                # Add Docker containerization stage
                docker_stage = StageDefinition(
                    id="containerize",
                    name="Containerize Application",
                    stage_type=StageType.DOCKER_RUN,
                    docker_config={
                        "image": "node:alpine",
                        "command": "docker build -t app:latest ."
                    },
                    depends_on=["build"],
                    can_run_parallel=True,
                    tags=["docker", "containerization"]
                )
                pipeline.stages.append(docker_stage)
                applied.append("Added Docker containerization stage")
        
        # Re-register the updated pipeline
        if applied:
            self.engine.register_pipeline(pipeline)
            logger.info(f"Applied optimizations to pipeline {pipeline.id}: {applied}")
        
        return applied
    
    async def export_pipeline_config(self, pipeline_id: str, format: str = "yaml") -> str:
        """Export pipeline configuration for version control."""
        pipeline = self.engine.pipeline_definitions.get(pipeline_id)
        if not pipeline:
            raise ValueError(f"Pipeline {pipeline_id} not found")
        
        # Convert to serializable format
        pipeline_dict = {
            "id": pipeline.id,
            "name": pipeline.name,
            "description": pipeline.description,
            "version": pipeline.version,
            "stages": [
                {
                    "id": stage.id,
                    "name": stage.name,
                    "stage_type": stage.stage_type.value,
                    "depends_on": stage.depends_on,
                    "can_run_parallel": stage.can_run_parallel,
                    "agent_config": {
                        "prompt": stage.agent_config.prompt,
                        "timeout": stage.agent_config.timeout
                    } if stage.agent_config else None,
                    "tags": stage.tags
                }
                for stage in pipeline.stages
            ],
            "global_variables": pipeline.global_variables,
            "max_parallel_stages": pipeline.max_parallel_stages,
            "tags": pipeline.tags
        }
        
        if format == "yaml":
            return yaml.dump(pipeline_dict, default_flow_style=False, indent=2)
        elif format == "json":
            return json.dumps(pipeline_dict, indent=2)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    async def get_evolution_report(self, pipeline_id: Optional[str] = None) -> Dict[str, Any]:
        """Generate a comprehensive evolution report."""
        
        if pipeline_id:
            pipelines = [self.engine.pipeline_definitions.get(pipeline_id)]
            pipelines = [p for p in pipelines if p is not None]
        else:
            pipelines = list(self.engine.pipeline_definitions.values())
        
        report = {
            "generated_at": datetime.now().isoformat(),
            "total_pipelines": len(pipelines),
            "pipeline_reports": []
        }
        
        for pipeline in pipelines:
            # Get executions for this pipeline
            all_executions = self.engine.get_all_pipeline_statuses()
            pipeline_executions = [
                exec for exec in all_executions.values() 
                if exec.pipeline_id == pipeline.id and exec.completed_at
            ]
            
            if pipeline_executions:
                metrics = await self.evolver.analyze_performance(pipeline_executions)
                recent_metrics = [
                    m for m in metrics 
                    if m.timestamp > datetime.now() - timedelta(days=self.config.learning_window_days)
                ]
                
                avg_success_rate = (
                    sum(m.success_rate for m in recent_metrics) / len(recent_metrics)
                    if recent_metrics else 0.0
                )
                
                avg_duration = (
                    sum(m.average_duration for m in recent_metrics) / len(recent_metrics)
                    if recent_metrics else 0.0
                )
                
                pipeline_report = {
                    "pipeline_id": pipeline.id,
                    "name": pipeline.name,
                    "total_executions": len(pipeline_executions),
                    "recent_executions": len(recent_metrics),
                    "avg_success_rate": avg_success_rate,
                    "avg_duration_minutes": avg_duration / 60,
                    "project_type": pipeline.global_variables.get("project_type", "unknown"),
                    "complexity_score": pipeline.global_variables.get("complexity_score", 0),
                    "stage_count": len(pipeline.stages),
                    "evolution_status": "optimized" if avg_success_rate > 0.9 else "needs_attention"
                }
            else:
                pipeline_report = {
                    "pipeline_id": pipeline.id,
                    "name": pipeline.name,
                    "total_executions": 0,
                    "evolution_status": "no_data"
                }
            
            report["pipeline_reports"].append(pipeline_report)
        
        return report