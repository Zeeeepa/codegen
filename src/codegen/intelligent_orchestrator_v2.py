"""
Intelligent Agent Orchestrator V2 - Using Official Codegen REST API

This version uses the OFFICIAL Codegen API endpoints:
- POST /v1/organizations/{org_id}/agent/run - Create agent run
- GET /v1/organizations/{org_id}/agent/run/{agent_run_id} - Get run status
- GET /v1/organizations/{org_id}/agent/runs - List all runs

Features:
- Track OFFICIAL agent_run_id from API
- Intelligent progress monitoring
- AI-powered debugging of stuck agents
- Fallback logic and self-healing
- Graceful degradation
"""

import asyncio
import json
import time
import requests
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any

# Base URL for Codegen API
CODEGEN_API_BASE = "https://api.codegen.com"


class AgentRunStatus(Enum):
    """Status from Codegen API."""
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETE = "complete"
    FAILED = "failed"
    CANCELLED = "cancelled"
    STUCK = "stuck"  # Our custom status
    TIMEOUT = "timeout"  # Our custom status
    DISCARDED = "discarded"  # Our custom status


class DecisionAction(Enum):
    """Actions for stuck agents."""
    WAIT_LONGER = "wait_longer"
    DISCARD = "discard"
    RETRY = "retry"
    PROCEED_WITHOUT = "proceed_without"


@dataclass
class AgentRun:
    """Tracks a single agent run using OFFICIAL API data."""
    agent_run_id: int  # OFFICIAL ID from API
    prompt: str
    specialization: str
    api_status: str = "pending"  # Raw status from API
    status: AgentRunStatus = AgentRunStatus.PENDING  # Our interpretation
    created_at: datetime = field(default_factory=datetime.now)
    last_check_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    response: Optional[str] = None
    error: Optional[str] = None
    check_count: int = 0
    stuck_analysis: Optional[str] = None
    decision: Optional[DecisionAction] = None
    raw_api_response: Optional[Dict] = None
    
    @property
    def elapsed_seconds(self) -> float:
        """Time since creation."""
        return (datetime.now() - self.created_at).total_seconds()


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


