"""
Infinity CICD Loop System

A self-improving continuous research and development system that:
1. Researches improvements
2. Analyzes solutions  
3. Applies findings
4. Benchmarks results
5. Integrates if better
6. Loops infinitely

Based on the Infinity CICD Loop concept - continuous autonomous improvement.
"""

import asyncio
import json
import os
import sqlite3
import time
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional

from codegen.agents.agent import Agent, AgentTask
from codegen.agent_profiles import AgentProfileManager, AgentProfile

try:
    from codegen.infinity_loop_demo import get_demo_response
except ImportError:
    get_demo_response = None


# ============================================================================
# CONFIGURATION
# ============================================================================

CODEGEN_API_KEY = os.environ.get("CODEGEN_API_KEY", "")
CODEGEN_ORG_ID = int(os.environ.get("CODEGEN_ORG_ID", "323"))
MAX_FIX_ITERATIONS = 5
IMPROVEMENT_THRESHOLD = 0.05  # 5% improvement required
STATE_DB_PATH = Path("~/.codegen/infinity_loop.db").expanduser()
DEMO_MODE = os.environ.get("INFINITY_LOOP_DEMO_MODE", "true").lower() == "true"


# ============================================================================
# DATA MODELS
# ============================================================================

class LoopStage(Enum):
    """Stages in the infinity loop."""
    RESEARCH = "research"
    ANALYZE = "analyze"
    IMPLEMENT = "implement"
    TEST = "test"
    FIX = "fix"
    BENCHMARK = "benchmark"
    INTEGRATE = "integrate"
    COMPLETE = "complete"
    FAILED = "failed"


@dataclass
class LoopExecution:
    """Represents a single loop execution."""
    loop_id: str
    stage: LoopStage
    iteration: int
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    
    def __post_init__(self):
        """Set start_time to now if not provided."""
        if self.start_time is None:
            self.start_time = datetime.now()
    
    # Stage outputs
    research_report: Optional[str] = None
    analysis_report: Optional[str] = None
    pr_number: Optional[int] = None
    test_report: Optional[str] = None
    benchmark_report: Optional[str] = None
    integration_decision: Optional[bool] = None
    
    # Metrics
    baseline_metrics: Optional[Dict] = None
    new_metrics: Optional[Dict] = None
    improvement_pct: Optional[float] = None
    
    # Error tracking
    error_count: int = 0
    last_error: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        d = asdict(self)
        d['stage'] = self.stage.value
        d['start_time'] = self.start_time.isoformat()
        d['end_time'] = self.end_time.isoformat() if self.end_time else None
        return d


# ============================================================================
# STATE PERSISTENCE
# ============================================================================

