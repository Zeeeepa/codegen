"""
Intelligent Agent Orchestrator with Self-Healing and AI-Driven Decision Making

This module implements sophisticated multi-agent orchestration with:
- State tracking for all agent runs
- Intelligent progress monitoring
- AI-powered debugging of stuck agents
- Fallback logic and self-healing
- Graceful degradation
"""

import asyncio
import json
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

from codegen.agents.agent import Agent


class AgentRunStatus(Enum):
    """Status of an agent run."""
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETE = "complete"
    FAILED = "failed"
    STUCK = "stuck"
    TIMEOUT = "timeout"
    DISCARDED = "discarded"


class DecisionAction(Enum):
    """Actions that can be taken for stuck agents."""
    WAIT_LONGER = "wait_longer"
    DISCARD = "discard"
    RETRY = "retry"
    PROCEED_WITHOUT = "proceed_without"


@dataclass
class AgentRun:
    """Tracks a single agent run."""
    run_id: str
    task_id: int
    agent_obj: Any  # The actual task object
    prompt: str
    specialization: str
    status: AgentRunStatus = AgentRunStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    last_check_at: Optional[datetime] = None
    response: Optional[str] = None
    error: Optional[str] = None
    check_count: int = 0
    stuck_analysis: Optional[str] = None
    decision: Optional[DecisionAction] = None
    
    @property
    def elapsed_seconds(self) -> float:
        """Time since creation."""
        return (datetime.now() - self.created_at).total_seconds()
    
    @property
    def time_since_last_check(self) -> float:
        """Time since last status check."""
        if not self.last_check_at:
            return 0.0
        return (datetime.now() - self.last_check_at).total_seconds()


@dataclass
class OrchestrationResult:
    """Result of multi-agent orchestration."""
    total_agents: int
    completed: int
    failed: int
    discarded: int
    responses: List[str]
    agent_runs: List[AgentRun]
    total_time: float
    decisions_made: List[Dict[str, Any]]


