"""
Intelligent Trace Analysis Engine
================================

Advanced trace analysis system that processes Codegen Agent Run Logs to extract
intelligent insights and enable systematic transfer of knowledge between agent runs.

Key Features:
- Pattern recognition in agent execution traces
- Context extraction from successful and failed runs
- Knowledge base building from execution history
- Intelligent recommendations based on historical patterns
- Continuous learning and optimization
"""

import asyncio
import json
import logging
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from dataclasses import dataclass
from enum import Enum
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import cosine_similarity

from codegen.cli.api.client import RestAPI
from codegen.cli.api.schemas import AgentRunWithLogsResponse
from ..core.event_system import Event, EventType, event_system

logger = logging.getLogger(__name__)


class TracePattern(str, Enum):
    """Common patterns found in agent execution traces."""
    
    SUCCESS_PATTERN = "success"
    FAILURE_PATTERN = "failure"
    RETRY_PATTERN = "retry"
    OPTIMIZATION_PATTERN = "optimization"
    ERROR_RECOVERY_PATTERN = "error_recovery"
    TOOL_USAGE_PATTERN = "tool_usage"
    CONTEXT_SWITCH_PATTERN = "context_switch"


@dataclass
class TraceInsight:
    """Insight extracted from trace analysis."""
    
    pattern_type: TracePattern
    confidence: float
    description: str
    context: Dict[str, Any]
    recommendations: List[str]
    related_traces: List[str]
    timestamp: datetime


@dataclass
class ExecutionContext:
    """Context information extracted from agent execution."""
    
    agent_run_id: str
    organization_id: str
    prompt: str
    tools_used: List[str]
    execution_time: float
    success: bool
    error_messages: List[str]
    key_actions: List[Dict[str, Any]]
    outcome_summary: str


