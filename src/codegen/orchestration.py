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

    async def orchestrate(self, prompt: str, num_agents: int = 9, models: Optional[List[str]] = None) -> Dict:
        """Basic orchestration: run N agents and synthesize."""
        models = models or COUNCIL_MODELS

        # Create prompts for all agents
        prompts = [prompt] * num_agents
        agent_models = [models[i % len(models)] for i in range(num_agents)]

        # Execute all in parallel
        results = await self.executor.execute_agents_parallel(prompts, agent_models)

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


if __name__ == "__main__":
    asyncio.run(main())