class IntelligentOrchestrator:
    """
    Intelligent multi-agent orchestrator with AI-driven debugging and decision making.
    
    Features:
    - Launch multiple agents and track their run IDs
    - Monitor progress intelligently (not blind waiting)
    - Use AI to analyze stuck agents
    - Make intelligent decisions (wait/skip/retry)
    - Gracefully handle partial failures
    """
    
    def __init__(self, api_key: str, org_id: int, debug_agent: Optional[Agent] = None):
        self.api_key = api_key
        self.org_id = org_id
        self.agent = Agent(token=api_key, org_id=org_id)
        self.debug_agent = debug_agent or Agent(token=api_key, org_id=org_id)
        self.runs: Dict[str, AgentRun] = {}
        self.decisions: List[Dict[str, Any]] = []
    
    async def orchestrate(
        self,
        prompts: List[str],
        specializations: Optional[List[str]] = None,
        initial_timeout: float = 300.0,  # 5 minutes initial wait
        extended_timeout: float = 600.0,  # 10 minutes max wait
        check_interval: float = 3.0,
        min_required: Optional[int] = None
    ) -> OrchestrationResult:
        """
        Orchestrate multiple agents with intelligent monitoring.
        
        Args:
            prompts: List of prompts for each agent
            specializations: Optional specialization for each agent
            initial_timeout: Initial wait time before analyzing stuck agents
            extended_timeout: Maximum total wait time
            check_interval: How often to check agent status
            min_required: Minimum number of agents required (None = all)
        
        Returns:
            OrchestrationResult with all agent responses and decisions
        """
        start_time = time.time()
        
        # Phase 1: Launch all agents
        print(f"\n{'='*80}")
        print(f"🚀 PHASE 1: Launching {len(prompts)} agents")
        print(f"{'='*80}")
        
        await self._launch_agents(prompts, specializations)
        
        # Phase 2: Initial monitoring
        print(f"\n{'='*80}")
        print(f"⏱️  PHASE 2: Monitoring (initial timeout: {initial_timeout}s)")
        print(f"{'='*80}")
        
        await self._monitor_agents(initial_timeout, check_interval)
        
        # Phase 3: Analyze incomplete agents
        incomplete = self._get_incomplete_runs()
        
        if incomplete:
            print(f"\n{'='*80}")
            print(f"🔍 PHASE 3: Analyzing {len(incomplete)} incomplete agents")
            print(f"{'='*80}")
            
            await self._analyze_stuck_agents(incomplete)
            
            # Phase 4: Make decisions
            print(f"\n{'='*80}")
            print(f"🧠 PHASE 4: AI Decision Making")
            print(f"{'='*80}")
            
            await self._make_decisions(
                incomplete, 
                elapsed=time.time() - start_time,
                extended_timeout=extended_timeout,
                min_required=min_required
            )
            
            # Phase 5: Execute decisions
            print(f"\n{'='*80}")
            print(f"⚡ PHASE 5: Executing Decisions")
            print(f"{'='*80}")
            
            await self._execute_decisions(incomplete, extended_timeout - (time.time() - start_time))
        
        # Phase 6: Aggregate results
        print(f"\n{'='*80}")
        print(f"📊 PHASE 6: Aggregating Results")
        print(f"{'='*80}")
        
        result = self._aggregate_results(time.time() - start_time)
        
        return result
    
    async def _launch_agents(self, prompts: List[str], specializations: Optional[List[str]]):
        """Launch all agents and track their run IDs."""
        if specializations is None:
            specializations = ["general"] * len(prompts)
        
        for i, (prompt, spec) in enumerate(zip(prompts, specializations)):
            run_id = f"run_{int(time.time() * 1000)}_{i}"
            
            print(f"\n[{i+1}/{len(prompts)}] Launching agent: {spec}")
            print(f"    Run ID: {run_id}")
            
            try:
                # Launch agent
                task = self.agent.run(prompt=prompt)
                
                # Track the run
                agent_run = AgentRun(
                    run_id=run_id,
                    task_id=task.id,
                    agent_obj=task,
                    prompt=prompt,
                    specialization=spec,
                    status=AgentRunStatus.ACTIVE,
                    started_at=datetime.now()
                )
                
                self.runs[run_id] = agent_run
                
                print(f"    Task ID: {task.id} ✅")
                
            except Exception as e:
                print(f"    ❌ Failed to launch: {e}")
                agent_run = AgentRun(
                    run_id=run_id,
                    task_id=-1,
                    agent_obj=None,
                    prompt=prompt,
                    specialization=spec,
                    status=AgentRunStatus.FAILED,
                    error=str(e)
                )
                self.runs[run_id] = agent_run
            
            # Small delay between launches
            await asyncio.sleep(0.5)
    
    async def _monitor_agents(self, timeout: float, check_interval: float):
        """Monitor all agents until timeout or all complete."""
        start = time.time()
        
        while time.time() - start < timeout:
            elapsed = time.time() - start
            
            # Check all active runs
            active_runs = [r for r in self.runs.values() if r.status == AgentRunStatus.ACTIVE]
            
            if not active_runs:
                print(f"\n[{elapsed:.1f}s] ✅ All agents complete!")
                break
            
            # Update status for each run
            for run in active_runs:
                try:
                    run.agent_obj.refresh()
                    status = run.agent_obj.status.lower()
                    run.last_check_at = datetime.now()
                    run.check_count += 1
                    
                    if status in ("complete", "completed"):
                        run.status = AgentRunStatus.COMPLETE
                        run.completed_at = datetime.now()
                        run.response = run.agent_obj.result or ""
                        print(f"\n[{elapsed:.1f}s] ✅ {run.run_id} ({run.specialization}) COMPLETE - {len(run.response)} chars")
                    
                    elif status in ("failed", "error", "cancelled"):
                        run.status = AgentRunStatus.FAILED
                        run.error = f"Status: {status}"
                        print(f"\n[{elapsed:.1f}s] ❌ {run.run_id} ({run.specialization}) FAILED")
                
                except Exception as e:
                    print(f"\n[{elapsed:.1f}s] ⚠️  Error checking {run.run_id}: {e}")
            
            # Status summary every 30s
            if int(elapsed) % 30 == 0 and int(elapsed) > 0:
                completed = sum(1 for r in self.runs.values() if r.status == AgentRunStatus.COMPLETE)
                active = sum(1 for r in self.runs.values() if r.status == AgentRunStatus.ACTIVE)
                print(f"\n[{elapsed:.1f}s] 📊 Progress: {completed}/{len(self.runs)} complete, {active} active")
            
            await asyncio.sleep(check_interval)
    
    def _get_incomplete_runs(self) -> List[AgentRun]:
        """Get all runs that are not complete or failed."""
        return [r for r in self.runs.values() if r.status == AgentRunStatus.ACTIVE]
    
    async def _analyze_stuck_agents(self, runs: List[AgentRun]):
        """Use AI to analyze potentially stuck agents."""
        for run in runs:
            print(f"\n🔍 Analyzing {run.run_id} ({run.specialization})")
            print(f"   Elapsed: {run.elapsed_seconds:.1f}s")
            print(f"   Checks: {run.check_count}")
            
            # Gather diagnostic info
            try:
                run.agent_obj.refresh()
                current_status = run.agent_obj.status
                
                diagnostic_info = {
                    "run_id": run.run_id,
                    "task_id": run.task_id,
                    "specialization": run.specialization,
                    "elapsed_seconds": run.elapsed_seconds,
                    "current_status": current_status,
                    "check_count": run.check_count,
                    "prompt_length": len(run.prompt),
                    "time_since_last_check": run.time_since_last_check
                }
                
                # Ask AI to analyze
                analysis_prompt = f"""You are a debugging AI analyzing a potentially stuck agent.

Agent Information:
{json.dumps(diagnostic_info, indent=2)}

Prompt snippet: {run.prompt[:200]}...

Task: Analyze if this agent is:
1. Still processing normally (just slow)
2. Genuinely stuck (needs intervention)
3. Failed but status not updated

Provide analysis in 2-3 sentences."""

                print(f"   🤖 Asking debug AI...")
                analysis_task = self.debug_agent.run(prompt=analysis_prompt)
                
                # Wait for analysis (with timeout)
                analysis_start = time.time()
                while time.time() - analysis_start < 60:  # 1 min max for analysis
                    analysis_task.refresh()
                    if analysis_task.status.lower() in ("complete", "completed"):
                        run.stuck_analysis = analysis_task.result or "No analysis available"
                        print(f"   📝 Analysis: {run.stuck_analysis[:150]}...")
                        break
                    await asyncio.sleep(2)
                
            except Exception as e:
                run.stuck_analysis = f"Error during analysis: {e}"
                print(f"   ⚠️  Analysis failed: {e}")
    
    async def _make_decisions(
        self, 
        runs: List[AgentRun], 
        elapsed: float, 
        extended_timeout: float,
        min_required: Optional[int]
    ):
        """Use AI to make decisions about incomplete agents."""
        completed_count = sum(1 for r in self.runs.values() if r.status == AgentRunStatus.COMPLETE)
        total_count = len(self.runs)
        
        decision_prompt = f"""You are an orchestration AI making decisions about incomplete agent runs.

Situation:
- Total agents: {total_count}
- Completed: {completed_count}
- Incomplete: {len(runs)}
- Elapsed time: {elapsed:.1f}s
- Max timeout: {extended_timeout:.1f}s
- Min required: {min_required or 'all'}

Incomplete Agents:
"""
        
        for run in runs:
            decision_prompt += f"\n{run.run_id} ({run.specialization}):"
            decision_prompt += f"\n  - Elapsed: {run.elapsed_seconds:.1f}s"
            decision_prompt += f"\n  - Analysis: {run.stuck_analysis or 'N/A'}"
        
        decision_prompt += f"""

For EACH incomplete agent, decide ONE action:
1. WAIT_LONGER - Agent is processing normally, wait more
2. DISCARD - Agent is stuck/failed, proceed without it
3. RETRY - Agent failed, should retry with new run
4. PROCEED_WITHOUT - We have enough results, don't wait

Format your response as JSON:
{{
    "run_id": "action",
    ...
}}

Only return the JSON, no other text."""

        print(f"\n🤖 Asking decision AI...")
        
        try:
            decision_task = self.debug_agent.run(prompt=decision_prompt)
            
            # Wait for decision
            decision_start = time.time()
            while time.time() - decision_start < 60:
                decision_task.refresh()
                if decision_task.status.lower() in ("complete", "completed"):
                    decision_text = decision_task.result or "{}"
                    
                    # Parse JSON from response
                    try:
                        # Extract JSON from response
                        json_start = decision_text.find("{")
                        json_end = decision_text.rfind("}") + 1
                        if json_start >= 0 and json_end > json_start:
                            decision_json = json.loads(decision_text[json_start:json_end])
                            
                            # Apply decisions
                            for run_id, action_str in decision_json.items():
                                if run_id in [r.run_id for r in runs]:
                                    action = DecisionAction(action_str.lower())
                                    matching_run = next(r for r in runs if r.run_id == run_id)
                                    matching_run.decision = action
                                    
                                    self.decisions.append({
                                        "run_id": run_id,
                                        "action": action.value,
                                        "reason": matching_run.stuck_analysis or "N/A",
                                        "timestamp": datetime.now().isoformat()
                                    })
                                    
                                    print(f"   📌 {run_id}: {action.value}")
                    
                    except json.JSONDecodeError as e:
                        print(f"   ⚠️  Failed to parse decision JSON: {e}")
                        # Fallback: wait for all
                        for run in runs:
                            run.decision = DecisionAction.WAIT_LONGER
                    
                    break
                
                await asyncio.sleep(2)
        
        except Exception as e:
            print(f"   ⚠️  Decision making failed: {e}")
            # Fallback: wait for all
            for run in runs:
                run.decision = DecisionAction.WAIT_LONGER
    
    async def _execute_decisions(self, runs: List[AgentRun], remaining_time: float):
        """Execute decisions for incomplete agents."""
        wait_runs = [r for r in runs if r.decision == DecisionAction.WAIT_LONGER]
        discard_runs = [r for r in runs if r.decision in (DecisionAction.DISCARD, DecisionAction.PROCEED_WITHOUT)]
        
        # Discard immediately
        for run in discard_runs:
            run.status = AgentRunStatus.DISCARDED
            print(f"   🗑️  Discarded {run.run_id}")
        
        # Wait for remaining
        if wait_runs and remaining_time > 0:
            print(f"\n⏱️  Waiting up to {remaining_time:.1f}s for {len(wait_runs)} agents...")
            
            await self._monitor_agents(remaining_time, check_interval=3.0)
    
    def _aggregate_results(self, total_time: float) -> OrchestrationResult:
        """Aggregate results from all agents."""
        completed = [r for r in self.runs.values() if r.status == AgentRunStatus.COMPLETE]
        failed = [r for r in self.runs.values() if r.status == AgentRunStatus.FAILED]
        discarded = [r for r in self.runs.values() if r.status == AgentRunStatus.DISCARDED]
        
        responses = [r.response for r in completed if r.response]
        
        print(f"\n✅ Completed: {len(completed)}")
        print(f"❌ Failed: {len(failed)}")
        print(f"🗑️  Discarded: {len(discarded)}")
        print(f"⏱️  Total time: {total_time:.1f}s")
        
        return OrchestrationResult(
            total_agents=len(self.runs),
            completed=len(completed),
            failed=len(failed),
            discarded=len(discarded),
            responses=responses,
            agent_runs=list(self.runs.values()),
            total_time=total_time,
            decisions_made=self.decisions
        )

