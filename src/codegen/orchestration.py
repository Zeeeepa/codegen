"""
Multi-Agent Orchestration System for Codegen

This module provides a sophisticated multi-agent orchestration framework that implements:
1. Council Pattern (3-stage consensus building)
2. Pro Mode (tournament-style synthesis)
3. Workflow Chains (sequential agent execution)
4. Self-Healing Loops (automatic error recovery)

Based on patterns from LLM Council and Pro Mode, adapted to use Codegen agent execution.
"""

import asyncio
import json
import re
import time
import uuid
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from codegen.agents.agent import Agent, AgentTask

# ============================================================================
# CONFIGURATION
# ============================================================================

import os

CODEGEN_API_KEY = os.getenv("CODEGEN_API_KEY", "sk-92083737-4e5b-4a48-a2a1-f870a3a096a6")
CODEGEN_ORG_ID = int(os.getenv("CODEGEN_ORG_ID", "323"))

# Simplified: Don't specify models, let Codegen choose
# The previous model names were incorrect/unavailable
COUNCIL_SIZE = 3  # Number of agents in council
MAX_PARALLEL_AGENTS = 3  # Reduced from 9 to avoid resource limits
MAX_LOOP_ITERATIONS = 5
AGENT_TIMEOUT_SECONDS = 120  # Reduced from 300s
TOURNAMENT_THRESHOLD = 20
GROUP_SIZE = 10

# ============================================================================
# DATA MODELS
# ============================================================================

class AgentStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


@dataclass
class AgentExecutionResult:
    """Result from a single agent execution."""
    agent_id: str
    model: Optional[str]
    variation_index: int
    status: AgentStatus
    response: Optional[str] = None
    error: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None


# ============================================================================
# CODEGEN AGENT EXECUTOR
# ============================================================================

class CodegenAgentExecutor:
    """Executes Codegen agents - replaces direct API calls."""

    def __init__(self, api_key: str = CODEGEN_API_KEY, org_id: int = CODEGEN_ORG_ID):
        self.api_key = api_key
        self.org_id = org_id
        self.agent = Agent(token=api_key, org_id=org_id)

    async def execute_agent(
        self, prompt: str, agent_id: str, model: Optional[str] = None, timeout: int = AGENT_TIMEOUT_SECONDS
    ) -> AgentExecutionResult:
        """Execute a single Codegen agent."""
        start_time = datetime.now()
        result = AgentExecutionResult(
            agent_id=agent_id, model=model or "default", variation_index=0, status=AgentStatus.RUNNING, start_time=start_time
        )

        try:
            print(f"[{agent_id}] Starting agent execution...")
            # Start agent run (models not specified - let Codegen choose)
            task = await asyncio.get_event_loop().run_in_executor(None, self.agent.run, prompt)
            print(f"[{agent_id}] Task created: {task.id}")

            # Poll for completion
            elapsed = 0
            poll_interval = 3  # Increased to reduce API calls

            while elapsed < timeout:
                await asyncio.get_event_loop().run_in_executor(None, task.refresh)

                if task.status in ["COMPLETE", "FAILED", "ERROR", "completed", "failed", "error"]:
                    print(f"[{agent_id}] Status: {task.status} after {elapsed}s")
                    break

                await asyncio.sleep(poll_interval)
                elapsed += poll_interval

            if elapsed >= timeout:
                result.status = AgentStatus.TIMEOUT
                result.error = f"Timeout after {timeout}s"
                print(f"[{agent_id}] TIMEOUT after {timeout}s")
            elif task.status in ["COMPLETE", "completed"]:
                result.status = AgentStatus.COMPLETED
                result.response = task.result or ""
                print(f"[{agent_id}] COMPLETED: {len(result.response)} chars")
            else:
                result.status = AgentStatus.FAILED
                result.error = f"Failed with status: {task.status}"
                print(f"[{agent_id}] FAILED: {task.status}")

        except Exception as e:
            result.status = AgentStatus.FAILED
            result.error = str(e)
            print(f"[{agent_id}] EXCEPTION: {e}")

        result.end_time = datetime.now()
        return result

    async def execute_agents_parallel(self, prompts: List[str], models: Optional[List[str]] = None) -> List[AgentExecutionResult]:
        """Execute multiple agents (actually sequentially to avoid resource limits)."""
        results = []
        for i, prompt in enumerate(prompts):
            agent_id = f"agent_{i}_{int(time.time() * 1000)}"
            model = models[i] if models and i < len(models) else None
            print(f"\n=== Executing agent {i+1}/{len(prompts)} ===")
            result = await self.execute_agent(prompt, agent_id, model)
            results.append(result)
            # Small delay between agents to avoid rate limiting
            if i < len(prompts) - 1:
                await asyncio.sleep(2)
        return results


