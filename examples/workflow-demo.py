#!/usr/bin/env python3
"""
Codegen Visual Orchestration System - Complete Workflow Demo

This script demonstrates the full self-evolving CI/CD flow with project management
integration via API calls, CLI commands, and MCP servers.
"""

import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime
import argparse

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    from codegen.orchestration.self_evolving import SelfEvolvingFlowManager
    from codegen.orchestration.project_management import (
        ProjectManagementIntegration,
        MCPServerIntegration, 
        ProjectManagementFactory,
        ProjectPlatform,
        TaskPriority
    )
    from codegen.orchestration.engine import OrchestrationEngine
    from codegen.orchestration.schemas import PipelineDefinition, ExecutionStatus
    from codegen.orchestration.webhooks import WebhookManager
    from codegen.orchestration.api import create_app
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Please ensure the orchestration system is properly installed")
    sys.exit(1)


class WorkflowDemo:
    """Comprehensive demonstration of the visual orchestration system."""
    
    def __init__(self):
        self.flow_manager = SelfEvolvingFlowManager()
        self.pm_integration = None
        self.webhook_manager = WebhookManager()
        self.orchestration_engine = OrchestrationEngine()
        
    async def setup_integrations(self):
        """Set up project management and MCP integrations."""
        print("🔧 Setting up integrations...")
        
        # Configure MCP servers (mock configuration)
        mcp_servers = {
            "linear": {
                "url": "ws://localhost:8001",
                "token": "linear_token_here"
            },
            "github": {
                "url": "ws://localhost:8002", 
                "token": "github_token_here"
            }
        }
        
        mcp_integration = MCPServerIntegration(mcp_servers)
        
        # Connect to MCP servers
        for server_name in mcp_servers:
            connected = await mcp_integration.connect_to_server(server_name)
            if connected:
                print(f"  ✅ Connected to {server_name} MCP server")
            else:
                print(f"  ⚠️  Failed to connect to {server_name} MCP server (using mock)")
        
        # Set up project management integration
        self.pm_integration = ProjectManagementIntegration(mcp_integration)
        
        # Add Linear integration
        linear_config = ProjectManagementFactory.create_linear_integration(
            project_id="codegen-demo-team",
            api_token="linear_api_token",
            team_id="team_123"
        )
        self.pm_integration.add_integration("linear_main", linear_config)
        
        # Add GitHub integration
        github_config = ProjectManagementFactory.create_github_integration(
            repo_owner="codegen-sh",
            repo_name="codegen",
            github_token="github_token"
        )
        self.pm_integration.add_integration("github_issues", github_config)
        
        print("  ✅ Project management integrations configured")
        
        # Configure webhooks
        webhook_configs = [
            {
                "name": "slack_notifications",
                "url": "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK",
                "events": ["pipeline.started", "pipeline.completed", "pipeline.failed"],
                "headers": {"Content-Type": "application/json"}
            },
            {
                "name": "project_sync",
                "url": "https://api.linear.app/webhooks/codegen",
                "events": ["task.completed", "evolution.applied"],
                "secret": "webhook_secret_key"
            }
        ]
        
        for config in webhook_configs:
            self.webhook_manager.add_webhook(config)
        
        print("  ✅ Webhook endpoints configured")
        
    async def demonstrate_project_analysis(self, project_path: Path):
        """Demonstrate intelligent project analysis."""
        print(f"\n🔍 Analyzing project: {project_path}")
        
        # Use the project analyzer directly
        analyzer = self.flow_manager.analyzer
        analysis = await analyzer.analyze_project(project_path)
        
        print("\n📊 Analysis Results:")
        print(f"  Project Type: {analysis.get('project_type', 'Unknown')}")
        print(f"  Primary Language: {analysis.get('primary_language', 'Unknown')}")
        print(f"  Complexity Score: {analysis.get('complexity_score', 0)}/10")
        
        if analysis.get('languages'):
            print("\n  Languages detected:")
            for lang, count in analysis['languages'].items():
                print(f"    • {lang}: {count} files")
        
        if analysis.get('frameworks'):
            print("\n  Frameworks detected:")
            for framework in analysis['frameworks']:
                print(f"    • {framework}")
        
        print("\n  Recommended Pipeline Features:")
        features = analysis.get('pipeline_features', [])
        for feature in features:
            print(f"    • {feature}")
        
        return analysis
    
    async def demonstrate_intelligent_pipeline_creation(self, project_path: Path):
        """Demonstrate intelligent pipeline generation."""
        print(f"\n🛠️ Creating intelligent pipeline for: {project_path.name}")
        
        custom_requirements = {
            "security_level": "high",
            "deployment_targets": ["staging", "production"],
            "notification_channels": ["slack", "email"],
            "compliance_required": True
        }
        
        pipeline = await self.flow_manager.create_intelligent_pipeline(
            project_path, 
            f"{project_path.name}-cicd",
            custom_requirements
        )
        
        print(f"\n📋 Generated Pipeline: {pipeline.name}")
        print(f"  Total Stages: {len(pipeline.stages)}")
        print(f"  Parallel Execution: {'Yes' if pipeline.parallel_execution else 'No'}")
        
        for i, stage in enumerate(pipeline.stages, 1):
            print(f"\n  Stage {i}: {stage.name}")
            print(f"    Tasks: {len(stage.tasks)}")
            print(f"    Parallel: {'Yes' if stage.parallel else 'No'}")
            
            if stage.depends_on:
                print(f"    Dependencies: {', '.join(stage.depends_on)}")
            
            for task in stage.tasks:
                print(f"      • {task.name} ({task.agent_type})")
        
        return pipeline
    
    async def demonstrate_project_management_integration(self, pipeline: PipelineDefinition):
        """Demonstrate project management platform integration."""
        print(f"\n🔗 Creating project management tasks for: {pipeline.name}")
        
        # Create tasks in Linear
        linear_tasks = await self.pm_integration.create_pipeline_tasks(
            pipeline, "linear_main"
        )
        
        print(f"  ✅ Created {len(linear_tasks)} Linear tasks")
        for task in linear_tasks[:3]:  # Show first 3 tasks
            print(f"    • {task.title} ({task.id})")
            if task.platform_url:
                print(f"      URL: {task.platform_url}")
        
        # Create GitHub issues for failures tracking
        github_tasks = await self.pm_integration.create_pipeline_tasks(
            pipeline, "github_issues"
        )
        
        print(f"  ✅ Created {len(github_tasks)} GitHub tracking issues")
        
        return linear_tasks + github_tasks
    
    async def simulate_pipeline_execution(self, pipeline: PipelineDefinition):
        """Simulate pipeline execution with real-time updates."""
        print(f"\n▶️ Simulating execution of: {pipeline.name}")
        
        # Start pipeline execution
        await self.pm_integration.update_pipeline_progress(
            pipeline, ExecutionStatus.RUNNING, "linear_main"
        )
        
        await self.webhook_manager.send_webhook_async(
            "slack_notifications",
            {
                "text": f"🚀 Pipeline started: {pipeline.name}",
                "timestamp": datetime.now().isoformat()
            }
        )
        
        # Simulate stage execution
        total_stages = len(pipeline.stages)
        for i, stage in enumerate(pipeline.stages):
            print(f"  🏗️ Executing stage: {stage.name}")
            
            # Update progress
            completion = (i / total_stages) * 100
            await self.pm_integration.update_pipeline_progress(
                pipeline,
                ExecutionStatus.RUNNING,
                "linear_main", 
                stage_name=stage.name,
                completion_percentage=completion
            )
            
            # Simulate stage execution time
            await asyncio.sleep(1)  # Shortened for demo
            
            # Simulate occasional failure for demonstration
            if stage.name == "Security & Compliance" and pipeline.name.endswith("-cicd"):
                print(f"    ❌ Stage failed: Security scan detected vulnerabilities")
                
                # Create failure issue
                failed_task = stage.tasks[0] if stage.tasks else None
                if failed_task:
                    failure_issue = await self.pm_integration.create_issue_from_failure(
                        pipeline,
                        failed_task,
                        "High-severity security vulnerability detected in dependency 'example-lib@1.2.3'",
                        "linear_main"
                    )
                    
                    if failure_issue:
                        print(f"    📝 Created failure issue: {failure_issue.title}")
                
                await self.webhook_manager.send_webhook_async(
                    "slack_notifications",
                    {
                        "text": f"🚨 Pipeline failed: {pipeline.name} - Security vulnerabilities detected",
                        "timestamp": datetime.now().isoformat()
                    }
                )
                
                return ExecutionStatus.FAILED
            else:
                print(f"    ✅ Stage completed: {stage.name}")
        
        # Pipeline completed successfully
        await self.pm_integration.update_pipeline_progress(
            pipeline, ExecutionStatus.COMPLETED, "linear_main", completion_percentage=100
        )
        
        await self.webhook_manager.send_webhook_async(
            "slack_notifications",
            {
                "text": f"✅ Pipeline completed successfully: {pipeline.name}",
                "timestamp": datetime.now().isoformat()
            }
        )
        
        print(f"  ✅ Pipeline execution completed")
        return ExecutionStatus.COMPLETED
    
    async def demonstrate_evolution_and_learning(self, pipeline: PipelineDefinition):
        """Demonstrate self-evolving pipeline optimization."""
        print(f"\n🧠 Analyzing pipeline performance and evolving: {pipeline.name}")
        
        # Simulate multiple execution history for learning
        execution_history = [
            {"duration": 1800, "success": True, "stage_times": {"Build": 600, "Test": 800, "Deploy": 400}},
            {"duration": 2100, "success": True, "stage_times": {"Build": 650, "Test": 900, "Deploy": 550}},
            {"duration": 2400, "success": False, "failed_stage": "Test", "error": "Flaky test failure"},
            {"duration": 1900, "success": True, "stage_times": {"Build": 580, "Test": 850, "Deploy": 470}},
        ]
        
        # Run evolution analysis
        evolution_result = await self.flow_manager.monitor_and_evolve(pipeline.name)
        
        print("\n🔍 Evolution Analysis Results:")
        
        if "performance_metrics" in evolution_result:
            metrics = evolution_result["performance_metrics"]
            print(f"  Success Rate: {metrics.get('success_rate', 0):.1f}%")
            print(f"  Average Duration: {metrics.get('avg_duration', 0):.1f}s")
            print(f"  Resource Efficiency: {metrics.get('resource_efficiency', 0):.1f}%")
        
        suggestions = evolution_result.get("evolution_suggestions", [])
        if suggestions:
            print("\n💡 Optimization Suggestions:")
            for i, suggestion in enumerate(suggestions, 1):
                print(f"  {i}. {suggestion.get('type', 'Optimization')}")
                print(f"     {suggestion.get('description', 'No description')}")
                if suggestion.get('impact'):
                    print(f"     Expected impact: {suggestion['impact']}")
        
        # Demonstrate automatic optimization application
        if suggestions:
            print("\n🔧 Applying optimizations automatically...")
            
            # Send webhook notification about evolution
            await self.webhook_manager.send_webhook_async(
                "project_sync",
                {
                    "event": "evolution.applied",
                    "pipeline": pipeline.name,
                    "optimizations": len(suggestions),
                    "timestamp": datetime.now().isoformat()
                }
            )
            
            print("  ✅ Pipeline evolved successfully!")
            
            # Update project management with evolution notes
            await self.pm_integration.update_pipeline_progress(
                pipeline,
                ExecutionStatus.COMPLETED,
                "linear_main",
                completion_percentage=100
            )
    
    async def demonstrate_api_integration(self):
        """Demonstrate REST API integration capabilities."""
        print("\n🌐 API Integration Demonstration")
        
        # This would normally start a real FastAPI server
        app = create_app()
        
        print("  📡 REST API endpoints available:")
        print("    • GET /api/v1/pipelines - List all pipelines")
        print("    • POST /api/v1/pipelines - Create new pipeline")
        print("    • GET /api/v1/pipelines/{id}/status - Get pipeline status")
        print("    • POST /api/v1/pipelines/{id}/execute - Execute pipeline")
        print("    • WebSocket /ws - Real-time pipeline updates")
        
        print("\n  📊 Project Management API calls:")
        
        # Demonstrate sync with platforms
        sync_result = await self.pm_integration.sync_tasks_with_platform("linear_main")
        print(f"    • Linear sync: {sync_result.get('synced', False)}")
        
        # Get analytics
        analytics = await self.pm_integration.get_platform_analytics("linear_main")
        print(f"    • Analytics retrieved: {len(analytics)} metrics")
        print(f"      - Total tasks: {analytics.get('total_tasks', 0)}")
        print(f"      - Success rate: {analytics.get('pipeline_success_rate', 0):.1f}%")
        
    async def demonstrate_mcp_integration(self):
        """Demonstrate MCP server integration."""
        print("\n🔌 MCP Server Integration Demonstration")
        
        if not self.pm_integration or not self.pm_integration.mcp:
            print("  ⚠️  No MCP integration available (using mock)")
            return
        
        mcp = self.pm_integration.mcp
        
        # Demonstrate Linear MCP integration
        print("  📋 Linear MCP Operations:")
        linear_result = await mcp.call_tool(
            "linear",
            "create_issue",
            {
                "title": "Demo Issue from Codegen Orchestration",
                "description": "This issue was created via MCP server integration",
                "priority": "medium"
            }
        )
        
        if linear_result.get("success"):
            print(f"    ✅ Created Linear issue: {linear_result.get('issue_id')}")
        else:
            print(f"    ❌ Linear operation failed: {linear_result.get('error', 'Unknown error')}")
        
        # Demonstrate GitHub MCP integration  
        print("  🐙 GitHub MCP Operations:")
        github_result = await mcp.call_tool(
            "github",
            "create_issue",
            {
                "title": "Orchestration System Demo",
                "body": "Demo issue created by the self-evolving CI/CD system",
                "labels": ["enhancement", "automation"]
            }
        )
        
        if github_result.get("success"):
            print(f"    ✅ Created GitHub issue: #{github_result.get('issue_number')}")
        else:
            print(f"    ❌ GitHub operation failed: {github_result.get('error', 'Unknown error')}")
    
    async def run_complete_workflow(self, project_path: Path):
        """Run the complete workflow demonstration."""
        print("🚀 Starting Codegen Visual Orchestration Full Demo")
        print("=" * 60)
        
        try:
            # Step 1: Setup integrations
            await self.setup_integrations()
            
            # Step 2: Project analysis
            analysis = await self.demonstrate_project_analysis(project_path)
            
            # Step 3: Intelligent pipeline creation
            pipeline = await self.demonstrate_intelligent_pipeline_creation(project_path)
            
            # Step 4: Project management integration
            tasks = await self.demonstrate_project_management_integration(pipeline)
            
            # Step 5: Pipeline execution simulation
            execution_status = await self.simulate_pipeline_execution(pipeline)
            
            # Step 6: Evolution and learning (if execution succeeded)
            if execution_status == ExecutionStatus.COMPLETED:
                await self.demonstrate_evolution_and_learning(pipeline)
            
            # Step 7: API integration demonstration
            await self.demonstrate_api_integration()
            
            # Step 8: MCP integration demonstration
            await self.demonstrate_mcp_integration()
            
            print("\n" + "=" * 60)
            print("✅ Complete workflow demonstration finished successfully!")
            print("\nNext steps:")
            print("  • Run 'codegen orchestrate serve' to start the web interface")
            print("  • Use 'codegen orchestrate project setup' to configure real integrations")
            print("  • Deploy with 'python deploy-orchestration.py' for production")
            
        except Exception as e:
            print(f"\n❌ Demo failed: {e}")
            import traceback
            traceback.print_exc()


async def main():
    """Main entry point for the workflow demonstration."""
    parser = argparse.ArgumentParser(description="Codegen Orchestration Workflow Demo")
    parser.add_argument(
        "project_path",
        nargs="?",
        default=".",
        help="Path to project for analysis (defaults to current directory)"
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Run a quick demo with minimal output"
    )
    
    args = parser.parse_args()
    project_path = Path(args.project_path).resolve()
    
    if not project_path.exists():
        print(f"❌ Project path does not exist: {project_path}")
        sys.exit(1)
    
    demo = WorkflowDemo()
    
    if args.quick:
        print("🏃 Running quick demo...")
        await demo.setup_integrations()
        analysis = await demo.demonstrate_project_analysis(project_path)
        pipeline = await demo.demonstrate_intelligent_pipeline_creation(project_path)
        print("✅ Quick demo completed!")
    else:
        await demo.run_complete_workflow(project_path)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Demo interrupted by user")
    except Exception as e:
        print(f"\n💥 Demo crashed: {e}")
        sys.exit(1)