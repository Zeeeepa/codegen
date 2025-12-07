"""Tests for council orchestrator."""

from unittest.mock import MagicMock, Mock, patch

import pytest

from codegen.council.models import AgentConfig, CouncilConfig
from codegen.council.orchestrator import CouncilOrchestrator


@pytest.fixture
def mock_agent_task():
    """Create a mock AgentTask."""
    task = Mock()
    task.id = 123
    task.status = "COMPLETE"
    task.result = {"content": "Mock response content"}
    task.web_url = "https://codegen.com/agent/run/123"
    return task


@pytest.fixture
def mock_agent(mock_agent_task):
    """Create a mock Agent class."""
    with patch("codegen.council.orchestrator.Agent") as MockAgent:
        mock_instance = Mock()
        mock_instance.run.return_value = mock_agent_task
        MockAgent.return_value = mock_instance
        yield MockAgent


def test_council_config_defaults():
    """Test CouncilConfig defaults."""
    agents = [AgentConfig(model="gpt-4o")]
    config = CouncilConfig(agents=agents)
    
    assert config.num_candidates == 3
    assert config.enable_ranking is True
    assert config.synthesis_model == "claude-3-5-sonnet-20241022"
    assert config.tournament_threshold == 20


def test_orchestrator_initialization():
    """Test CouncilOrchestrator initialization."""
    agents = [AgentConfig(model="gpt-4o")]
    config = CouncilConfig(agents=agents)
    
    orchestrator = CouncilOrchestrator(
        token="test-token",
        org_id=123,
        config=config,
    )
    
    assert orchestrator.token == "test-token"
    assert orchestrator.org_id == 123
    assert orchestrator.config == config


def test_parse_ranking_from_text():
    """Test parsing of ranking text."""
    orchestrator = CouncilOrchestrator(
        token="test-token",
        org_id=123,
        config=CouncilConfig(agents=[AgentConfig(model="gpt-4o")]),
    )
    
    ranking_text = """
    Response A is good but has issues.
    Response B is better.
    Response C is the best.
    
    FINAL RANKING:
    1. Response C
    2. Response B
    3. Response A
    """
    
    parsed = orchestrator._parse_ranking_from_text(ranking_text)
    assert parsed == ["Response C", "Response B", "Response A"]


def test_parse_ranking_fallback():
    """Test parsing falls back gracefully when format is off."""
    orchestrator = CouncilOrchestrator(
        token="test-token",
        org_id=123,
        config=CouncilConfig(agents=[AgentConfig(model="gpt-4o")]),
    )
    
    # Missing FINAL RANKING header
    ranking_text = """
    Response A is mentioned here.
    Response B is also mentioned.
    """
    
    parsed = orchestrator._parse_ranking_from_text(ranking_text)
    assert "Response A" in parsed
    assert "Response B" in parsed


def test_build_synthesis_prompt():
    """Test synthesis prompt building."""
    from codegen.council.models import CandidateResponse
    
    orchestrator = CouncilOrchestrator(
        token="test-token",
        org_id=123,
        config=CouncilConfig(agents=[AgentConfig(model="gpt-4o")]),
    )
    
    candidates = [
        CandidateResponse(
            agent_run_id=1,
            model="gpt-4o",
            content="Response 1",
        ),
        CandidateResponse(
            agent_run_id=2,
            model="claude-3-5-sonnet",
            content="Response 2",
        ),
    ]
    
    prompt = orchestrator._build_synthesis_prompt(
        "What is AI?",
        candidates,
        [],
    )
    
    assert "What is AI?" in prompt
    assert "Response 1" in prompt
    assert "Response 2" in prompt
    assert "synthesize" in prompt.lower()


def test_calculate_aggregate_rankings():
    """Test aggregate ranking calculation."""
    from codegen.council.models import RankingResult
    
    orchestrator = CouncilOrchestrator(
        token="test-token",
        org_id=123,
        config=CouncilConfig(agents=[AgentConfig(model="gpt-4o")]),
    )
    
    rankings = [
        RankingResult(
            judge_model="gpt-4o",
            agent_run_id=1,
            ranking_text="FINAL RANKING:\n1. Response A\n2. Response B",
            parsed_ranking=["Response A", "Response B"],
        ),
        RankingResult(
            judge_model="claude-3-5-sonnet",
            agent_run_id=2,
            ranking_text="FINAL RANKING:\n1. Response B\n2. Response A",
            parsed_ranking=["Response B", "Response A"],
        ),
    ]
    
    label_to_model = {
        "Response A": "model-1",
        "Response B": "model-2",
    }
    
    aggregate = orchestrator._calculate_aggregate_rankings(rankings, label_to_model)
    
    # Both models should have average rank of 1.5 (got 1st once, 2nd once)
    assert len(aggregate) == 2
    assert all(r["average_rank"] == 1.5 for r in aggregate)


@pytest.mark.skip(reason="Integration test - requires live API")
def test_full_council_run():
    """Integration test for full council run (requires API access)."""
    agents = [
        AgentConfig(model="gpt-4o"),
        AgentConfig(model="claude-3-5-sonnet-20241022"),
    ]
    
    config = CouncilConfig(
        agents=agents,
        num_candidates=1,  # Keep it small for testing
        enable_ranking=False,  # Skip ranking for speed
    )
    
    orchestrator = CouncilOrchestrator(
        token="your-api-token",
        org_id=123,
        config=config,
    )
    
    result = orchestrator.run("What is 2+2?", poll_interval=2.0)
    
    assert result.stage1_candidates
    assert result.stage3_synthesis
    assert result.stage3_synthesis.content