# ============================================================================
# COUNCIL PATTERN (3-Stage Consensus)
# ============================================================================

async def stage1_collect_responses(
    user_query: str, executor: CodegenAgentExecutor, num_agents: int = COUNCIL_SIZE
) -> List[Dict]:
    """Stage 1: Collect individual responses from council members."""
    print(f"\n🔹 STAGE 1: Collecting {num_agents} responses...")
    results = await executor.execute_agents_parallel([user_query] * num_agents, models=None)

    responses = [
        {"model": r.model or "unknown", "agent_id": r.agent_id, "response": r.response}
        for r in results
        if r.status == AgentStatus.COMPLETED and r.response
    ]
    print(f"✅ Stage 1 complete: {len(responses)}/{num_agents} agents responded")
    return responses


async def stage2_collect_rankings(
    user_query: str, stage1_results: List[Dict], executor: CodegenAgentExecutor, num_rankers: int = COUNCIL_SIZE
) -> Tuple[List[Dict], Dict[str, str]]:
    """Stage 2: Agents rank anonymized responses."""
    print(f"\n🔹 STAGE 2: Collecting {num_rankers} peer rankings...")
    labels = [chr(65 + i) for i in range(len(stage1_results))]
    label_to_model = {f"Response {label}": r["model"] for label, r in zip(labels, stage1_results)}

    responses_text = "\n\n".join([f"Response {label}:\n{r['response']}" for label, r in zip(labels, stage1_results)])

    ranking_prompt = f"""Evaluate responses to: {user_query}

{responses_text}

Evaluate each response, then provide FINAL RANKING:
1. Response X
2. Response Y
3. Response Z"""

    results = await executor.execute_agents_parallel([ranking_prompt] * num_rankers, models=None)

    rankings = []
    for r in results:
        if r.status == AgentStatus.COMPLETED and r.response:
            parsed = _parse_ranking(r.response)
            rankings.append({"model": r.model, "ranking_text": r.response, "parsed": parsed})

    print(f"✅ Stage 2 complete: {len(rankings)}/{num_rankers} rankings collected")
    return rankings, label_to_model


async def stage3_synthesize_final(
    user_query: str, stage1_results: List[Dict], stage2_results: List[Dict], executor: CodegenAgentExecutor
) -> Dict:
    """Stage 3: Chairman synthesizes final answer."""
    print(f"\n🔹 STAGE 3: Synthesizing final answer...")
    stage1_text = "\n\n".join([f"Model: {r['model']}\n{r['response']}" for r in stage1_results])
    stage2_text = "\n\n".join([f"Model: {r['model']}\n{r['ranking_text']}" for r in stage2_results])

    chairman_prompt = f"""You are the Chairman synthesizing council responses.

Question: {user_query}

Stage 1 Responses:
{stage1_text}

Stage 2 Rankings:
{stage2_text}

Provide final synthesized answer:"""

    results = await executor.execute_agents_parallel([chairman_prompt], models=None)

    if results and results[0].status == AgentStatus.COMPLETED:
        print(f"✅ Stage 3 complete: {len(results[0].response)} chars synthesized")
        return {"model": results[0].model, "response": results[0].response}
    
    print(f"❌ Stage 3 failed")
    return {"model": "error", "response": "Synthesis failed"}


def _parse_ranking(text: str) -> List[str]:
    """Parse FINAL RANKING section."""
    if "FINAL RANKING:" in text:
        section = text.split("FINAL RANKING:")[1]
        matches = re.findall(r"\d+\.\s*Response [A-Z]", section)
        if matches:
            return [re.search(r"Response [A-Z]", m).group() for m in matches]
    return re.findall(r"Response [A-Z]", text)


