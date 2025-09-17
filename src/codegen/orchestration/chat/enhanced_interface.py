"""
Enhanced Chat Interface for CI/CD Orchestration

This module provides an enhanced chat interface that integrates with all
ecosystem components through the comprehensive orchestration system.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, AsyncGenerator
from dataclasses import dataclass
from enum import Enum

from codegen.orchestration.enhanced_manager import EnhancedCICDOrchestrator, DeploymentRequest, DeploymentStatus
from codegen.orchestration.chat.interface import ChatInterface, MessageType, IntentType, ParsedIntent

logger = logging.getLogger(__name__)

class EnhancedIntentType(Enum):
    """Enhanced intent types for CI/CD operations."""
    DEPLOY_PROJECT = "deploy_project"
    DEPLOYMENT_STATUS = "deployment_status"
    CANCEL_DEPLOYMENT = "cancel_deployment"
    LIST_DEPLOYMENTS = "list_deployments"
    SANDBOX_MANAGEMENT = "sandbox_management"
    SYSTEM_METRICS = "system_metrics"
    PROXY_STATUS = "proxy_status"
    HEALTH_CHECK = "health_check"
    
    # Existing intents from base class
    AGENT_CREATE = "agent_create"
    AGENT_STATUS = "agent_status"
    AGENT_LIST = "agent_list"
    CODE_ANALYSIS = "code_analysis"
    CHAT_CONVERSATION = "chat_conversation"
    SYSTEM_STATUS = "system_status"
    HELP = "help"
    UNKNOWN = "unknown"

class EnhancedChatInterface:
    """
    Enhanced Chat Interface for Comprehensive CI/CD Orchestration.
    
    This interface provides natural language access to the complete CI/CD
    ecosystem including deployment management, monitoring, and system control.
    """
    
    def __init__(self, orchestrator: EnhancedCICDOrchestrator):
        """Initialize enhanced chat interface."""
        self.orchestrator = orchestrator
        self._initialized = False
        
        # Enhanced intent patterns
        self._enhanced_intent_patterns = {
            EnhancedIntentType.DEPLOY_PROJECT: [
                "deploy", "deployment", "deploy project", "start deployment",
                "create deployment", "launch", "release"
            ],
            EnhancedIntentType.DEPLOYMENT_STATUS: [
                "deployment status", "check deployment", "deployment progress",
                "how is deployment", "deployment update"
            ],
            EnhancedIntentType.CANCEL_DEPLOYMENT: [
                "cancel deployment", "stop deployment", "abort deployment",
                "terminate deployment", "halt deployment"
            ],
            EnhancedIntentType.LIST_DEPLOYMENTS: [
                "list deployments", "show deployments", "active deployments",
                "deployment list", "my deployments"
            ],
            EnhancedIntentType.SANDBOX_MANAGEMENT: [
                "sandbox", "container", "vm", "environment",
                "sandbox status", "create sandbox"
            ],
            EnhancedIntentType.SYSTEM_METRICS: [
                "metrics", "performance", "system metrics", "statistics",
                "monitoring", "observability"
            ],
            EnhancedIntentType.PROXY_STATUS: [
                "proxy", "proxy status", "proxy pool", "proxy health",
                "rotation", "proxy metrics"
            ],
            EnhancedIntentType.HEALTH_CHECK: [
                "health", "health check", "system health", "service health",
                "status check", "diagnostics"
            ]
        }
        
        logger.info("EnhancedChatInterface initialized")
    
    async def initialize(self) -> None:
        """Initialize the enhanced chat interface."""
        if self._initialized:
            return
        
        # Ensure orchestrator is initialized
        await self.orchestrator.initialize()
        
        self._initialized = True
        logger.info("Enhanced chat interface initialized")
    
    async def process_message(
        self,
        message: str,
        user_id: str,
        session_id: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """
        Process a user message and yield response chunks.
        
        Args:
            message: User message text
            user_id: User identifier
            session_id: Optional session identifier
            
        Yields:
            Response text chunks
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            # Parse enhanced intent
            intent = await self._parse_enhanced_intent(message)
            
            # Route to appropriate handler
            async for chunk in self._handle_intent(intent, user_id, session_id):
                yield chunk
                
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            yield f"❌ **Error**: {str(e)}\n\nI encountered an issue processing your request. Please try again or contact support if the problem persists."
    
    async def get_enhanced_help_text(self) -> str:
        """Get enhanced help text for all available commands."""
        return """
🚀 **Enhanced CI/CD Orchestration Chat Interface**

I can help you with comprehensive CI/CD operations across the entire ecosystem:

## 🚀 **Deployment Operations**
- `deploy [project-name] from [repo-url]` - Deploy a project through the full CI/CD pipeline
- `deployment status [deployment-id]` - Check deployment progress and status
- `cancel deployment [deployment-id]` - Cancel an active deployment
- `list deployments` - Show all active deployments
- `deployment logs [deployment-id]` - View deployment logs

## 🔒 **Sandbox Management**
- `create sandbox for [project]` - Create a new Grainchain sandbox
- `sandbox status [sandbox-id]` - Check sandbox status
- `destroy sandbox [sandbox-id]` - Clean up sandbox resources
- `list sandboxes` - Show all active sandboxes

## 📊 **Monitoring & Metrics**
- `system metrics` - View comprehensive system metrics
- `proxy status` - Check proxy pool health and rotation
- `health check` - Perform system-wide health diagnostics
- `service status` - Check status of all ecosystem services

## 🤖 **AI Services**
- `analyze code in [repo]` - Use Z.AI for code analysis
- `generate code for [task]` - AI-powered code generation
- `validate deployment` - Use RepoMaster for validation

## 🖥️ **UI Automation**
- `automate ui task [description]` - Use NeuralAgent + MIRIX for UI tasks
- `click element [description]` - Automated UI interaction
- `capture screen` - Take screenshots for analysis

## 🧠 **Advanced Operations**
- `evolve solution for [problem]` - Use R-Zero + Elysia + Neosgenesis
- `optimize workflow` - Intelligent workflow optimization
- `learn from deployment` - Adaptive system learning

## 📈 **Examples**
- "Deploy my-app from https://github.com/user/my-app"
- "What's the status of deployment dep_abc123?"
- "Create a sandbox for testing the new API"
- "Show me system metrics and proxy health"
- "Analyze the code quality in my repository"
- "Automate the login flow testing"

## 🔧 **System Commands**
- `help` - Show this help message
- `system status` - Overall system health
- `reset session` - Clear current session
- `export logs` - Export system logs

Just describe what you want to do naturally - I'll understand and coordinate across all services! 🎯
        """
    
    # Private methods
    
    async def _parse_enhanced_intent(self, message: str) -> ParsedIntent:
        """Parse message to determine enhanced intent."""
        message_lower = message.lower()
        
        # Check enhanced intents first
        best_intent = EnhancedIntentType.UNKNOWN
        best_confidence = 0.0
        
        for intent_type, patterns in self._enhanced_intent_patterns.items():
            for pattern in patterns:
                if pattern in message_lower:
                    confidence = len(pattern) / len(message_lower)
                    if confidence > best_confidence:
                        best_intent = intent_type
                        best_confidence = confidence
        
        # Extract parameters based on intent
        parameters = await self._extract_enhanced_parameters(message, best_intent)
        
        return ParsedIntent(
            intent_type=best_intent,
            confidence=best_confidence,
            parameters=parameters,
            raw_message=message
        )
    
    async def _extract_enhanced_parameters(self, message: str, intent: EnhancedIntentType) -> Dict[str, Any]:
        """Extract parameters from message based on enhanced intent."""
        parameters = {}
        message_lower = message.lower()
        words = message.split()
        
        if intent == EnhancedIntentType.DEPLOY_PROJECT:
            # Extract project name and repository URL
            for i, word in enumerate(words):
                if word.lower() in ["deploy", "deployment"]:
                    if i + 1 < len(words):
                        parameters["project_name"] = words[i + 1]
                elif word.lower() in ["from", "repo", "repository"]:
                    if i + 1 < len(words):
                        parameters["repository_url"] = words[i + 1]
                elif word.startswith("http"):
                    parameters["repository_url"] = word
            
            # Extract environment
            if "staging" in message_lower:
                parameters["environment"] = "staging"
            elif "production" in message_lower:
                parameters["environment"] = "production"
            else:
                parameters["environment"] = "development"
        
        elif intent == EnhancedIntentType.DEPLOYMENT_STATUS:
            # Extract deployment ID
            for word in words:
                if word.startswith("dep_") or len(word) > 6 and word.isalnum():
                    parameters["deployment_id"] = word
                    break
        
        elif intent == EnhancedIntentType.CANCEL_DEPLOYMENT:
            # Extract deployment ID
            for word in words:
                if word.startswith("dep_") or len(word) > 6 and word.isalnum():
                    parameters["deployment_id"] = word
                    break
        
        elif intent == EnhancedIntentType.SANDBOX_MANAGEMENT:
            # Extract sandbox ID or action
            for word in words:
                if word.startswith("sandbox_") or word.startswith("sb_"):
                    parameters["sandbox_id"] = word
                    break
            
            if "create" in message_lower:
                parameters["action"] = "create"
            elif "destroy" in message_lower or "delete" in message_lower:
                parameters["action"] = "destroy"
            elif "status" in message_lower:
                parameters["action"] = "status"
            else:
                parameters["action"] = "list"
        
        return parameters
    
    async def _handle_intent(
        self,
        intent: ParsedIntent,
        user_id: str,
        session_id: Optional[str]
    ) -> AsyncGenerator[str, None]:
        """Handle parsed intent and generate response."""
        
        if intent.intent_type == EnhancedIntentType.DEPLOY_PROJECT:
            async for chunk in self._handle_deploy_project(intent, user_id, session_id):
                yield chunk
        
        elif intent.intent_type == EnhancedIntentType.DEPLOYMENT_STATUS:
            async for chunk in self._handle_deployment_status(intent):
                yield chunk
        
        elif intent.intent_type == EnhancedIntentType.CANCEL_DEPLOYMENT:
            async for chunk in self._handle_cancel_deployment(intent):
                yield chunk
        
        elif intent.intent_type == EnhancedIntentType.LIST_DEPLOYMENTS:
            async for chunk in self._handle_list_deployments():
                yield chunk
        
        elif intent.intent_type == EnhancedIntentType.SANDBOX_MANAGEMENT:
            async for chunk in self._handle_sandbox_management(intent):
                yield chunk
        
        elif intent.intent_type == EnhancedIntentType.SYSTEM_METRICS:
            async for chunk in self._handle_system_metrics():
                yield chunk
        
        elif intent.intent_type == EnhancedIntentType.PROXY_STATUS:
            async for chunk in self._handle_proxy_status():
                yield chunk
        
        elif intent.intent_type == EnhancedIntentType.HEALTH_CHECK:
            async for chunk in self._handle_health_check():
                yield chunk
        
        elif intent.intent_type == EnhancedIntentType.HELP:
            yield await self.get_enhanced_help_text()
        
        else:
            # Fallback to basic responses
            yield f"🤔 I understand you want to: **{intent.raw_message}**\n\n"
            yield "I'm still learning how to handle this request. "
            yield "Try being more specific or use `help` to see available commands."
    
    async def _handle_deploy_project(
        self,
        intent: ParsedIntent,
        user_id: str,
        session_id: Optional[str]
    ) -> AsyncGenerator[str, None]:
        """Handle project deployment request."""
        parameters = intent.parameters
        
        if not parameters.get("project_name"):
            yield "❌ **Missing Project Name**\n\n"
            yield "Please specify a project name. Example: `deploy my-app from https://github.com/user/repo`"
            return
        
        if not parameters.get("repository_url"):
            yield "❌ **Missing Repository URL**\n\n"
            yield "Please specify a repository URL. Example: `deploy my-app from https://github.com/user/repo`"
            return
        
        # Create deployment request
        deployment_request = DeploymentRequest(
            project_name=parameters["project_name"],
            repository_url=parameters["repository_url"],
            environment=parameters.get("environment", "development"),
            user_id=user_id,
            session_id=session_id or f"chat_{user_id}_{datetime.utcnow().timestamp()}"
        )
        
        yield f"🚀 **Starting Deployment: {deployment_request.project_name}**\n\n"
        yield f"**Repository:** {deployment_request.repository_url}\n"
        yield f"**Environment:** {deployment_request.environment}\n"
        yield f"**Deployment ID:** `{deployment_request.deployment_id}`\n\n"
        yield "📊 **Progress:**\n"
        
        # Stream deployment progress
        async for status in self.orchestrator.deploy_project(deployment_request):
            progress_bar = "█" * int(status.progress_percentage / 10) + "░" * (10 - int(status.progress_percentage / 10))
            
            yield f"\n🔄 **{status.phase.value.replace('_', ' ').title()}** "
            yield f"[{progress_bar}] {status.progress_percentage:.1f}%\n"
            
            if status.logs:
                latest_log = status.logs[-1]
                yield f"   💬 {latest_log}\n"
            
            if status.phase.value == "completed":
                yield f"\n✅ **Deployment Completed Successfully!**\n\n"
                yield f"**Sandbox ID:** `{status.sandbox_id}`\n"
                if status.snapshot_id:
                    yield f"**Snapshot ID:** `{status.snapshot_id}`\n"
                yield f"**Duration:** {(status.completed_at - status.started_at).total_seconds():.1f}s\n"
                break
            elif status.phase.value == "failed":
                yield f"\n❌ **Deployment Failed**\n\n"
                if status.error_message:
                    yield f"**Error:** {status.error_message}\n"
                yield f"Use `deployment logs {deployment_request.deployment_id}` for detailed logs."
                break
    
    async def _handle_deployment_status(self, intent: ParsedIntent) -> AsyncGenerator[str, None]:
        """Handle deployment status request."""
        deployment_id = intent.parameters.get("deployment_id")
        
        if not deployment_id:
            yield "❌ **Missing Deployment ID**\n\n"
            yield "Please specify a deployment ID. Example: `deployment status dep_abc123`"
            return
        
        status = await self.orchestrator.get_deployment_status(deployment_id)
        
        if not status:
            yield f"❌ **Deployment Not Found**\n\n"
            yield f"No deployment found with ID: `{deployment_id}`\n"
            yield "Use `list deployments` to see active deployments."
            return
        
        # Format status response
        yield f"📊 **Deployment Status: {deployment_id}**\n\n"
        yield f"**Phase:** {status.phase.value.replace('_', ' ').title()}\n"
        yield f"**Progress:** {status.progress_percentage:.1f}%\n"
        
        if status.sandbox_id:
            yield f"**Sandbox:** `{status.sandbox_id}`\n"
        
        if status.current_service:
            yield f"**Current Service:** {status.current_service}\n"
        
        if status.started_at:
            elapsed = (datetime.utcnow() - status.started_at).total_seconds()
            yield f"**Elapsed Time:** {elapsed:.1f}s\n"
        
        if status.error_message:
            yield f"\n❌ **Error:** {status.error_message}\n"
        
        # Show recent logs
        if status.logs:
            yield f"\n📝 **Recent Logs:**\n"
            for log in status.logs[-3:]:  # Show last 3 logs
                yield f"   • {log}\n"
    
    async def _handle_cancel_deployment(self, intent: ParsedIntent) -> AsyncGenerator[str, None]:
        """Handle deployment cancellation request."""
        deployment_id = intent.parameters.get("deployment_id")
        
        if not deployment_id:
            yield "❌ **Missing Deployment ID**\n\n"
            yield "Please specify a deployment ID. Example: `cancel deployment dep_abc123`"
            return
        
        success = await self.orchestrator.cancel_deployment(deployment_id)
        
        if success:
            yield f"✅ **Deployment Cancelled**\n\n"
            yield f"Successfully cancelled deployment: `{deployment_id}`\n"
            yield "Resources are being cleaned up..."
        else:
            yield f"❌ **Cancellation Failed**\n\n"
            yield f"Could not cancel deployment: `{deployment_id}`\n"
            yield "The deployment may have already completed or failed."
    
    async def _handle_list_deployments(self) -> AsyncGenerator[str, None]:
        """Handle list deployments request."""
        deployments = await self.orchestrator.list_active_deployments()
        
        if not deployments:
            yield "📋 **No Active Deployments**\n\n"
            yield "There are currently no active deployments.\n"
            yield "Use `deploy [project] from [repo]` to start a new deployment."
            return
        
        yield f"📋 **Active Deployments ({len(deployments)})**\n\n"
        
        for deployment in deployments:
            status_emoji = {
                "initializing": "🔄",
                "sandboxing": "🔒",
                "environment_setup": "⚙️",
                "dependency_installation": "📦",
                "application_deployment": "🚀",
                "context_validation": "✅",
                "monitoring_setup": "📊",
                "completed": "✅",
                "failed": "❌"
            }.get(deployment.phase.value, "🔄")
            
            yield f"{status_emoji} **{deployment.deployment_id}**\n"
            yield f"   Phase: {deployment.phase.value.replace('_', ' ').title()}\n"
            yield f"   Progress: {deployment.progress_percentage:.1f}%\n"
            
            if deployment.started_at:
                elapsed = (datetime.utcnow() - deployment.started_at).total_seconds()
                yield f"   Elapsed: {elapsed:.1f}s\n"
            
            yield "\n"
    
    async def _handle_sandbox_management(self, intent: ParsedIntent) -> AsyncGenerator[str, None]:
        """Handle sandbox management request."""
        action = intent.parameters.get("action", "list")
        sandbox_id = intent.parameters.get("sandbox_id")
        
        if action == "list":
            # List all sandboxes
            sandboxes = await self.orchestrator.grainchain_manager.list_sandboxes()
            
            if not sandboxes:
                yield "📋 **No Active Sandboxes**\n\n"
                yield "There are currently no active sandboxes."
                return
            
            yield f"📋 **Active Sandboxes ({len(sandboxes)})**\n\n"
            
            for sandbox in sandboxes:
                status_emoji = {
                    "creating": "🔄",
                    "ready": "✅",
                    "running": "🚀",
                    "error": "❌"
                }.get(sandbox["status"], "🔄")
                
                yield f"{status_emoji} **{sandbox['sandbox_id']}**\n"
                yield f"   Project: {sandbox['project_name']}\n"
                yield f"   Status: {sandbox['status'].title()}\n"
                yield f"   IP: {sandbox.get('ip_address', 'N/A')}\n\n"
        
        elif action == "status":
            if not sandbox_id:
                yield "❌ **Missing Sandbox ID**\n\n"
                yield "Please specify a sandbox ID. Example: `sandbox status sandbox_abc123`"
                return
            
            status = await self.orchestrator.grainchain_manager.get_sandbox_status(sandbox_id)
            
            if not status:
                yield f"❌ **Sandbox Not Found**\n\n"
                yield f"No sandbox found with ID: `{sandbox_id}`"
                return
            
            yield f"📊 **Sandbox Status: {sandbox_id}**\n\n"
            yield f"**Project:** {status['project_name']}\n"
            yield f"**Status:** {status['status'].title()}\n"
            yield f"**IP Address:** {status.get('ip_address', 'N/A')}\n"
            yield f"**Container ID:** {status.get('container_id', 'N/A')}\n"
            yield f"**Created:** {status['created_at']}\n"
            
            if status.get('snapshots'):
                yield f"**Snapshots:** {len(status['snapshots'])}\n"
    
    async def _handle_system_metrics(self) -> AsyncGenerator[str, None]:
        """Handle system metrics request."""
        metrics = await self.orchestrator.get_system_metrics()
        
        yield "📊 **System Metrics**\n\n"
        
        # Core metrics
        yield f"**🚀 Active Deployments:** {metrics.get('active_deployments', 0)}\n"
        yield f"**📈 Total Deployments:** {metrics.get('total_deployments', 0)}\n"
        yield f"**⚙️ Active Operations:** {metrics.get('active_operations', 0)}\n"
        yield f"**📋 Total Operations:** {metrics.get('total_operations', 0)}\n\n"
        
        # Service status
        yield "**🔧 Service Status:**\n"
        zai_status = metrics.get('zai_client_status', {})
        yield f"   • Z.AI: {zai_status.get('status', 'Unknown')}\n"
        
        grainchain_status = metrics.get('grainchain_status', {})
        yield f"   • Grainchain: {grainchain_status.get('status', 'Unknown')}\n"
        
        roma_status = metrics.get('roma_status', {})
        yield f"   • ROMA: {roma_status.get('status', 'Unknown')}\n"
        
        # Proxy status
        proxy_status = metrics.get('proxy_pool_status', {})
        if proxy_status:
            yield f"\n**🔄 Proxy Pool:**\n"
            yield f"   • Total Proxies: {proxy_status.get('total_proxies', 0)}\n"
            yield f"   • Healthy Proxies: {proxy_status.get('healthy_proxies', 0)}\n"
            yield f"   • Pool Health: {proxy_status.get('pool_health_score', 0):.1f}%\n"
        
        # Storage status
        storage_status = metrics.get('storage_status', {})
        if storage_status:
            yield f"\n**💾 Storage:**\n"
            yield f"   • Total Reads: {storage_status.get('total_reads', 0)}\n"
            yield f"   • Total Writes: {storage_status.get('total_writes', 0)}\n"
            yield f"   • Cache Hit Rate: {storage_status.get('cache_hit_rate', 0):.1f}%\n"
    
    async def _handle_proxy_status(self) -> AsyncGenerator[str, None]:
        """Handle proxy status request."""
        proxy_status = await self.orchestrator.proxy_manager.get_pool_status()
        
        yield "🔄 **Proxy Pool Status**\n\n"
        yield f"**Total Proxies:** {proxy_status['total_proxies']}\n"
        yield f"**Healthy Proxies:** {proxy_status['healthy_proxies']}\n"
        yield f"**Available Proxies:** {proxy_status['available_proxies']}\n"
        yield f"**Pool Health Score:** {proxy_status['pool_health_score']:.1f}%\n"
        yield f"**Rotation Strategy:** {proxy_status['rotation_strategy']}\n"
        yield f"**Total Requests:** {proxy_status['total_requests']}\n"
        yield f"**Failure Rate:** {proxy_status['failure_rate']:.1f}%\n\n"
        
        if proxy_status['proxy_details']:
            yield "**📋 Proxy Details:**\n"
            for proxy in proxy_status['proxy_details'][:5]:  # Show first 5
                status_emoji = "✅" if proxy['status'] == 'healthy' else "❌"
                yield f"{status_emoji} **{proxy['proxy_id']}** ({proxy['host']}:{proxy['port']})\n"
                yield f"   Success Rate: {proxy['success_rate']:.1f}%\n"
                yield f"   Avg Response: {proxy['average_response_time']:.2f}s\n"
                yield f"   Connections: {proxy['current_connections']}\n\n"
    
    async def _handle_health_check(self) -> AsyncGenerator[str, None]:
        """Handle system health check request."""
        yield "🏥 **System Health Check**\n\n"
        yield "Checking all services...\n\n"
        
        # Check Z.AI
        zai_health = await self.orchestrator.zai_client.health_check()
        status_emoji = "✅" if zai_health['status'] == 'healthy' else "❌"
        yield f"{status_emoji} **Z.AI Service:** {zai_health['status']}\n"
        if 'response_time' in zai_health:
            yield f"   Response Time: {zai_health['response_time']:.2f}s\n"
        
        # Check Grainchain
        grainchain_health = await self.orchestrator.grainchain_manager.health_check()
        status_emoji = "✅" if grainchain_health['status'] == 'healthy' else "❌"
        yield f"{status_emoji} **Grainchain Service:** {grainchain_health['status']}\n"
        yield f"   Active Sandboxes: {grainchain_health.get('active_sandboxes', 0)}\n"
        
        # Check ROMA
        roma_health = await self.orchestrator.roma_coordinator.health_check()
        status_emoji = "✅" if roma_health['status'] == 'healthy' else "❌"
        yield f"{status_emoji} **ROMA Coordinator:** {roma_health['status']}\n"
        yield f"   Active Tasks: {roma_health.get('active_tasks', 0)}\n"
        
        # Check Observer
        observer_health = await self.orchestrator.wandb_weave_observer.health_check()
        status_emoji = "✅" if observer_health['status'] == 'healthy' else "❌"
        yield f"{status_emoji} **Wandb+Weave Observer:** {observer_health['status']}\n"
        
        yield f"\n🎯 **Overall System Status:** "
        all_healthy = all([
            zai_health['status'] == 'healthy',
            grainchain_health['status'] == 'healthy',
            roma_health['status'] == 'healthy',
            observer_health['status'] == 'healthy'
        ])
        
        if all_healthy:
            yield "✅ **All Systems Operational**"
        else:
            yield "⚠️ **Some Services Need Attention**"

