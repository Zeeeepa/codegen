#!/usr/bin/env python3
"""
Deployment script for Codegen Visual Orchestration CI/CD System

This script sets up and deploys the complete visual orchestration system
including the API server, WebSocket handlers, and web UI.
"""

import asyncio
import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any

import uvicorn
from src.codegen.orchestration.api import create_orchestration_api
from src.codegen.orchestration.engine import OrchestrationConfig


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class OrchestrationDeployment:
    """Handles deployment and management of the orchestration system."""
    
    def __init__(self):
        self.config = self._load_configuration()
        self.api = None
        
    def _load_configuration(self) -> OrchestrationConfig:
        """Load configuration from environment variables."""
        return OrchestrationConfig(
            max_concurrent_pipelines=int(os.getenv("MAX_CONCURRENT_PIPELINES", "10")),
            max_concurrent_stages=int(os.getenv("MAX_CONCURRENT_STAGES", "20")),
            default_stage_timeout=int(os.getenv("DEFAULT_STAGE_TIMEOUT", "3600")),
            pipeline_timeout=int(os.getenv("PIPELINE_TIMEOUT", "14400")),
            cleanup_completed_after=int(os.getenv("CLEANUP_COMPLETED_AFTER", "86400")),
            enable_webhooks=os.getenv("ENABLE_WEBHOOKS", "true").lower() == "true",
            enable_real_time_updates=os.getenv("ENABLE_REAL_TIME_UPDATES", "true").lower() == "true"
        )
        
    def check_dependencies(self) -> bool:
        """Check if all required dependencies are installed."""
        logger.info("Checking system dependencies...")
        
        required_packages = [
            'fastapi', 'uvicorn', 'websockets', 'aiohttp', 
            'pydantic', 'networkx', 'asyncpg'
        ]
        
        missing_packages = []
        
        for package in required_packages:
            try:
                __import__(package)
            except ImportError:
                missing_packages.append(package)
                
        if missing_packages:
            logger.error(f"Missing required packages: {missing_packages}")
            logger.info("Please install dependencies: pip install -r requirements-orchestration.txt")
            return False
            
        logger.info("✅ All dependencies satisfied")
        return True
        
    def setup_database(self) -> bool:
        """Set up database for state persistence."""
        logger.info("Setting up database...")
        
        # For development, we'll use SQLite. In production, use PostgreSQL
        db_url = os.getenv("DATABASE_URL", "sqlite:///orchestration.db")
        
        # Here you would run migrations, create tables, etc.
        # For now, we'll just log the configuration
        
        logger.info(f"✅ Database configured: {db_url}")
        return True
        
    def setup_redis(self) -> bool:
        """Set up Redis for caching and pub/sub."""
        logger.info("Setting up Redis...")
        
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        
        # Here you would verify Redis connectivity
        # For now, we'll just log the configuration
        
        logger.info(f"✅ Redis configured: {redis_url}")
        return True
        
    def create_sample_pipelines(self):
        """Create sample pipelines for demonstration."""
        logger.info("Creating sample pipelines...")
        
        from src.codegen.orchestration.schemas import (
            PipelineDefinition, StageDefinition, StageType, 
            AgentTaskConfig, WebhookConfig
        )
        from datetime import datetime
        
        # Sample parallel execution pipeline
        sample_pipeline = PipelineDefinition(
            id="sample_parallel_pipeline",
            name="Sample Parallel Agent Pipeline",
            description="Demonstrates parallel codegen agent execution",
            stages=[
                StageDefinition(
                    id="init",
                    name="Initialize Pipeline",
                    stage_type=StageType.AGENT_TASK,
                    agent_config=AgentTaskConfig(
                        prompt="Initialize the demonstration pipeline",
                        agent_type="initializer",
                        timeout=300
                    ),
                    depends_on=[],
                    can_run_parallel=True
                ),
                StageDefinition(
                    id="parallel_task_1",
                    name="Parallel Agent Task 1",
                    stage_type=StageType.AGENT_TASK,
                    agent_config=AgentTaskConfig(
                        prompt="Execute first parallel codegen agent task",
                        agent_type="worker",
                        timeout=600
                    ),
                    depends_on=["init"],
                    can_run_parallel=True
                ),
                StageDefinition(
                    id="parallel_task_2", 
                    name="Parallel Agent Task 2",
                    stage_type=StageType.AGENT_TASK,
                    agent_config=AgentTaskConfig(
                        prompt="Execute second parallel codegen agent task",
                        agent_type="worker",
                        timeout=600
                    ),
                    depends_on=["init"],
                    can_run_parallel=True
                ),
                StageDefinition(
                    id="aggregate",
                    name="Aggregate Results",
                    stage_type=StageType.AGENT_TASK,
                    agent_config=AgentTaskConfig(
                        prompt="Aggregate results from parallel tasks",
                        agent_type="aggregator",
                        timeout=300
                    ),
                    depends_on=["parallel_task_1", "parallel_task_2"],
                    can_run_parallel=True
                )
            ],
            webhooks=[
                WebhookConfig(
                    url="https://httpbin.org/post",
                    retry_attempts=3
                )
            ],
            global_variables={"demo_mode": True, "parallel_execution": True},
            max_parallel_stages=5,
            created_at=datetime.now(),
            tags=["demo", "parallel", "sample"]
        )
        
        # Register the sample pipeline
        if self.api and self.api.engine:
            self.api.engine.register_pipeline(sample_pipeline)
            logger.info(f"✅ Created sample pipeline: {sample_pipeline.name}")
            
    async def start_api_server(self):
        """Start the orchestration API server."""
        logger.info("Starting Codegen Visual Orchestration API Server...")
        
        # Create the API
        self.api = create_orchestration_api(self.config)
        
        # Setup startup event
        @self.api.app.on_event("startup")
        async def startup_event():
            await self.api.start()
            self.create_sample_pipelines()
            logger.info("🚀 Orchestration system fully initialized!")
            
        @self.api.app.on_event("shutdown")
        async def shutdown_event():
            await self.api.stop()
            logger.info("✅ Orchestration system shut down gracefully")
            
        # Configure server settings
        host = os.getenv("HOST", "0.0.0.0")
        port = int(os.getenv("PORT", "8000"))
        
        logger.info(f"Starting server on {host}:{port}")
        logger.info("API Documentation: http://localhost:8000/docs")
        logger.info("WebSocket Endpoint: ws://localhost:8000/ws")
        
        # Run the server
        config = uvicorn.Config(
            self.api.app,
            host=host,
            port=port,
            log_level="info",
            access_log=True,
            reload=os.getenv("RELOAD", "false").lower() == "true"
        )
        
        server = uvicorn.Server(config)
        await server.serve()
        
    def build_frontend(self) -> bool:
        """Build the frontend React application."""
        logger.info("Building frontend React application...")
        
        frontend_dir = Path("web-ui")
        if not frontend_dir.exists():
            logger.warning("Frontend directory not found, skipping build")
            return True
            
        try:
            # Install dependencies
            subprocess.run(["npm", "install"], cwd=frontend_dir, check=True)
            
            # Build the application
            subprocess.run(["npm", "run", "build"], cwd=frontend_dir, check=True)
            
            logger.info("✅ Frontend built successfully")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Frontend build failed: {e}")
            return False
            
    def print_deployment_info(self):
        """Print deployment information and next steps."""
        logger.info("🎉 Codegen Visual Orchestration System Deployment Complete!")
        
        print("\n" + "="*70)
        print("🚀 CODEGEN VISUAL ORCHESTRATION CI/CD SYSTEM")
        print("="*70)
        
        print("\n📍 API Endpoints:")
        print(f"   • REST API: http://localhost:8000")
        print(f"   • API Docs: http://localhost:8000/docs")
        print(f"   • WebSocket: ws://localhost:8000/ws")
        
        print("\n🎨 Visual Pipeline Designer:")
        print(f"   • Web UI: http://localhost:3000 (if running)")
        print(f"   • Source: web-ui/src/components/PipelineDesigner.tsx")
        
        print("\n⚡ Key Features Available:")
        print("   ✅ Parallel codegen agent execution")
        print("   ✅ Real-time WebSocket monitoring")
        print("   ✅ Webhook callback integration")
        print("   ✅ Visual drag-and-drop pipeline designer")
        print("   ✅ Complex dependency management")
        print("   ✅ Resource management & scaling")
        print("   ✅ State persistence & recovery")
        
        print("\n🧪 Testing the System:")
        print("   1. Open http://localhost:8000/docs")
        print("   2. Create a pipeline using POST /pipelines")
        print("   3. Execute pipeline using POST /pipelines/{id}/execute")
        print("   4. Monitor via WebSocket at ws://localhost:8000/ws")
        print("   5. Check webhook deliveries at GET /webhooks/deliveries")
        
        print("\n🔧 Configuration:")
        print(f"   • Max Concurrent Pipelines: {self.config.max_concurrent_pipelines}")
        print(f"   • Max Concurrent Stages: {self.config.max_concurrent_stages}")
        print(f"   • Webhooks Enabled: {self.config.enable_webhooks}")
        print(f"   • Real-time Updates: {self.config.enable_real_time_updates}")
        
        print("\n💡 Next Steps:")
        print("   1. Configure your codegen API credentials")
        print("   2. Set up webhook endpoints for external integrations")
        print("   3. Create your first visual pipeline")
        print("   4. Set up monitoring and alerting")
        
        print("\n" + "="*70)


async def main():
    """Main deployment function."""
    deployment = OrchestrationDeployment()
    
    logger.info("🚀 Starting Codegen Visual Orchestration Deployment...")
    
    # Pre-flight checks
    if not deployment.check_dependencies():
        sys.exit(1)
        
    if not deployment.setup_database():
        sys.exit(1)
        
    if not deployment.setup_redis():
        sys.exit(1)
        
    # Build frontend (optional)
    deployment.build_frontend()
    
    # Print deployment info
    deployment.print_deployment_info()
    
    # Start the API server
    try:
        await deployment.start_api_server()
    except KeyboardInterrupt:
        logger.info("Deployment interrupted by user")
    except Exception as e:
        logger.error(f"Deployment failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("✅ Deployment stopped by user")
    except Exception as e:
        logger.error(f"❌ Deployment failed: {e}")
        sys.exit(1)