class LoopStateManager:
    """Manages persistent state for infinity loop executions."""
    
    def __init__(self, db_path: Path = STATE_DB_PATH):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Initialize SQLite database."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS loop_executions (
                loop_id TEXT PRIMARY KEY,
                stage TEXT NOT NULL,
                iteration INTEGER NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT,
                research_report TEXT,
                analysis_report TEXT,
                pr_number INTEGER,
                test_report TEXT,
                benchmark_report TEXT,
                integration_decision INTEGER,
                baseline_metrics TEXT,
                new_metrics TEXT,
                improvement_pct REAL,
                error_count INTEGER DEFAULT 0,
                last_error TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
    
    def save_execution(self, execution: LoopExecution):
        """Save or update a loop execution."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO loop_executions (
                loop_id, stage, iteration, start_time, end_time,
                research_report, analysis_report, pr_number, test_report,
                benchmark_report, integration_decision, baseline_metrics,
                new_metrics, improvement_pct, error_count, last_error,
                updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (
            execution.loop_id,
            execution.stage.value,
            execution.iteration,
            execution.start_time.isoformat(),
            execution.end_time.isoformat() if execution.end_time else None,
            execution.research_report,
            execution.analysis_report,
            execution.pr_number,
            execution.test_report,
            execution.benchmark_report,
            1 if execution.integration_decision else 0 if execution.integration_decision is not None else None,
            json.dumps(execution.baseline_metrics) if execution.baseline_metrics else None,
            json.dumps(execution.new_metrics) if execution.new_metrics else None,
            execution.improvement_pct,
            execution.error_count,
            execution.last_error
        ))
        
        conn.commit()
        conn.close()
    
    def get_execution(self, loop_id: str) -> Optional[LoopExecution]:
        """Retrieve a loop execution by ID."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM loop_executions WHERE loop_id = ?", (loop_id,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        return LoopExecution(
            loop_id=row[0],
            stage=LoopStage(row[1]),
            iteration=row[2],
            start_time=datetime.fromisoformat(row[3]),
            end_time=datetime.fromisoformat(row[4]) if row[4] else None,
            research_report=row[5],
            analysis_report=row[6],
            pr_number=row[7],
            test_report=row[8],
            benchmark_report=row[9],
            integration_decision=bool(row[10]) if row[10] is not None else None,
            baseline_metrics=json.loads(row[11]) if row[11] else None,
            new_metrics=json.loads(row[12]) if row[12] else None,
            improvement_pct=row[13],
            error_count=row[14],
            last_error=row[15]
        )
    
    def list_executions(self, limit: int = 100) -> List[LoopExecution]:
        """List recent loop executions."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM loop_executions 
            ORDER BY start_time DESC 
            LIMIT ?
        """, (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        executions = []
        for row in rows:
            executions.append(LoopExecution(
                loop_id=row[0],
                stage=LoopStage(row[1]),
                iteration=row[2],
                start_time=datetime.fromisoformat(row[3]),
                end_time=datetime.fromisoformat(row[4]) if row[4] else None,
                research_report=row[5],
                analysis_report=row[6],
                pr_number=row[7],
                test_report=row[8],
                benchmark_report=row[9],
                integration_decision=bool(row[10]) if row[10] is not None else None,
                baseline_metrics=json.loads(row[11]) if row[11] else None,
                new_metrics=json.loads(row[12]) if row[12] else None,
                improvement_pct=row[13],
                error_count=row[14],
                last_error=row[15]
            ))
        
        return executions


# ============================================================================
# AGENT EXECUTORS
# ============================================================================

class InfinityLoopAgent:
    """Base agent executor for infinity loop stages."""
    
    def __init__(self, api_key: str = CODEGEN_API_KEY, org_id: int = CODEGEN_ORG_ID, profile: Optional[AgentProfile] = None):
        """
        Initialize agent executor.
        
        Args:
            api_key: Codegen API key
            org_id: Organization ID
            profile: Optional AgentProfile with instructions/rules
        """
        self.agent = Agent(token=api_key, org_id=org_id)
        self.profile = profile
    
    def _format_prompt(self, base_prompt: str) -> str:
        """
        Format prompt with profile instructions if available.
        
        Args:
            base_prompt: Base prompt/query
            
        Returns:
            Formatted prompt with profile instructions injected
        """
        if self.profile:
            return self.profile.format_instructions(base_prompt)
        return base_prompt
    
    async def execute(self, prompt: str, timeout: int = 300) -> str:
        """Execute agent with prompt and return result."""
        # Format prompt with profile instructions if available
        formatted_prompt = self._format_prompt(prompt)
        
        # Demo mode: Return mock responses instantly
        if DEMO_MODE:
            await asyncio.sleep(1)  # Simulate some processing
            return self._generate_demo_response(formatted_prompt)
        
        task = await asyncio.get_event_loop().run_in_executor(None, self.agent.run, formatted_prompt)
        
        # Poll for completion
        elapsed = 0
        poll_interval = 5
        
        while elapsed < timeout:
            await asyncio.get_event_loop().run_in_executor(None, task.refresh)
            
            if task.status in ["COMPLETE", "completed"]:
                # Handle both string and dict result types
                if isinstance(task.result, str):
                    return task.result
                elif isinstance(task.result, dict):
                    return task.result.get("content", str(task.result))
                else:
                    return str(task.result) if task.result else ""
            elif task.status in ["FAILED", "ERROR", "failed", "error"]:
                raise Exception(f"Agent execution failed: {task.status}")
            
            await asyncio.sleep(poll_interval)
            elapsed += poll_interval
        
        raise TimeoutError(f"Agent execution timed out after {timeout}s")
    
    def _generate_demo_response(self, prompt: str) -> str:
        """Generate mock responses for demo mode."""
        if get_demo_response:
            # Determine agent type from class name
            agent_type = self.__class__.__name__.replace("Agent", "").lower()
            return get_demo_response(agent_type, prompt)
        return "DEMO MODE: Mock response generated"


class ResearchAgent(InfinityLoopAgent):
    async def research(self, context: str) -> str:
        """Research potential improvements."""
        prompt = f"""You are a Research Agent for continuous system improvement.

Current Context:
{context}

Your Task:
1. Analyze current system state and identify areas for improvement
2. Research state-of-the-art solutions (academic papers, GitHub repos, blogs)
3. Identify specific optimization opportunities
4. Generate a detailed PRD (Product Requirements Document) for improvements

Output Format:
## Research Report

### Current State Analysis
[Analysis of current system]

### Improvement Opportunities
[List of potential improvements]

### Proposed Changes PRD
[Detailed PRD with requirements, implementation strategy, expected benefits]

### References
[Links to research sources]
"""
        return await self.execute(prompt)


class AnalysisAgent(InfinityLoopAgent):
    """Agent that analyzes proposed changes."""
    
    async def analyze(self, research_report: str) -> str:
        """Analyze feasibility and impact of proposed changes."""
        prompt = f"""You are an Analysis Agent validating proposed improvements.

Research Report:
{research_report}

Your Task:
1. Validate technical feasibility
2. Estimate implementation cost and effort
3. Identify potential risks and blockers
4. Design detailed implementation strategy
5. Define success metrics

Output Format:
## Analysis Report

### Feasibility Assessment
[Technical feasibility analysis]

### Impact Estimation
- Effort: [hours/days]
- Complexity: [low/medium/high]
- Risk Level: [low/medium/high]

### Implementation Plan
[Step-by-step implementation strategy]

### Success Metrics
[How to measure if improvement worked]

### Risks & Mitigation
[Potential issues and how to handle them]
"""
        return await self.execute(prompt)


class ImplementationAgent(InfinityLoopAgent):
    """Agent that implements changes."""
    
    async def implement(self, analysis_report: str, repo_context: str) -> str:
        """Generate code changes based on analysis."""
        prompt = f"""You are an Implementation Agent creating code changes.

Analysis Report:
{analysis_report}

Repository Context:
{repo_context}

Your Task:
1. Generate all necessary code changes
2. Write comprehensive tests
3. Create clear documentation
4. Output as a structured format ready for PR creation

Output Format:
## Implementation

### Code Changes
[List all file changes with full code]

### Tests Added
[Test code]

### Documentation
[README updates, docstrings, etc.]

### PR Description
[Clear description for pull request]
"""
        return await self.execute(prompt)


class TestAgent(InfinityLoopAgent):
    """Agent that runs tests and reports results."""
    
    async def test(self, pr_number: int) -> str:
        """Run full test suite on PR."""
        prompt = f"""You are a Test Agent validating PR #{pr_number}.

Your Task:
1. Run full test suite
2. Run performance benchmarks
3. Run security scans (trufflehog, etc.)
4. Check code quality (linting, type checking)
5. Generate comprehensive test report

Output Format:
## Test Report for PR #{pr_number}

### Unit Tests
- Passed: X/Y
- Failed: [list failures]

### Integration Tests  
- Passed: X/Y
- Failed: [list failures]

### Performance Tests
- Metrics: [performance numbers]

### Security Scan
- Issues Found: X
- Details: [security issues]

### Code Quality
- Linting: [pass/fail]
- Type Checking: [pass/fail]

### Overall Result
✅ PASS / ❌ FAIL

### Details
[Full test output if failures]
"""
        return await self.execute(prompt)


class FixAgent(InfinityLoopAgent):
    """Agent that fixes test failures."""
    
    async def fix(self, test_report: str, pr_number: int) -> str:
        """Analyze failures and generate fixes."""
        prompt = f"""You are a Fix Agent resolving test failures for PR #{pr_number}.

Test Report:
{test_report}

Your Task:
1. Analyze all test failures
2. Identify root causes
3. Generate fixes for each failure
4. Ensure fixes don't introduce new issues

Output Format:
## Fix Report

### Failure Analysis
[Root cause analysis for each failure]

### Proposed Fixes
[Code changes to fix issues]

### Testing Strategy
[How to verify fixes work]
"""
        return await self.execute(prompt)


class BenchmarkAgent(InfinityLoopAgent):
    """Agent that benchmarks changes against baseline."""
    
    async def benchmark(self, pr_number: int, baseline_metrics: Dict) -> str:
        """Compare new metrics vs baseline."""
        prompt = f"""You are a Benchmark Agent comparing PR #{pr_number} against baseline.

Baseline Metrics:
{json.dumps(baseline_metrics, indent=2)}

Your Task:
1. Run performance profiling on PR changes
2. Measure resource usage (CPU, memory, etc.)
3. Compare against baseline metrics
4. Calculate improvement percentages

Output Format:
## Benchmark Report for PR #{pr_number}

### Performance Metrics
- Metric 1: baseline vs new (% change)
- Metric 2: baseline vs new (% change)

### Resource Usage
- CPU: [comparison]
- Memory: [comparison]

### Overall Improvement
- Performance: +X%
- Efficiency: +Y%

### Regression Check
✅ No regressions / ❌ Regressions found

### Recommendation
INTEGRATE / DO NOT INTEGRATE
"""
        return await self.execute(prompt)


class IntegrationAgent(InfinityLoopAgent):
    """Agent that makes integration decisions."""
    
    async def decide(self, benchmark_report: str) -> Dict:
        """Decide whether to integrate changes."""
        prompt = f"""You are an Integration Agent making merge decisions.

Benchmark Report:
{benchmark_report}

Your Task:
1. Analyze benchmark results
2. Check for regressions
3. Validate improvement meets threshold (>5%)
4. Make integration decision with reasoning

Output ONLY valid JSON:
{{
    "decision": true/false,
    "improvement_pct": X.XX,
    "reasoning": "why integrate or not",
    "action": "merge_pr / close_pr",
    "learnings": ["key learning 1", "key learning 2"]
}}
"""
        result = await self.execute(prompt)
        
        # Extract JSON from response
        try:
            # Try to find JSON in response
            start = result.find('{')
            end = result.rfind('}') + 1
            if start >= 0 and end > start:
                return json.loads(result[start:end])
        except:
            pass
        
        # Fallback - parse manually
        return {
            "decision": False,
            "improvement_pct": 0.0,
            "reasoning": "Could not parse integration decision",
            "action": "close_pr",
            "learnings": ["Integration agent output was unparseable"]
        }


# ============================================================================
# INFINITY LOOP ORCHESTRATOR
# ============================================================================

class InfinityLoopOrchestrator:
    """Orchestrates the complete infinity CICD loop."""
    
    def __init__(
        self, 
        api_key: str = CODEGEN_API_KEY, 
        org_id: int = CODEGEN_ORG_ID,
        profiles: Optional[Dict[str, AgentProfile]] = None
    ):
        """
        Initialize orchestrator.
        
        Args:
            api_key: Codegen API key
            org_id: Organization ID
            profiles: Optional dict of agent profiles {"research": profile, ...}
        """
        self.api_key = api_key
        self.org_id = org_id
        self.profiles = profiles or {}
        
        # Initialize agents with optional profiles
        self.research_agent = ResearchAgent(
            api_key, org_id, 
            profile=self.profiles.get("research")
        )
        self.analysis_agent = AnalysisAgent(
            api_key, org_id,
            profile=self.profiles.get("analysis")
        )
        self.implementation_agent = ImplementationAgent(
            api_key, org_id,
            profile=self.profiles.get("implementation")
        )
        self.test_agent = TestAgent(
            api_key, org_id,
            profile=self.profiles.get("test")
        )
        self.fix_agent = FixAgent(
            api_key, org_id,
            profile=self.profiles.get("fix")
        )
        self.benchmark_agent = BenchmarkAgent(
            api_key, org_id,
            profile=self.profiles.get("benchmark")
        )
        self.integration_agent = IntegrationAgent(
            api_key, org_id,
            profile=self.profiles.get("integration")
        )
        
        # State manager
        self.state_mgr = LoopStateManager()
    
    async def run_loop(self, context: str, baseline_metrics: Optional[Dict] = None) -> LoopExecution:
        """Run a complete infinity loop iteration."""
        loop_id = f"loop_{int(time.time())}"
        execution = LoopExecution(
            loop_id=loop_id,
            stage=LoopStage.RESEARCH,
            iteration=1,
            start_time=datetime.now(),
            baseline_metrics=baseline_metrics or {}
        )
        
        try:
            # Stage 1: Research
            print(f"🔬 Stage 1: Research...")
            execution.research_report = await self.research_agent.research(context)
            execution.stage = LoopStage.ANALYZE
            self.state_mgr.save_execution(execution)
            
            # Stage 2: Analysis
            print(f"📊 Stage 2: Analysis...")
            execution.analysis_report = await self.analysis_agent.analyze(execution.research_report)
            execution.stage = LoopStage.IMPLEMENT
            self.state_mgr.save_execution(execution)
            
            # Stage 3: Implementation
            print(f"💻 Stage 3: Implementation...")
            implementation_result = await self.implementation_agent.implement(
                execution.analysis_report, context
            )
            # TODO: Actually create PR from implementation_result
            execution.pr_number = 999  # Placeholder
            execution.stage = LoopStage.TEST
            self.state_mgr.save_execution(execution)
            
            # Stage 4: Test (with fix loop)
            print(f"🧪 Stage 4: Test...")
            for fix_iteration in range(MAX_FIX_ITERATIONS):
                execution.test_report = await self.test_agent.test(execution.pr_number)
                
                # Check if tests passed
                if "✅ PASS" in execution.test_report or "PASS" in execution.test_report:
                    break
                
                # Tests failed - try to fix
                if fix_iteration < MAX_FIX_ITERATIONS - 1:
                    print(f"🔧 Stage 4.{fix_iteration+1}: Fix iteration {fix_iteration+1}...")
                    execution.stage = LoopStage.FIX
                    fix_result = await self.fix_agent.fix(execution.test_report, execution.pr_number)
                    # TODO: Apply fixes to PR
                    execution.error_count += 1
                    execution.last_error = f"Fix iteration {fix_iteration+1}"
                    self.state_mgr.save_execution(execution)
                else:
                    # Max iterations reached
                    execution.stage = LoopStage.FAILED
                    execution.last_error = f"Failed after {MAX_FIX_ITERATIONS} fix attempts"
                    execution.end_time = datetime.now()
                    self.state_mgr.save_execution(execution)
                    return execution
            
            execution.stage = LoopStage.BENCHMARK
            self.state_mgr.save_execution(execution)
            
            # Stage 5: Benchmark
            print(f"📈 Stage 5: Benchmark...")
            execution.benchmark_report = await self.benchmark_agent.benchmark(
                execution.pr_number, execution.baseline_metrics
            )
            execution.stage = LoopStage.INTEGRATE
            self.state_mgr.save_execution(execution)
            
            # Stage 6: Integration Decision
            print(f"🎯 Stage 6: Integration Decision...")
            decision = await self.integration_agent.decide(execution.benchmark_report)
            execution.integration_decision = decision["decision"]
            execution.improvement_pct = decision.get("improvement_pct", 0.0)
            
            if execution.integration_decision:
                print(f"✅ INTEGRATE - Improvement: {execution.improvement_pct}%")
                # TODO: Actually merge PR
            else:
                print(f"❌ DO NOT INTEGRATE - {decision.get('reasoning')}")
                # TODO: Close PR
            
            execution.stage = LoopStage.COMPLETE
            execution.end_time = datetime.now()
            self.state_mgr.save_execution(execution)
            
        except Exception as e:
            execution.stage = LoopStage.FAILED
            execution.last_error = str(e)
            execution.error_count += 1
            execution.end_time = datetime.now()
            self.state_mgr.save_execution(execution)
            raise
        
        return execution
    
    async def run_continuous_loop(self, initial_context: str, max_iterations: Optional[int] = None):
        """Run continuous improvement loop indefinitely (or until max_iterations)."""
        iteration = 0
        context = initial_context
        baseline_metrics = {}
        
        while max_iterations is None or iteration < max_iterations:
            iteration += 1
            print(f"\n{'='*80}")
            print(f"INFINITY LOOP ITERATION {iteration}")
            print(f"{'='*80}\n")
            
            try:
                execution = await self.run_loop(context, baseline_metrics)
                
                # Update baseline if improvement was integrated
                if execution.integration_decision and execution.new_metrics:
                    baseline_metrics = execution.new_metrics
                
                # Small delay between iterations
                await asyncio.sleep(10)
                
            except Exception as e:
                print(f"❌ Loop iteration {iteration} failed: {e}")
                # Continue to next iteration
                await asyncio.sleep(30)


# ============================================================================
# CLI INTERFACE
# ============================================================================

async def main():
    """Demo the infinity loop system."""
    print("=" * 80)
    print("INFINITY CICD LOOP SYSTEM")
    print("=" * 80)
    
    orchestrator = InfinityLoopOrchestrator()
    
    context = """
Current System: Codegen Python SDK multi-agent orchestration
Goal: Continuously improve performance, code quality, and features
Repository: Zeeeepa/codegen
"""
    
    # Run single loop
    print("\n▶️  Running single loop iteration...")
    execution = await orchestrator.run_loop(context)
    
    print(f"\n✅ Loop completed!")
    print(f"Loop ID: {execution.loop_id}")
    print(f"Final Stage: {execution.stage.value}")
    print(f"Integration Decision: {execution.integration_decision}")
    print(f"Improvement: {execution.improvement_pct}%")
    
    # To run continuous loop:
    # await orchestrator.run_continuous_loop(context, max_iterations=10)


if __name__ == "__main__":
    asyncio.run(main())
