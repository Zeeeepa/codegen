"""Data models for council orchestration."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class AgentConfig:
    """Configuration for a single agent in the council.
    
    Attributes:
        model: Model identifier to use for this agent
        role: Optional role description for the agent
        temperature: Sampling temperature (0-1, higher = more creative)
        prompt_variation: Optional prompt modification strategy
    """
    
    model: str
    role: Optional[str] = None
    temperature: float = 0.9
    prompt_variation: Optional[str] = None


@dataclass
class CouncilConfig:
    """Configuration for council execution.
    
    Attributes:
        agents: List of agent configurations to use
        num_candidates: Number of parallel candidates to generate per agent
        enable_ranking: Whether to run Stage 2 (peer ranking)
        synthesis_model: Model to use for final synthesis
        synthesis_temperature: Temperature for synthesis
        tournament_threshold: Use tournament synthesis if candidates exceed this
        group_size: Size of groups for tournament synthesis
    """
    
    agents: List[AgentConfig]
    num_candidates: int = 3
    enable_ranking: bool = True
    synthesis_model: str = "claude-3-5-sonnet-20241022"
    synthesis_temperature: float = 0.2
    tournament_threshold: int = 20
    group_size: int = 10


@dataclass
class CandidateResponse:
    """A single candidate response from an agent.
    
    Attributes:
        agent_run_id: ID of the codegen agent run
        model: Model that generated this response
        content: The response content
        web_url: URL to view the agent run
        metadata: Additional metadata from the run
    """
    
    agent_run_id: int
    model: str
    content: str
    web_url: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RankingResult:
    """Ranking of candidates by a judging agent.
    
    Attributes:
        judge_model: Model that performed the ranking
        agent_run_id: ID of the ranking agent run
        ranking_text: Full text of the ranking explanation
        parsed_ranking: Ordered list of response labels (best to worst)
        web_url: URL to view the ranking agent run
    """
    
    judge_model: str
    agent_run_id: int
    ranking_text: str
    parsed_ranking: List[str]
    web_url: Optional[str] = None


@dataclass
class SynthesisResult:
    """Final synthesized response.
    
    Attributes:
        agent_run_id: ID of the synthesis agent run
        model: Model that performed synthesis
        content: The final synthesized response
        web_url: URL to view the synthesis agent run
        method: Synthesis method used ('simple' or 'tournament')
    """
    
    agent_run_id: int
    model: str
    content: str
    web_url: Optional[str] = None
    method: str = "simple"


@dataclass
class CouncilResult:
    """Complete result from a council execution.
    
    Attributes:
        stage1_candidates: All candidate responses generated
        stage2_rankings: Rankings from peer evaluation (if enabled)
        stage3_synthesis: Final synthesized response
        aggregate_rankings: Aggregated ranking scores across all judges
        label_to_model: Mapping from anonymous labels to model names
    """
    
    stage1_candidates: List[CandidateResponse]
    stage2_rankings: Optional[List[RankingResult]] = None
    stage3_synthesis: Optional[SynthesisResult] = None
    aggregate_rankings: Optional[List[Dict[str, Any]]] = None
    label_to_model: Optional[Dict[str, str]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "stage1_candidates": [
                {
                    "agent_run_id": c.agent_run_id,
                    "model": c.model,
                    "content": c.content,
                    "web_url": c.web_url,
                }
                for c in self.stage1_candidates
            ],
            "stage2_rankings": [
                {
                    "judge_model": r.judge_model,
                    "agent_run_id": r.agent_run_id,
                    "ranking_text": r.ranking_text,
                    "parsed_ranking": r.parsed_ranking,
                    "web_url": r.web_url,
                }
                for r in (self.stage2_rankings or [])
            ],
            "stage3_synthesis": {
                "agent_run_id": self.stage3_synthesis.agent_run_id,
                "model": self.stage3_synthesis.model,
                "content": self.stage3_synthesis.content,
                "web_url": self.stage3_synthesis.web_url,
                "method": self.stage3_synthesis.method,
            } if self.stage3_synthesis else None,
            "aggregate_rankings": self.aggregate_rankings,
            "label_to_model": self.label_to_model,
        }