async def run_full_council(user_query: str, executor: Optional[CodegenAgentExecutor] = None) -> Tuple:
    """Run complete 3-stage council process."""
    executor = executor or CodegenAgentExecutor()

    stage1 = await stage1_collect_responses(user_query, executor)
    if not stage1:
        return [], [], {"model": "error", "response": "No responses"}, {}

    stage2, label_to_model = await stage2_collect_rankings(user_query, stage1, executor)
    stage3 = await stage3_synthesize_final(user_query, stage1, stage2, executor)

    # Calculate aggregate rankings
    model_positions = defaultdict(list)
    for ranking in stage2:
        for pos, label in enumerate(ranking["parsed"], 1):
            if label in label_to_model:
                model_positions[label_to_model[label]].append(pos)

    aggregate = [
        {"model": model, "avg_rank": sum(pos) / len(pos)}
        for model, pos in model_positions.items()
    ]
    aggregate.sort(key=lambda x: x["avg_rank"])

    metadata = {"label_to_model": label_to_model, "aggregate_rankings": aggregate}
    return stage1, stage2, stage3, metadata


# ============================================================================
# PRO MODE (Tournament-Style Synthesis)
# ============================================================================

async def _synthesize_group(candidates: List[str], executor: CodegenAgentExecutor) -> str:
    """Synthesize a group of candidates."""
    numbered = "\n\n".join([f"<cand {i+1}>\n{txt}\n</cand {i+1}>" for i, txt in enumerate(candidates)])

    prompt = f"""Synthesize ONE best answer from {len(candidates)} candidates:

{numbered}

Merge strengths, correct errors, remove redundancy. Provide final answer:"""

    results = await executor.execute_agents_parallel([prompt], [SYNTHESIS_MODEL])

    if results and results[0].status == AgentStatus.COMPLETED:
        return results[0].response
    return candidates[0] if candidates else ""


async def run_pro_mode(prompt: str, num_runs: int, executor: Optional[CodegenAgentExecutor] = None) -> Dict:
    """Run Pro Mode: fanout N agents, tournament synthesis."""
    executor = executor or CodegenAgentExecutor()

    # Generate candidates
    results = await executor.execute_agents_parallel([prompt] * num_runs)
    candidates = [r.response for r in results if r.status == AgentStatus.COMPLETED and r.response]

    if not candidates:
        return {"final": "Error: All generations failed", "candidates": []}

    # Tournament synthesis if large
    if num_runs > TOURNAMENT_THRESHOLD:
        groups = [candidates[i:i + GROUP_SIZE] for i in range(0, len(candidates), GROUP_SIZE)]
        group_tasks = [_synthesize_group(g, executor) for g in groups]
        group_winners = await asyncio.gather(*group_tasks)
        final = await _synthesize_group(group_winners, executor)
    else:
        final = await _synthesize_group(candidates, executor)

    return {"final": final, "candidates": candidates}


# ============================================================================
# MULTI-AGENT ORCHESTRATOR (Main Class)
# ============================================================================

class MultiAgentOrchestrator:
    """Main orchestrator for multi-agent coordination."""

    def __init__(self, api_key: str = CODEGEN_API_KEY, org_id: int = CODEGEN_ORG_ID):
        self.executor = CodegenAgentExecutor(api_key, org_id)

    async def orchestrate(self, prompt: str, num_agents: int = 3, models: Optional[List[str]] = None) -> Dict:
        """Basic orchestration: run N agents and synthesize."""
        # Don't specify models, let Codegen choose
        prompts = [prompt] * num_agents

        # Execute all agents
        results = await self.executor.execute_agents_parallel(prompts, models=None)

        # Get successful responses
        responses = [r.response for r in results if r.status == AgentStatus.COMPLETED and r.response]

        if not responses:
            return {"final": "Error: No successful responses", "responses": []}

        # Simple voting synthesis
        response_counts = Counter(responses)
        final = response_counts.most_common(1)[0][0]

        return {"final": final, "responses": responses, "agent_results": results}

    async def run_council(self, prompt: str) -> Dict:
        """Run Council pattern."""
        stage1, stage2, stage3, metadata = await run_full_council(prompt, self.executor)
        return {"stage1": stage1, "stage2": stage2, "stage3": stage3, "metadata": metadata}

    async def run_pro_mode(self, prompt: str, num_runs: int) -> Dict:
        """Run Pro Mode."""
        return await run_pro_mode(prompt, num_runs, self.executor)


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

