"""Council orchestrator for multi-agent collaboration."""

import re
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Optional, Tuple

from codegen.agents.agent import Agent, AgentTask
from codegen.council.models import (
    AgentConfig,
    CandidateResponse,
    CouncilConfig,
    CouncilResult,
    RankingResult,
    SynthesisResult,
)
from codegen.shared.logging.get_logger import get_logger

logger = get_logger(__name__)


class CouncilOrchestrator:
    """Orchestrates multi-agent council execution with Codegen agents.
    
    Implements a 3-stage process:
    1. Stage 1: Generate N candidate responses from each agent/model
    2. Stage 2 (optional): Each agent ranks all candidates anonymously
    3. Stage 3: Synthesize final response from all candidates and rankings
    """
    
    def __init__(
        self,
        token: str,
        org_id: int,
        config: CouncilConfig,
        max_workers: int = 50,
    ):
        """Initialize council orchestrator.
        
        Args:
            token: Codegen API token
            org_id: Organization ID
            config: Council configuration
            max_workers: Max parallel workers for agent execution
        """
        self.token = token
        self.org_id = org_id
        self.config = config
        self.max_workers = max_workers
    
    def run(self, prompt: str, poll_interval: float = 5.0) -> CouncilResult:
        """Execute the full council process.
        
        Args:
            prompt: User's question/task
            poll_interval: Seconds between status polls for agent runs
            
        Returns:
            CouncilResult with all stages completed
        """
        logger.info(
            f"Starting council with {len(self.config.agents)} agents, "
            f"{self.config.num_candidates} candidates each"
        )
        
        # Stage 1: Generate candidates
        stage1_candidates = self._stage1_generate_candidates(prompt, poll_interval)
        
        if not stage1_candidates:
            raise RuntimeError("All candidate generations failed")
        
        logger.info(f"Stage 1 complete: {len(stage1_candidates)} candidates generated")
        
        # Stage 2: Rankings (optional)
        stage2_rankings = None
        aggregate_rankings = None
        label_to_model = None
        
        if self.config.enable_ranking:
            stage2_rankings, label_to_model = self._stage2_collect_rankings(
                prompt, stage1_candidates, poll_interval
            )
            aggregate_rankings = self._calculate_aggregate_rankings(
                stage2_rankings, label_to_model
            )
            logger.info(f"Stage 2 complete: {len(stage2_rankings)} rankings collected")
        
        # Stage 3: Synthesis
        method = "tournament" if len(stage1_candidates) > self.config.tournament_threshold else "simple"
        
        stage3_synthesis = self._stage3_synthesize(
            prompt,
            stage1_candidates,
            stage2_rankings or [],
            method,
            poll_interval,
        )
        logger.info(f"Stage 3 complete: Final synthesis using {method} method")
        
        return CouncilResult(
            stage1_candidates=stage1_candidates,
            stage2_rankings=stage2_rankings,
            stage3_synthesis=stage3_synthesis,
            aggregate_rankings=aggregate_rankings,
            label_to_model=label_to_model,
        )
    
    def _stage1_generate_candidates(
        self,
        prompt: str,
        poll_interval: float,
    ) -> List[CandidateResponse]:
        """Stage 1: Generate candidate responses from all agents."""
        # Calculate total runs: agents × candidates_per_agent
        total_runs = len(self.config.agents) * self.config.num_candidates
        
        logger.info(f"Stage 1: Launching {total_runs} agent runs")
        
        # Build all agent run configs
        run_configs = []
        for agent_config in self.config.agents:
            for _ in range(self.config.num_candidates):
                run_configs.append((agent_config.model, prompt))
        
        # Launch all runs in parallel
        tasks = self._launch_parallel_runs(run_configs)
        
        # Wait for completion
        results = self._wait_for_completion(tasks, poll_interval)
        
        # Convert to CandidateResponse objects
        candidates = []
        for task, (model, _) in zip(tasks, run_configs):
            status = self._get_task_status(task)
            if status and status.get("status") == "COMPLETE":
                result_content = status.get("result", {}).get("content", "")
                if result_content:
                    candidates.append(
                        CandidateResponse(
                            agent_run_id=task.id,
                            model=model,
                            content=result_content,
                            web_url=task.web_url,
                        )
                    )
        
        return candidates
    
    def _stage2_collect_rankings(
        self,
        original_prompt: str,
        candidates: List[CandidateResponse],
        poll_interval: float,
    ) -> Tuple[List[RankingResult], Dict[str, str]]:
        """Stage 2: Each agent ranks the anonymized candidates."""
        # Create anonymous labels (Response A, Response B, etc.)
        labels = [chr(65 + i) for i in range(len(candidates))]  # A, B, C, ...
        label_to_model = {
            f"Response {label}": cand.model
            for label, cand in zip(labels, candidates)
        }
        
        # Build ranking prompt
        ranking_prompt = self._build_ranking_prompt(original_prompt, candidates, labels)
        
        logger.info(f"Stage 2: Launching {len(self.config.agents)} ranking runs")
        
        # Launch ranking runs for each agent
        run_configs = [(agent.model, ranking_prompt) for agent in self.config.agents]
        tasks = self._launch_parallel_runs(run_configs)
        
        # Wait for completion
        self._wait_for_completion(tasks, poll_interval)
        
        # Parse rankings
        rankings = []
        for task, (model, _) in zip(tasks, run_configs):
            status = self._get_task_status(task)
            if status and status.get("status") == "COMPLETE":
                ranking_text = status.get("result", {}).get("content", "")
                if ranking_text:
                    parsed = self._parse_ranking_from_text(ranking_text)
                    rankings.append(
                        RankingResult(
                            judge_model=model,
                            agent_run_id=task.id,
                            ranking_text=ranking_text,
                            parsed_ranking=parsed,
                            web_url=task.web_url,
                        )
                    )
        
        return rankings, label_to_model
    
    def _stage3_synthesize(
        self,
        original_prompt: str,
        candidates: List[CandidateResponse],
        rankings: List[RankingResult],
        method: str,
        poll_interval: float,
    ) -> SynthesisResult:
        """Stage 3: Synthesize final response."""
        if method == "tournament":
            return self._tournament_synthesis(
                original_prompt, candidates, rankings, poll_interval
            )
        else:
            return self._simple_synthesis(
                original_prompt, candidates, rankings, poll_interval
            )
    
    def _simple_synthesis(
        self,
        original_prompt: str,
        candidates: List[CandidateResponse],
        rankings: List[RankingResult],
        poll_interval: float,
    ) -> SynthesisResult:
        """Simple synthesis: combine all candidates in one shot."""
        synthesis_prompt = self._build_synthesis_prompt(
            original_prompt, candidates, rankings
        )
        
        logger.info("Stage 3: Running simple synthesis")
        
        # Launch synthesis run
        agent = Agent(token=self.token, org_id=self.org_id)
        task = agent.run(synthesis_prompt)
        
        # Wait for completion
        self._wait_for_single_task(task, poll_interval)
        
        # Get result
        status = self._get_task_status(task)
        content = ""
        if status and status.get("status") == "COMPLETE":
            content = status.get("result", {}).get("content", "")
        
        return SynthesisResult(
            agent_run_id=task.id,
            model=self.config.synthesis_model,
            content=content,
            web_url=task.web_url,
            method="simple",
        )
    
    def _tournament_synthesis(
        self,
        original_prompt: str,
        candidates: List[CandidateResponse],
        rankings: List[RankingResult],
        poll_interval: float,
    ) -> SynthesisResult:
        """Tournament synthesis: group → synth groups → synth winners."""
        logger.info(
            f"Stage 3: Running tournament synthesis with {len(candidates)} candidates, "
            f"group_size={self.config.group_size}"
        )
        
        # Split into groups
        groups = [
            candidates[i : i + self.config.group_size]
            for i in range(0, len(candidates), self.config.group_size)
        ]
        
        logger.info(f"Created {len(groups)} groups for tournament")
        
        # Synthesize each group
        group_winners = []
        for group_idx, group in enumerate(groups):
            logger.info(f"Synthesizing group {group_idx + 1}/{len(groups)}")
            group_prompt = self._build_synthesis_prompt(original_prompt, group, [])
            
            agent = Agent(token=self.token, org_id=self.org_id)
            task = agent.run(group_prompt)
            self._wait_for_single_task(task, poll_interval)
            
            status = self._get_task_status(task)
            if status and status.get("status") == "COMPLETE":
                content = status.get("result", {}).get("content", "")
                if content:
                    group_winners.append(
                        CandidateResponse(
                            agent_run_id=task.id,
                            model=self.config.synthesis_model,
                            content=content,
                            web_url=task.web_url,
                        )
                    )
        
        # Final synthesis across group winners
        logger.info(f"Final synthesis across {len(group_winners)} group winners")
        final_prompt = self._build_synthesis_prompt(original_prompt, group_winners, rankings)
        
        agent = Agent(token=self.token, org_id=self.org_id)
        task = agent.run(final_prompt)
        self._wait_for_single_task(task, poll_interval)
        
        status = self._get_task_status(task)
        content = ""
        if status and status.get("status") == "COMPLETE":
            content = status.get("result", {}).get("content", "")
        
        return SynthesisResult(
            agent_run_id=task.id,
            model=self.config.synthesis_model,
            content=content,
            web_url=task.web_url,
            method="tournament",
        )
    
    def _launch_parallel_runs(
        self,
        run_configs: List[Tuple[str, str]],
    ) -> List[AgentTask]:
        """Launch multiple agent runs in parallel.
        
        Args:
            run_configs: List of (model, prompt) tuples
            
        Returns:
            List of AgentTask objects
        """
        tasks = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_config = {}
            
            for model, prompt in run_configs:
                agent = Agent(token=self.token, org_id=self.org_id)
                future = executor.submit(agent.run, prompt)
                future_to_config[future] = (model, prompt)
            
            for future in as_completed(future_to_config):
                try:
                    task = future.result()
                    tasks.append(task)
                except Exception as e:
                    logger.error(f"Failed to launch agent run: {e}")
        
        return tasks
    
    def _wait_for_completion(
        self,
        tasks: List[AgentTask],
        poll_interval: float,
    ) -> List[AgentTask]:
        """Wait for all tasks to complete."""
        pending = set(tasks)
        
        while pending:
            completed_in_round = set()
            
            for task in pending:
                task.refresh()
                if task.status in ("COMPLETE", "FAILED", "STOPPED"):
                    completed_in_round.add(task)
            
            pending -= completed_in_round
            
            if pending:
                time.sleep(poll_interval)
        
        return tasks
    
    def _wait_for_single_task(self, task: AgentTask, poll_interval: float):
        """Wait for a single task to complete."""
        while task.status not in ("COMPLETE", "FAILED", "STOPPED"):
            time.sleep(poll_interval)
            task.refresh()
    
    def _get_task_status(self, task: AgentTask) -> Optional[Dict[str, Any]]:
        """Get status dict for a task."""
        return {
            "id": task.id,
            "status": task.status,
            "result": task.result,
            "web_url": task.web_url,
        }
    
    def _build_ranking_prompt(
        self,
        original_prompt: str,
        candidates: List[CandidateResponse],
        labels: List[str],
    ) -> str:
        """Build prompt for ranking candidates."""
        responses_text = "\n\n".join(
            f"<Response {label}>\n{cand.content}\n</Response {label}>"
            for label, cand in zip(labels, candidates)
        )
        
        return f"""You are evaluating different responses to the following question:

Question: {original_prompt}

Here are the responses from different models (anonymized):

{responses_text}

Your task:
1. First, evaluate each response individually. For each response, explain what it does well and what it does poorly.
2. Then, at the very end of your response, provide a final ranking.

IMPORTANT: Your final ranking MUST be formatted EXACTLY as follows:
- Start with the line "FINAL RANKING:" (all caps, with colon)
- Then list the responses from best to worst as a numbered list
- Each line should be: number, period, space, then ONLY the response label (e.g., "1. Response A")
- Do not add any other text or explanations in the ranking section

Example format:

[Your evaluation of each response...]

FINAL RANKING:
1. Response C
2. Response A
3. Response B

Now provide your evaluation and ranking:"""
    
    def _build_synthesis_prompt(
        self,
        original_prompt: str,
        candidates: List[CandidateResponse],
        rankings: List[RankingResult],
    ) -> str:
        """Build prompt for synthesizing final answer."""
        candidates_text = "\n\n".join(
            f"<Candidate {i + 1}>\n{cand.content}\n</Candidate {i + 1}>"
            for i, cand in enumerate(candidates)
        )
        
        rankings_text = ""
        if rankings:
            rankings_text = "\n\nPeer Rankings:\n" + "\n\n".join(
                f"Judge {i + 1}:\n{rank.ranking_text}"
                for i, rank in enumerate(rankings)
            )
        
        return f"""You are an expert editor synthesizing multiple candidate responses.

Original Question: {original_prompt}

Candidate Responses:
{candidates_text}{rankings_text}

Your task is to synthesize ONE best answer by:
- Merging the strengths of multiple candidates
- Correcting any errors or inconsistencies
- Removing repetition and redundancy
- Being decisive and clear

Do not mention the candidates, synthesis process, or ranking. Just provide the best final answer."""
    
    def _parse_ranking_from_text(self, ranking_text: str) -> List[str]:
        """Parse FINAL RANKING section from response."""
        if "FINAL RANKING:" in ranking_text:
            parts = ranking_text.split("FINAL RANKING:")
            if len(parts) >= 2:
                ranking_section = parts[1]
                numbered_matches = re.findall(r"\d+\.\s*Response [A-Z]", ranking_section)
                if numbered_matches:
                    return [
                        re.search(r"Response [A-Z]", m).group()
                        for m in numbered_matches
                    ]
                matches = re.findall(r"Response [A-Z]", ranking_section)
                return matches
        
        matches = re.findall(r"Response [A-Z]", ranking_text)
        return matches
    
    def _calculate_aggregate_rankings(
        self,
        rankings: List[RankingResult],
        label_to_model: Dict[str, str],
    ) -> List[Dict[str, Any]]:
        """Calculate aggregate rankings across all judges."""
        model_positions: Dict[str, List[int]] = defaultdict(list)
        
        for ranking in rankings:
            for position, label in enumerate(ranking.parsed_ranking, start=1):
                if label in label_to_model:
                    model_name = label_to_model[label]
                    model_positions[model_name].append(position)
        
        aggregate = []
        for model, positions in model_positions.items():
            if positions:
                avg_rank = sum(positions) / len(positions)
                aggregate.append(
                    {
                        "model": model,
                        "average_rank": round(avg_rank, 2),
                        "rankings_count": len(positions),
                    }
                )
        
        aggregate.sort(key=lambda x: x["average_rank"])
        return aggregate