class TraceAnalyzer:
    """
    Intelligent trace analysis engine for extracting insights from agent executions.
    
    Capabilities:
    - Pattern recognition in execution traces
    - Context extraction and knowledge building
    - Intelligent recommendations generation
    - Continuous learning from new executions
    """
    
    def __init__(self, api_client: RestAPI):
        self.api_client = api_client
        self.knowledge_base: Dict[str, List[TraceInsight]] = {}
        self.execution_contexts: List[ExecutionContext] = []
        self.pattern_models: Dict[TracePattern, Any] = {}
        self.vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
        
    async def analyze_agent_run(
        self,
        agent_run_id: str,
        organization_id: str
    ) -> List[TraceInsight]:
        """
        Analyze a specific agent run and extract insights.
        
        Args:
            agent_run_id: ID of the agent run to analyze
            organization_id: Organization ID for API access
            
        Returns:
            List of insights extracted from the trace
        """
        try:
            # Fetch agent run logs from Codegen API
            logs_response = await self._fetch_agent_logs(agent_run_id, organization_id)
            
            if not logs_response or not logs_response.logs:
                logger.warning(f"No logs found for agent run {agent_run_id}")
                return []
            
            # Extract execution context
            context = self._extract_execution_context(logs_response)
            self.execution_contexts.append(context)
            
            # Analyze patterns in the trace
            insights = await self._analyze_trace_patterns(context, logs_response.logs)
            
            # Store insights in knowledge base
            self._store_insights(agent_run_id, insights)
            
            # Publish trace analysis event
            await self._publish_trace_event(agent_run_id, insights)
            
            logger.info(f"Analyzed agent run {agent_run_id}, found {len(insights)} insights")
            return insights
            
        except Exception as e:
            logger.error(f"Failed to analyze agent run {agent_run_id}: {e}")
            return []
    
    async def get_recommendations(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Get intelligent recommendations based on historical patterns.
        
        Args:
            prompt: The prompt for the new agent run
            context: Additional context information
            
        Returns:
            List of recommendations with confidence scores
        """
        try:
            # Find similar historical executions
            similar_contexts = self._find_similar_contexts(prompt, context)
            
            # Generate recommendations based on patterns
            recommendations = []
            
            for similar_context in similar_contexts[:5]:  # Top 5 similar contexts
                insights = self.knowledge_base.get(similar_context.agent_run_id, [])
                
                for insight in insights:
                    if insight.pattern_type == TracePattern.SUCCESS_PATTERN:
                        recommendations.extend([
                            {
                                "type": "tool_suggestion",
                                "confidence": insight.confidence * 0.9,
                                "description": f"Consider using tools: {', '.join(similar_context.tools_used)}",
                                "rationale": f"Similar successful execution used these tools",
                                "context": insight.context
                            }
                        ])
                    
                    elif insight.pattern_type == TracePattern.ERROR_RECOVERY_PATTERN:
                        recommendations.extend([
                            {
                                "type": "error_prevention",
                                "confidence": insight.confidence * 0.8,
                                "description": insight.description,
                                "rationale": "Prevent common errors based on historical patterns",
                                "recommendations": insight.recommendations
                            }
                        ])
            
            # Sort by confidence and return top recommendations
            recommendations.sort(key=lambda x: x["confidence"], reverse=True)
            return recommendations[:10]
            
        except Exception as e:
            logger.error(f"Failed to generate recommendations: {e}")
            return []
    
    async def build_knowledge_graph(self) -> Dict[str, Any]:
        """
        Build a knowledge graph from all analyzed traces.
        
        Returns:
            Knowledge graph structure with nodes and relationships
        """
        try:
            nodes = []
            edges = []
            
            # Create nodes for each execution context
            for context in self.execution_contexts:
                nodes.append({
                    "id": context.agent_run_id,
                    "type": "execution",
                    "label": context.prompt[:50] + "..." if len(context.prompt) > 50 else context.prompt,
                    "success": context.success,
                    "tools": context.tools_used,
                    "execution_time": context.execution_time
                })
            
            # Create edges based on similarity and patterns
            for i, context1 in enumerate(self.execution_contexts):
                for j, context2 in enumerate(self.execution_contexts[i+1:], i+1):
                    similarity = self._calculate_context_similarity(context1, context2)
                    
                    if similarity > 0.7:  # High similarity threshold
                        edges.append({
                            "source": context1.agent_run_id,
                            "target": context2.agent_run_id,
                            "type": "similarity",
                            "weight": similarity,
                            "label": f"Similar ({similarity:.2f})"
                        })
            
            return {
                "nodes": nodes,
                "edges": edges,
                "metadata": {
                    "total_executions": len(self.execution_contexts),
                    "success_rate": sum(1 for c in self.execution_contexts if c.success) / len(self.execution_contexts),
                    "avg_execution_time": np.mean([c.execution_time for c in self.execution_contexts]),
                    "most_used_tools": self._get_most_used_tools()
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to build knowledge graph: {e}")
            return {"nodes": [], "edges": [], "metadata": {}}
    
    async def _fetch_agent_logs(
        self,
        agent_run_id: str,
        organization_id: str
    ) -> Optional[AgentRunWithLogsResponse]:
        """Fetch agent run logs from Codegen API."""
        try:
            # Use the existing Codegen API client to fetch logs
            endpoint = f"/v1/organizations/{organization_id}/agent/run/{agent_run_id}/logs"
            response = self.api_client._make_request(
                "GET",
                endpoint,
                None,
                AgentRunWithLogsResponse
            )
            return response
            
        except Exception as e:
            logger.error(f"Failed to fetch agent logs: {e}")
            return None
    
    def _extract_execution_context(
        self,
        logs_response: AgentRunWithLogsResponse
    ) -> ExecutionContext:
        """Extract execution context from agent run logs."""
        tools_used = set()
        error_messages = []
        key_actions = []
        
        for log in logs_response.logs:
            # Extract tools used
            if log.tool_name:
                tools_used.add(log.tool_name)
            
            # Extract error messages
            if log.message_type == "ERROR" and log.observation:
                error_messages.append(str(log.observation))
            
            # Extract key actions
            if log.message_type == "ACTION" and log.tool_name:
                key_actions.append({
                    "tool": log.tool_name,
                    "input": log.tool_input,
                    "output": log.tool_output,
                    "timestamp": log.created_at
                })
        
        # Determine success based on final status
        success = logs_response.status == "completed" and not error_messages
        
        # Calculate execution time
        if logs_response.logs:
            start_time = min(log.created_at for log in logs_response.logs)
            end_time = max(log.created_at for log in logs_response.logs)
            execution_time = (end_time - start_time).total_seconds()
        else:
            execution_time = 0.0
        
        return ExecutionContext(
            agent_run_id=str(logs_response.id),
            organization_id=str(logs_response.organization_id),
            prompt=logs_response.result or "Unknown prompt",
            tools_used=list(tools_used),
            execution_time=execution_time,
            success=success,
            error_messages=error_messages,
            key_actions=key_actions,
            outcome_summary=logs_response.result or "No result"
        )
    
    async def _analyze_trace_patterns(
        self,
        context: ExecutionContext,
        logs: List[Any]
    ) -> List[TraceInsight]:
        """Analyze patterns in the execution trace."""
        insights = []
        
        # Analyze success patterns
        if context.success:
            insights.append(TraceInsight(
                pattern_type=TracePattern.SUCCESS_PATTERN,
                confidence=0.9,
                description=f"Successful execution using tools: {', '.join(context.tools_used)}",
                context={
                    "tools_used": context.tools_used,
                    "execution_time": context.execution_time,
                    "key_actions": context.key_actions[:3]  # Top 3 actions
                },
                recommendations=[
                    f"Consider using {tool} for similar tasks" for tool in context.tools_used
                ],
                related_traces=[context.agent_run_id],
                timestamp=datetime.utcnow()
            ))
        
        # Analyze failure patterns
        if not context.success and context.error_messages:
            insights.append(TraceInsight(
                pattern_type=TracePattern.FAILURE_PATTERN,
                confidence=0.8,
                description=f"Execution failed with errors: {'; '.join(context.error_messages[:2])}",
                context={
                    "error_messages": context.error_messages,
                    "tools_attempted": context.tools_used,
                    "failure_point": self._identify_failure_point(logs)
                },
                recommendations=[
                    "Add error handling for similar scenarios",
                    "Consider alternative tools or approaches",
                    "Validate inputs before execution"
                ],
                related_traces=[context.agent_run_id],
                timestamp=datetime.utcnow()
            ))
        
        # Analyze tool usage patterns
        if context.tools_used:
            tool_sequence = self._extract_tool_sequence(logs)
            insights.append(TraceInsight(
                pattern_type=TracePattern.TOOL_USAGE_PATTERN,
                confidence=0.7,
                description=f"Tool usage sequence: {' -> '.join(tool_sequence)}",
                context={
                    "tool_sequence": tool_sequence,
                    "tool_effectiveness": self._calculate_tool_effectiveness(context, logs)
                },
                recommendations=[
                    f"Optimize tool sequence for better performance",
                    f"Consider parallel execution where possible"
                ],
                related_traces=[context.agent_run_id],
                timestamp=datetime.utcnow()
            ))
        
        return insights
    
    def _find_similar_contexts(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None
    ) -> List[ExecutionContext]:
        """Find execution contexts similar to the given prompt and context."""
        if not self.execution_contexts:
            return []
        
        # Create feature vectors for similarity comparison
        all_prompts = [ctx.prompt for ctx in self.execution_contexts] + [prompt]
        
        try:
            # Fit vectorizer and transform prompts
            tfidf_matrix = self.vectorizer.fit_transform(all_prompts)
            
            # Calculate similarity with the new prompt (last item)
            similarities = cosine_similarity(tfidf_matrix[-1:], tfidf_matrix[:-1]).flatten()
            
            # Sort contexts by similarity
            similar_indices = np.argsort(similarities)[::-1]
            
            return [self.execution_contexts[i] for i in similar_indices if similarities[i] > 0.3]
            
        except Exception as e:
            logger.error(f"Failed to find similar contexts: {e}")
            return []
    
    def _calculate_context_similarity(
        self,
        context1: ExecutionContext,
        context2: ExecutionContext
    ) -> float:
        """Calculate similarity between two execution contexts."""
        try:
            # Text similarity
            prompts = [context1.prompt, context2.prompt]
            tfidf_matrix = self.vectorizer.fit_transform(prompts)
            text_similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            
            # Tool similarity (Jaccard similarity)
            tools1 = set(context1.tools_used)
            tools2 = set(context2.tools_used)
            tool_similarity = len(tools1 & tools2) / len(tools1 | tools2) if tools1 | tools2 else 0
            
            # Success similarity
            success_similarity = 1.0 if context1.success == context2.success else 0.0
            
            # Weighted average
            return (text_similarity * 0.5 + tool_similarity * 0.3 + success_similarity * 0.2)
            
        except Exception as e:
            logger.error(f"Failed to calculate context similarity: {e}")
            return 0.0
    
    def _store_insights(self, agent_run_id: str, insights: List[TraceInsight]) -> None:
        """Store insights in the knowledge base."""
        self.knowledge_base[agent_run_id] = insights
    
    async def _publish_trace_event(
        self,
        agent_run_id: str,
        insights: List[TraceInsight]
    ) -> None:
        """Publish trace analysis event."""
        event = Event(
            type=EventType.AGENT_TRACE_UPDATED,
            source="trace_analyzer",
            data={
                "agent_run_id": agent_run_id,
                "insights_count": len(insights),
                "patterns_found": [insight.pattern_type.value for insight in insights]
            }
        )
        await event_system.publish(event)
    
    def _identify_failure_point(self, logs: List[Any]) -> Optional[str]:
        """Identify the point where execution failed."""
        for log in reversed(logs):
            if log.message_type == "ERROR":
                return f"Failed at {log.tool_name or 'unknown step'}: {log.observation}"
        return None
    
    def _extract_tool_sequence(self, logs: List[Any]) -> List[str]:
        """Extract the sequence of tools used in execution."""
        sequence = []
        for log in logs:
            if log.message_type == "ACTION" and log.tool_name:
                sequence.append(log.tool_name)
        return sequence
    
    def _calculate_tool_effectiveness(
        self,
        context: ExecutionContext,
        logs: List[Any]
    ) -> Dict[str, float]:
        """Calculate effectiveness score for each tool used."""
        tool_effectiveness = {}
        
        for tool in context.tools_used:
            # Simple effectiveness based on success and usage frequency
            tool_logs = [log for log in logs if log.tool_name == tool]
            success_rate = 1.0 if context.success else 0.5
            usage_frequency = len(tool_logs) / len(logs) if logs else 0
            
            tool_effectiveness[tool] = success_rate * (1 - usage_frequency * 0.1)  # Penalize overuse
        
        return tool_effectiveness
    
    def _get_most_used_tools(self) -> List[Tuple[str, int]]:
        """Get the most frequently used tools across all executions."""
        tool_counts = {}
        
        for context in self.execution_contexts:
            for tool in context.tools_used:
                tool_counts[tool] = tool_counts.get(tool, 0) + 1
        
        return sorted(tool_counts.items(), key=lambda x: x[1], reverse=True)[:10]


class ContextExtractor:
    """
    Context extraction engine for building searchable knowledge from agent executions.
    
    Extracts and structures context information for intelligent reuse in future runs.
    """
    
    def __init__(self, trace_analyzer: TraceAnalyzer):
        self.trace_analyzer = trace_analyzer
        self.context_database: Dict[str, Dict[str, Any]] = {}
    
    async def extract_context(
        self,
        agent_run_id: str,
        organization_id: str
    ) -> Dict[str, Any]:
        """
        Extract structured context from an agent run.
        
        Args:
            agent_run_id: ID of the agent run
            organization_id: Organization ID
            
        Returns:
            Structured context information
        """
        try:
            # Get insights from trace analyzer
            insights = await self.trace_analyzer.analyze_agent_run(agent_run_id, organization_id)
            
            # Find the execution context
            context = next(
                (ctx for ctx in self.trace_analyzer.execution_contexts 
                 if ctx.agent_run_id == agent_run_id),
                None
            )
            
            if not context:
                logger.warning(f"No execution context found for agent run {agent_run_id}")
                return {}
            
            # Extract structured context
            extracted_context = {
                "agent_run_id": agent_run_id,
                "prompt_analysis": self._analyze_prompt(context.prompt),
                "tool_patterns": self._extract_tool_patterns(context),
                "success_factors": self._identify_success_factors(context, insights),
                "failure_points": self._identify_failure_points(context, insights),
                "reusable_strategies": self._extract_reusable_strategies(insights),
                "performance_metrics": {
                    "execution_time": context.execution_time,
                    "tool_count": len(context.tools_used),
                    "action_count": len(context.key_actions),
                    "success": context.success
                },
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Store in context database
            self.context_database[agent_run_id] = extracted_context
            
            return extracted_context
            
        except Exception as e:
            logger.error(f"Failed to extract context for agent run {agent_run_id}: {e}")
            return {}
    
    def _analyze_prompt(self, prompt: str) -> Dict[str, Any]:
        """Analyze the prompt to extract key information."""
        return {
            "length": len(prompt),
            "keywords": self._extract_keywords(prompt),
            "intent": self._classify_intent(prompt),
            "complexity": self._assess_complexity(prompt)
        }
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text."""
        # Simple keyword extraction (can be enhanced with NLP)
        words = re.findall(r'\b\w+\b', text.lower())
        return [word for word in words if len(word) > 3][:10]
    
    def _classify_intent(self, prompt: str) -> str:
        """Classify the intent of the prompt."""
        prompt_lower = prompt.lower()
        
        if any(word in prompt_lower for word in ['fix', 'bug', 'error', 'issue']):
            return 'bug_fix'
        elif any(word in prompt_lower for word in ['create', 'add', 'implement', 'build']):
            return 'feature_development'
        elif any(word in prompt_lower for word in ['test', 'validate', 'check']):
            return 'testing'
        elif any(word in prompt_lower for word in ['refactor', 'optimize', 'improve']):
            return 'optimization'
        else:
            return 'general'
    
    def _assess_complexity(self, prompt: str) -> str:
        """Assess the complexity of the prompt."""
        word_count = len(prompt.split())
        
        if word_count < 10:
            return 'simple'
        elif word_count < 50:
            return 'medium'
        else:
            return 'complex'
    
    def _extract_tool_patterns(self, context: ExecutionContext) -> Dict[str, Any]:
        """Extract patterns from tool usage."""
        return {
            "tools_used": context.tools_used,
            "tool_sequence": [action["tool"] for action in context.key_actions],
            "tool_effectiveness": self.trace_analyzer._calculate_tool_effectiveness(context, [])
        }
    
    def _identify_success_factors(
        self,
        context: ExecutionContext,
        insights: List[TraceInsight]
    ) -> List[str]:
        """Identify factors that contributed to success."""
        if not context.success:
            return []
        
        factors = []
        
        # Tool-based success factors
        if context.tools_used:
            factors.append(f"Effective use of tools: {', '.join(context.tools_used)}")
        
        # Execution time factor
        if context.execution_time < 60:  # Less than 1 minute
            factors.append("Fast execution time")
        
        # Pattern-based factors from insights
        for insight in insights:
            if insight.pattern_type == TracePattern.SUCCESS_PATTERN:
                factors.extend(insight.recommendations)
        
        return factors
    
    def _identify_failure_points(
        self,
        context: ExecutionContext,
        insights: List[TraceInsight]
    ) -> List[str]:
        """Identify points where execution failed."""
        if context.success:
            return []
        
        failure_points = []
        
        # Error-based failure points
        failure_points.extend(context.error_messages)
        
        # Pattern-based failure points from insights
        for insight in insights:
            if insight.pattern_type == TracePattern.FAILURE_PATTERN:
                failure_points.append(insight.description)
        
        return failure_points
    
    def _extract_reusable_strategies(self, insights: List[TraceInsight]) -> List[Dict[str, Any]]:
        """Extract strategies that can be reused in future runs."""
        strategies = []
        
        for insight in insights:
            if insight.confidence > 0.7:  # High confidence insights
                strategies.append({
                    "pattern": insight.pattern_type.value,
                    "description": insight.description,
                    "recommendations": insight.recommendations,
                    "confidence": insight.confidence
                })
        
        return strategies