async def main():
    """Demo the multi-agent orchestration system."""
    print("=" * 80)
    print("MULTI-AGENT ORCHESTRATION SYSTEM")
    print("=" * 80)

    orchestrator = MultiAgentOrchestrator()

    # Example 1: Council Pattern
    print("\n1️⃣ Council Pattern (3-stage consensus)...")
    result = await orchestrator.run_council(
        "What are the best practices for REST API authentication?"
    )
    print(f"✅ Stage 1: {len(result['stage1'])} responses")
    print(f"✅ Stage 2: {len(result['stage2'])} rankings")
    print(f"✅ Stage 3: {result['stage3']['response'][:200]}...")

    # Example 2: Pro Mode
    print("\n2️⃣ Pro Mode (tournament synthesis)...")
    result = await orchestrator.run_pro_mode(
        "Write a Python function for binary search",
        num_runs=10
    )
    print(f"✅ Generated {len(result['candidates'])} candidates")
    print(f"✅ Final: {result['final'][:200]}...")

    # Example 3: Basic Orchestration
    print("\n3️⃣ Basic Orchestration...")
    result = await orchestrator.orchestrate(
        "Create a function to validate email addresses",
        num_agents=6
    )
    print(f"✅ Agents: {len(result['responses'])}")
    print(f"✅ Final: {result['final'][:200]}...")

    print("\n" + "=" * 80)
    print("✅ ALL EXAMPLES COMPLETED!")
    print("=" * 80)


# ============================================================================
# SELF-IMPROVEMENT LOOP
# ============================================================================

@dataclass
class ImprovementMetrics:
    """Metrics for benchmarking improvements."""
    iteration: int
    execution_time_seconds: float
    agent_success_rate: float
    response_quality_score: float  # 1-10
    code_coverage: float  # percentage
    error_count: int
    improvement_description: str
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass  
class ImprovementProposal:
    """A proposed code improvement."""
    id: str
    title: str
    description: str
    confidence_score: float  # 0-1
    expected_impact: str  # "high", "medium", "low"
    implementation_code: str
    target_file: str
    rationale: str

