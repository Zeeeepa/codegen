"""
Pro Mode Engine for generating multiple PRD candidates and synthesizing the best result
Similar to OpenAI's Pro Mode but using Codegen API
"""

import asyncio
import json
import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed

from ...sdk.client import CodegenClient
from .prd_template import PRDTemplate


@dataclass
class ProModeRequest:
    prompt: str
    num_gens: int
    temperature: float = 0.9
    org_id: int = None
    repo_id: int = None
    model: str = "claude-3-5-sonnet-20241022"


@dataclass
class ProModeResponse:
    final: str
    candidates: List[str]
    metadata: Dict[str, Any]


@dataclass
class ProModeConfig:
    max_workers: int = 10
    tournament_threshold: int = 20
    group_size: int = 5
    timeout_seconds: int = 300


class ProModeEngine:
    """
    Pro Mode Engine that generates multiple AI responses and synthesizes the best result
    """
    
    def __init__(self, codegen_client: CodegenClient, config: Optional[ProModeConfig] = None):
        self.codegen_client = codegen_client
        self.config = config or ProModeConfig()
    
    async def execute_pro_mode(self, request: ProModeRequest) -> ProModeResponse:
        """
        Execute Pro Mode generation with multiple candidates and synthesis
        """
        start_time = time.time()
        
        # Generate multiple candidates in parallel
        candidates = await self._generate_candidates(request)
        
        # Synthesize the best response
        synthesis_start = time.time()
        final_result = await self._synthesize_responses(candidates, request)
        synthesis_time = time.time() - synthesis_start
        
        return ProModeResponse(
            final=final_result,
            candidates=candidates,
            metadata={
                "total_time": time.time() - start_time,
                "successful_gens": len(candidates),
                "synthesis_time": synthesis_time,
                "tournament_used": len(candidates) > self.config.tournament_threshold
            }
        )
    
    async def _generate_candidates(self, request: ProModeRequest) -> List[str]:
        """Generate multiple candidate responses in parallel"""
        
        # Create tasks for parallel execution
        tasks = []
        for i in range(request.num_gens):
            task = self._generate_single_candidate(request, i)
            tasks.append(task)
        
        # Execute with limited concurrency
        semaphore = asyncio.Semaphore(self.config.max_workers)
        
        async def bounded_task(task, index):
            async with semaphore:
                try:
                    return await task
                except Exception as e:
                    print(f"Candidate {index} failed: {e}")
                    return None
        
        # Run all tasks
        bounded_tasks = [bounded_task(task, i) for i, task in enumerate(tasks)]
        results = await asyncio.gather(*bounded_tasks, return_exceptions=True)
        
        # Filter successful results
        candidates = []
        for result in results:
            if isinstance(result, str) and result.strip():
                candidates.append(result)
            elif isinstance(result, Exception):
                print(f"Task failed with exception: {result}")
        
        return candidates
    
    async def _generate_single_candidate(self, request: ProModeRequest, index: int) -> str:
        """Generate a single candidate response"""
        try:
            # Create agent run
            agent_run = await self.codegen_client.create_agent_run(
                org_id=request.org_id,
                prompt=request.prompt,
                repo_id=request.repo_id,
                model=request.model,
                temperature=request.temperature
            )
            
            # Poll for completion
            result = await self._poll_agent_completion(
                request.org_id, 
                agent_run.id,
                timeout=self.config.timeout_seconds
            )
            
            return result.get("output", "")
            
        except Exception as e:
            print(f"Candidate {index} generation failed: {e}")
            raise
    
    async def _poll_agent_completion(self, org_id: int, agent_run_id: str, timeout: int = 300) -> Dict[str, Any]:
        """Poll for agent run completion"""
        start_time = time.time()
        poll_interval = 5  # seconds
        
        while time.time() - start_time < timeout:
            try:
                agent_run = await self.codegen_client.get_agent_run(org_id, agent_run_id)
                
                if agent_run.status == "COMPLETE":
                    return agent_run.result or {"output": ""}
                elif agent_run.status == "FAILED":
                    raise Exception(f"Agent run failed: {agent_run.error}")
                
                # Wait before next poll
                await asyncio.sleep(poll_interval)
                
            except Exception as e:
                print(f"Polling error: {e}")
                await asyncio.sleep(poll_interval)
        
        raise Exception(f"Agent run timed out after {timeout} seconds")
    
    async def _synthesize_responses(self, candidates: List[str], request: ProModeRequest) -> str:
        """Synthesize the best response from candidates"""
        if not candidates:
            raise Exception("No successful candidates to synthesize")
        
        if len(candidates) == 1:
            return candidates[0]
        
        # Use tournament approach for large numbers
        if len(candidates) > self.config.tournament_threshold:
            return await self._tournament_synthesis(candidates, request)
        else:
            return await self._simple_synthesis(candidates, request)
    
    async def _tournament_synthesis(self, candidates: List[str], request: ProModeRequest) -> str:
        """Tournament-style synthesis for large candidate sets"""
        
        # Group candidates into chunks
        groups = self._chunk_array(candidates, self.config.group_size)
        
        # Synthesize each group in parallel
        group_tasks = [
            self._synthesize_group(group, request) 
            for group in groups
        ]
        
        group_winners = await asyncio.gather(*group_tasks)
        
        # Final synthesis of group winners
        return await self._synthesize_group(group_winners, request)
    
    async def _simple_synthesis(self, candidates: List[str], request: ProModeRequest) -> str:
        """Simple synthesis for smaller candidate sets"""
        return await self._synthesize_group(candidates, request)
    
    async def _synthesize_group(self, candidates: List[str], request: ProModeRequest) -> str:
        """Synthesize a group of candidates"""
        synthesis_prompt = self._build_synthesis_prompt(candidates, request.prompt)
        
        # Create synthesis request
        synthesis_request = ProModeRequest(
            prompt=synthesis_prompt,
            num_gens=1,  # Only need one synthesis result
            temperature=0.7,  # Lower temperature for synthesis
            org_id=request.org_id,
            repo_id=request.repo_id,
            model=request.model
        )
        
        # Generate synthesis (single candidate)
        synthesis_candidates = await self._generate_candidates(synthesis_request)
        
        if not synthesis_candidates:
            # Fallback to first candidate if synthesis fails
            return candidates[0]
        
        return synthesis_candidates[0]
    
    def _build_synthesis_prompt(self, candidates: List[str], original_prompt: str) -> str:
        """Build prompt for synthesizing multiple candidates"""
        
        candidates_text = "\n\n---CANDIDATE SEPARATOR---\n\n".join(
            f"CANDIDATE {i+1}:\n{candidate}" 
            for i, candidate in enumerate(candidates)
        )
        
        return f"""
# Synthesis Task

You are tasked with synthesizing the best possible response from multiple AI-generated candidates.

## Original Request
{original_prompt}

## Candidates to Synthesize
{candidates_text}

## Instructions
1. Analyze all candidates for their strengths and weaknesses
2. Identify the best ideas, approaches, and content from each
3. Synthesize a final response that:
   - Combines the best elements from all candidates
   - Maintains consistency and coherence
   - Addresses the original request comprehensively
   - Is better than any individual candidate

## Output
Provide the synthesized response that represents the best combination of all candidates.
Do not include meta-commentary about the synthesis process - just provide the final result.
"""
    
    def _chunk_array(self, array: List[Any], chunk_size: int) -> List[List[Any]]:
        """Split array into chunks of specified size"""
        return [
            array[i:i + chunk_size] 
            for i in range(0, len(array), chunk_size)
        ]
    
    # Synchronous wrapper methods for backward compatibility
    def execute_pro_mode_sync(self, request: ProModeRequest) -> ProModeResponse:
        """Synchronous wrapper for execute_pro_mode"""
        return asyncio.run(self.execute_pro_mode(request))
    
    def generate_prd_with_pro_mode(
        self, 
        user_prompt: str, 
        org_id: int, 
        repo_id: int,
        num_generations: int = 10,
        temperature: float = 0.9
    ) -> str:
        """
        Generate a PRD using Pro Mode
        
        Args:
            user_prompt: User's request for the PRD
            org_id: Organization ID
            repo_id: Repository ID  
            num_generations: Number of candidate generations
            temperature: Generation temperature
            
        Returns:
            Synthesized PRD content
        """
        
        # Build comprehensive PRD generation prompt
        prd_prompt = self._build_prd_generation_prompt(user_prompt)
        
        # Create Pro Mode request
        request = ProModeRequest(
            prompt=prd_prompt,
            num_gens=num_generations,
            temperature=temperature,
            org_id=org_id,
            repo_id=repo_id
        )
        
        # Execute Pro Mode
        response = self.execute_pro_mode_sync(request)
        
        return response.final
    
    def _build_prd_generation_prompt(self, user_prompt: str) -> str:
        """Build comprehensive PRD generation prompt"""
        return f"""
# Generate Comprehensive PRD using Base PRP Template v2

## User Request
{user_prompt}

## Requirements
Generate a complete PRD following the Base PRP Template v2 structure:

1. **Goal**: Clear, specific end state
2. **Why**: Business value and user impact  
3. **What**: User-visible behavior and technical requirements
4. **Success Criteria**: Measurable outcomes
5. **Context**: Documentation, codebase trees, gotchas
6. **Implementation**: Data models, tasks, pseudocode, integration points
7. **Validation**: Syntax checks, unit tests, integration tests, checklist

## Output Format
Provide a complete, structured PRD in JSON format:

{{
  "title": "PRD Title",
  "goal": "What needs to be built...",
  "why": ["Business value 1", "Business value 2"],
  "what": "User-visible behavior...",
  "successCriteria": ["Measurable outcome 1", "Measurable outcome 2"],
  "context": {{
    "documentation": [],
    "codebaseTree": "Current structure...",
    "desiredTree": "Desired structure...",
    "gotchas": ["Known issue 1", "Known issue 2"]
  }},
  "implementation": {{
    "dataModels": "Data model definitions...",
    "tasks": [],
    "pseudocode": "Implementation pseudocode...",
    "integrationPoints": []
  }},
  "validation": {{
    "syntaxChecks": ["ruff check .", "mypy ."],
    "unitTests": ["pytest tests/"],
    "integrationTests": ["pytest tests/integration/"],
    "checklist": ["All tests pass", "No linting errors"]
  }}
}}

Make the PRD comprehensive, actionable, and ready for implementation.
Focus on creating a PRD that can be directly implemented by AI agents.
"""