class IntelligentOrchestratorV2:
    """
    Intelligent multi-agent orchestrator using OFFICIAL Codegen REST API.
    """
    
    def __init__(self, api_key: str, org_id: int):
        self.api_key = api_key
        self.org_id = org_id
        self.runs: Dict[int, AgentRun] = {}  # Keyed by OFFICIAL agent_run_id
        self.decisions: List[Dict[str, Any]] = []
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    def _create_agent_run(self, prompt: str) -> Optional[int]:
        """
        Create agent run using OFFICIAL API.
        Returns agent_run_id or None on failure.
        """
        url = f"{CODEGEN_API_BASE}/v1/organizations/{self.org_id}/agent/run"
        
        payload = {
            "prompt": prompt
        }
        
        try:
            response = requests.post(url, headers=self.headers, json=payload, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            agent_run_id = data.get("id")
            
            if agent_run_id:
                print(f"   ✅ Created agent_run_id: {agent_run_id}")
                return agent_run_id
            else:
                print(f"   ❌ No id in response: {data}")
                return None
                
        except Exception as e:
            print(f"   ❌ API Error: {e}")
            return None
    
    def _get_agent_run_status(self, agent_run_id: int) -> Optional[Dict]:
        """
        Get agent run status using OFFICIAL API.
        Returns full API response or None on failure.
        """
        url = f"{CODEGEN_API_BASE}/v1/organizations/{self.org_id}/agent/run/{agent_run_id}"
        
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"   ⚠️  Error checking {agent_run_id}: {e}")
            return None
    
    async def orchestrate(
        self,
        prompts: List[str],
        specializations: Optional[List[str]] = None,
        initial_timeout: float = 300.0,
        extended_timeout: float = 600.0,
        check_interval: float = 3.0,
        min_required: Optional[int] = None
    ) -> OrchestrationResult:
        """
        Orchestrate multiple agents with intelligent monitoring.
        """
        start_time = time.time()
        
        if specializations is None:
            specializations = ["general"] * len(prompts)
        
        # Phase 1: Launch all agents
        print(f"\n{'='*80}")
        print(f"🚀 PHASE 1: Launching {len(prompts)} agents via OFFICIAL API")
        print(f"{'='*80}")
        
        await self._launch_agents(prompts, specializations)
        
        if not self.runs:
            print("\n❌ No agents launched successfully!")
            return OrchestrationResult(
                total_agents=len(prompts),
                completed=0,
                failed=len(prompts),
                discarded=0,
                responses=[],
                agent_runs=[],
                total_time=time.time() - start_time,
                decisions_made=[]
            )
        
        # Phase 2: Initial monitoring
        print(f"\n{'='*80}")
        print(f"⏱️  PHASE 2: Monitoring {len(self.runs)} agents (timeout: {initial_timeout}s)")
        print(f"{'='*80}")
        
        await self._monitor_agents(initial_timeout, check_interval)
        
        # Phase 3-5: Handle incomplete agents
        incomplete = self._get_incomplete_runs()
        
        if incomplete:
            print(f"\n{'='*80}")
            print(f"🔍 PHASE 3: {len(incomplete)} agents still incomplete")
            print(f"{'='*80}")
            
            # Ask AI to analyze
            await self._ai_analyze_and_decide(
                incomplete,
                elapsed=time.time() - start_time,
                extended_timeout=extended_timeout,
                min_required=min_required
            )
            
            # Execute decisions
            await self._execute_decisions(incomplete, extended_timeout - (time.time() - start_time))
        
        # Phase 6: Aggregate
        print(f"\n{'='*80}")
        print(f"📊 FINAL RESULTS")
        print(f"{'='*80}")
        
        result = self._aggregate_results(time.time() - start_time)
        return result
    
    async def _launch_agents(self, prompts: List[str], specializations: List[str]):
        """Launch all agents using OFFICIAL API."""
        for i, (prompt, spec) in enumerate(zip(prompts, specializations)):
            print(f"\n[{i+1}/{len(prompts)}] Launching: {spec}")
            
            agent_run_id = self._create_agent_run(prompt)
            
            if agent_run_id:
                agent_run = AgentRun(
                    agent_run_id=agent_run_id,
                    prompt=prompt,
                    specialization=spec,
                    status=AgentRunStatus.ACTIVE,
                    api_status="active"
                )
                self.runs[agent_run_id] = agent_run
            else:
                print(f"   ❌ Failed to create agent")
            
            # Small delay to avoid rate limits (10 req/min = 6s between)
            if i < len(prompts) - 1:
                await asyncio.sleep(6.5)
    
    async def _monitor_agents(self, timeout: float, check_interval: float):
        """Monitor all agents using OFFICIAL API."""
        start = time.time()
        
        while time.time() - start < timeout:
            elapsed = time.time() - start
            
            # Check all non-terminal runs
            active_runs = [
                r for r in self.runs.values() 
                if r.status not in (AgentRunStatus.COMPLETE, AgentRunStatus.FAILED, 
                                   AgentRunStatus.CANCELLED, AgentRunStatus.DISCARDED)
            ]
            
            if not active_runs:
                print(f"\n[{elapsed:.1f}s] ✅ All agents terminal!")
                break
            
            # Update each run
            for run in active_runs:
                api_response = self._get_agent_run_status(run.agent_run_id)
                
                if api_response:
                    run.raw_api_response = api_response
                    run.last_check_at = datetime.now()
                    run.check_count += 1
                    
                    # Update status from API
                    api_status = api_response.get("status", "unknown").lower()
                    run.api_status = api_status
                    
                    if api_status == "complete":
                        run.status = AgentRunStatus.COMPLETE
                        run.completed_at = datetime.now()
                        run.response = api_response.get("response", "")
                        print(f"\n[{elapsed:.1f}s] ✅ {run.agent_run_id} ({run.specialization}) COMPLETE - {len(run.response)} chars")
                    
                    elif api_status in ("failed", "error", "cancelled"):
                        run.status = AgentRunStatus.FAILED
                        run.error = api_response.get("error", f"Status: {api_status}")
                        print(f"\n[{elapsed:.1f}s] ❌ {run.agent_run_id} ({run.specialization}) {api_status.upper()}")
                    
                    elif api_status in ("active", "pending"):
                        # Check if it's been too long
                        if run.elapsed_seconds > 300:  # 5 min
                            run.status = AgentRunStatus.STUCK
                            print(f"\n[{elapsed:.1f}s] ⚠️  {run.agent_run_id} ({run.specialization}) appears STUCK (>300s)")
            
            # Status every 30s
            if int(elapsed) % 30 == 0 and elapsed > 0:
                completed = sum(1 for r in self.runs.values() if r.status == AgentRunStatus.COMPLETE)
                active = len(active_runs)
                print(f"\n[{elapsed:.1f}s] 📊 {completed}/{len(self.runs)} complete, {active} active")
            
            await asyncio.sleep(check_interval)
    
    def _get_incomplete_runs(self) -> List[AgentRun]:
        """Get runs that are not complete."""
        return [
            r for r in self.runs.values() 
            if r.status not in (AgentRunStatus.COMPLETE, AgentRunStatus.FAILED, 
                               AgentRunStatus.CANCELLED, AgentRunStatus.DISCARDED)
        ]
    
    async def _ai_analyze_and_decide(
        self,
        runs: List[AgentRun],
        elapsed: float,
        extended_timeout: float,
        min_required: Optional[int]
    ):
        """Use AI to analyze and make decisions."""
        completed_count = sum(1 for r in self.runs.values() if r.status == AgentRunStatus.COMPLETE)
        
        # Build analysis prompt
        analysis = f"""You are an orchestration AI managing {len(self.runs)} agent runs.

Current Status:
- Completed: {completed_count}
- Incomplete: {len(runs)}
- Elapsed: {elapsed:.1f}s / {extended_timeout:.1f}s max
- Min required: {min_required or 'all'}

Incomplete Agents:
"""
        
        for run in runs:
            analysis += f"\n{run.agent_run_id} ({run.specialization}):"
            analysis += f"\n  - Elapsed: {run.elapsed_seconds:.1f}s"
            analysis += f"\n  - API Status: {run.api_status}"
            analysis += f"\n  - Checks: {run.check_count}"
        
        analysis += f"""

For EACH incomplete agent, decide ONE action:
1. wait_longer - Still processing, wait more
2. discard - Stuck/failed, proceed without it
3. proceed_without - Have enough results

Return ONLY a JSON object like:
{{"123": "wait_longer", "456": "discard"}}

Only the JSON, no other text."""

        print(f"\n🤖 Asking AI for decisions...")
        
        # Create debug agent to make decision
        decision_id = self._create_agent_run(analysis)
        
        if decision_id:
            # Wait for decision (60s max)
            decision_start = time.time()
            while time.time() - decision_start < 60:
                decision_response = self._get_agent_run_status(decision_id)
                
                if decision_response and decision_response.get("status") == "complete":
                    decision_text = decision_response.get("response", "{}")
                    
                    # Parse JSON
                    try:
                        json_start = decision_text.find("{")
                        json_end = decision_text.rfind("}") + 1
                        if json_start >= 0 and json_end > json_start:
                            decisions = json.loads(decision_text[json_start:json_end])
                            
                            # Apply decisions
                            for run_id_str, action_str in decisions.items():
                                run_id = int(run_id_str)
                                if run_id in self.runs:
                                    action = DecisionAction(action_str)
                                    self.runs[run_id].decision = action
                                    
                                    self.decisions.append({
                                        "agent_run_id": run_id,
                                        "action": action.value,
                                        "timestamp": datetime.now().isoformat()
                                    })
                                    
                                    print(f"   📌 {run_id}: {action.value}")
                        
                    except (json.JSONDecodeError, ValueError) as e:
                        print(f"   ⚠️  JSON parse failed: {e}")
                        # Fallback
                        for run in runs:
                            if run.elapsed_seconds > 400:
                                run.decision = DecisionAction.DISCARD
                            else:
                                run.decision = DecisionAction.WAIT_LONGER
                    
                    break
                
                await asyncio.sleep(2)
        else:
            # Fallback decisions
            print(f"   ⚠️  AI decision failed, using fallback logic")
            for run in runs:
                if run.elapsed_seconds > 400:
                    run.decision = DecisionAction.DISCARD
                else:
                    run.decision = DecisionAction.WAIT_LONGER
    
    async def _execute_decisions(self, runs: List[AgentRun], remaining_time: float):
        """Execute decisions."""
        # Discard marked runs
        for run in runs:
            if run.decision in (DecisionAction.DISCARD, DecisionAction.PROCEED_WITHOUT):
                run.status = AgentRunStatus.DISCARDED
                print(f"   🗑️  Discarded {run.agent_run_id}")
        
        # Wait for others
        wait_runs = [r for r in runs if r.decision == DecisionAction.WAIT_LONGER]
        
        if wait_runs and remaining_time > 0:
            print(f"\n⏱️  Waiting up to {remaining_time:.1f}s for {len(wait_runs)} agents...")
            await self._monitor_agents(remaining_time, 3.0)
    
    def _aggregate_results(self, total_time: float) -> OrchestrationResult:
        """Aggregate final results."""
        completed = [r for r in self.runs.values() if r.status == AgentRunStatus.COMPLETE]
        failed = [r for r in self.runs.values() if r.status == AgentRunStatus.FAILED]
        discarded = [r for r in self.runs.values() if r.status == AgentRunStatus.DISCARDED]
        
        responses = [r.response for r in completed if r.response]
        
        print(f"\n✅ Completed: {len(completed)}")
        print(f"❌ Failed: {len(failed)}")
        print(f"🗑️  Discarded: {len(discarded)}")
        print(f"⏱️  Total: {total_time:.1f}s ({total_time/60:.1f} min)")
        
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