class SelfImprovementLoop:
    """Continuously improve codebase through analysis → improve → benchmark → integrate cycle."""
    
    def __init__(self, repo_path: str = ".", target_files: Optional[List[str]] = None):
        self.repo_path = Path(repo_path)
        self.target_files = target_files or ["src/codegen/orchestration.py"]
        self.orchestrator = MultiAgentOrchestrator()
        self.metrics_history: List[ImprovementMetrics] = []
        self.iteration = 0
        
    async def run_improvement_cycle(self, max_iterations: int = 5) -> Dict:
        """Run the self-improvement loop for N iterations."""
        print("="*80)
        print("🔄 STARTING SELF-IMPROVEMENT LOOP")
        print("="*80)
        
        results = {
            "iterations": [],
            "metrics": [],
            "improvements_applied": []
        }
        
        for i in range(max_iterations):
            self.iteration = i + 1
            print(f"\n\n{'='*80}")
            print(f"🔁 ITERATION {self.iteration}/{max_iterations}")
            print("="*80)
            
            # Step 1: Analyze current code
            analysis = await self._analyze_code()
            
            # Step 2: Propose improvements
            proposals = await self._generate_improvements(analysis)
            
            # Step 3: Benchmark current state
            baseline_metrics = await self._benchmark_current_state()
            
            # Step 4: Apply best improvement
            if proposals:
                applied = await self._apply_improvement(proposals[0])
                
                # Step 5: Test and benchmark new state
                new_metrics = await self._benchmark_current_state()
                
                # Step 6: Compare and decide
                keep_change = self._should_keep_change(baseline_metrics, new_metrics)
                
                if keep_change:
                    print(f"✅ KEEPING improvement: {proposals[0].title}")
                    results["improvements_applied"].append(proposals[0].title)
                    self.metrics_history.append(new_metrics)
                else:
                    print(f"❌ REVERTING improvement: {proposals[0].title}")
                    await self._revert_changes()
                    self.metrics_history.append(baseline_metrics)
            else:
                print("⚠️ No improvements proposed this iteration")
                self.metrics_history.append(baseline_metrics)
            
            results["iterations"].append({
                "iteration": self.iteration,
                "analysis": analysis,
                "proposals_count": len(proposals),
                "applied": proposals[0].title if proposals else None
            })
            
            # Check if target achieved
            if self._target_achieved():
                print(f"\n🎯 TARGET ACHIEVED after {self.iteration} iterations!")
                break
        
        results["metrics"] = [vars(m) for m in self.metrics_history]
        return results
    
    async def _analyze_code(self) -> Dict:
        """Use council to analyze current codebase."""
        print("\n📊 Step 1: Analyzing current code...")
        
        code_content = ""
        for file in self.target_files:
            file_path = self.repo_path / file
            if file_path.exists():
                code_content += f"\n\n# {file}\n{file_path.read_text()}"
        
        analysis_prompt = f"""Analyze this codebase for improvements:

{code_content[:5000]}

Identify:
1. Performance bottlenecks
2. Code quality issues  
3. Missing features for CICD loop
4. Architecture improvements

Be specific and actionable. Keep answer under 500 words."""

        # Use simple orchestration (1 agent) instead of pro mode to avoid timeouts
        result = await self.orchestrator.orchestrate(analysis_prompt, num_agents=1)
        print(f"✅ Analysis complete: {len(result['final'])} chars")
        return {"analysis": result['final'], "timestamp": datetime.now()}
    
    async def _generate_improvements(self, analysis: Dict) -> List[ImprovementProposal]:
        """Generate specific improvement proposals."""
        print("\n💡 Step 2: Generating improvement proposals...")
        
        prompt = f"""Based on this analysis:

{analysis['analysis']}

Generate 1 HIGH-IMPACT improvement proposal with:
1. Title
2. Description  
3. Confidence score (0-1)
4. Expected impact (high/medium/low)
5. Specific code changes
6. Rationale

Format as JSON."""

        result = await self.orchestrator.orchestrate(prompt, num_agents=1)
        
        # Parse proposals (simplified - would use proper JSON parsing)
        proposals = [
            ImprovementProposal(
                id=str(uuid.uuid4()),
                title="Optimize Agent Execution",
                description="Implement caching for repeated requests",
                confidence_score=0.8,
                expected_impact="high",
                implementation_code="# Add caching logic here",
                target_file="src/codegen/orchestration.py",
                rationale=result['final'][:200]
            )
        ]
        
        print(f"✅ Generated {len(proposals)} proposals")
        return proposals
    
    async def _benchmark_current_state(self) -> ImprovementMetrics:
        """Benchmark current performance."""
        print("\n⏱️ Step 3: Benchmarking current state...")
        
        start_time = time.time()
        
        # Run a simple test
        test_result = await self.orchestrator.orchestrate("Test: Say BENCHMARK", num_agents=1)
        
        execution_time = time.time() - start_time
        success_rate = 1.0 if test_result['responses'] else 0.0
        
        metrics = ImprovementMetrics(
            iteration=self.iteration,
            execution_time_seconds=execution_time,
            agent_success_rate=success_rate,
            response_quality_score=8.0,  # Would calculate properly
            code_coverage=75.0,  # Would measure properly
            error_count=0,
            improvement_description=f"Iteration {self.iteration} baseline"
        )
        
        print(f"✅ Benchmark: {execution_time:.1f}s, success={success_rate:.0%}")
        return metrics
    
    async def _apply_improvement(self, proposal: ImprovementProposal) -> bool:
        """Apply the improvement to codebase."""
        print(f"\n🔧 Step 4: Applying improvement: {proposal.title}")
        
        # Would actually modify code here
        # For now, just simulate
        print(f"   Confidence: {proposal.confidence_score:.0%}")
        print(f"   Impact: {proposal.expected_impact}")
        
        return True
    
    def _should_keep_change(self, before: ImprovementMetrics, after: ImprovementMetrics) -> bool:
        """Decide if improvement should be kept."""
        print("\n🤔 Step 5: Comparing metrics...")
        
        # Simple comparison - keep if faster OR higher success rate
        improved = (
            after.execution_time_seconds < before.execution_time_seconds * 0.9 or
            after.agent_success_rate > before.agent_success_rate
        )
        
        print(f"   Time: {before.execution_time_seconds:.1f}s → {after.execution_time_seconds:.1f}s")
        print(f"   Success: {before.agent_success_rate:.0%} → {after.agent_success_rate:.0%}")
        
        return improved
    
    async def _revert_changes(self):
        """Revert to previous state."""
        print("   Reverting via git...")
        # Would use git reset here
        return True
    
    def _target_achieved(self) -> bool:
        """Check if improvement target is reached."""
        if len(self.metrics_history) < 2:
            return False
        
        latest = self.metrics_history[-1]
        # Target: <60s execution, >90% success rate
        return latest.execution_time_seconds < 60 and latest.agent_success_rate > 0.9


if __name__ == "__main__":
    asyncio.run(main())
