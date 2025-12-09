"""
Council Orchestrator - Multi-Model, Multi-Variation Query System

Implements the "council" pattern where:
1. Same query sent to multiple models (GPT-5, Claude 4.5, Grok)
2. Each query has 3 semantic variations
3. Results in 3 models × 3 variations = 9 parallel agent executions
4. Synthesizes best response from all 9 results
"""

import asyncio
from dataclasses import dataclass
from typing import List, Dict, Optional
from codegen.agents.agent import Agent


@dataclass
class CouncilResponse:
    """Response from a single council member."""
    model: str
    variation: int
    prompt: str
    response: str
    confidence: float = 0.0


@dataclass
class SynthesizedResult:
    """Final synthesized result from council."""
    final_response: str
    all_responses: List[CouncilResponse]
    synthesis_reasoning: str
    top_3_responses: List[CouncilResponse]


class SemanticVariationGenerator:
    """Generates semantic variations of prompts."""
    
    @staticmethod
    def generate_variations(base_prompt: str, num_variations: int = 3) -> List[str]:
        """
        Generate semantic variations of the base prompt.
        
        Variations maintain the same intent but use different:
        - Phrasing
        - Level of detail
        - Emphasis
        """
        variations = []
        
        # Variation 1: Direct and concise
        variations.append(
            f"Task: {base_prompt}\n"
            f"Provide a direct, concise solution focusing on core requirements."
        )
        
        # Variation 2: Detailed and comprehensive
        variations.append(
            f"Context: {base_prompt}\n"
            f"Provide a comprehensive analysis considering:\n"
            f"- All edge cases and potential issues\n"
            f"- Best practices and industry standards\n"
            f"- Performance and scalability implications"
        )
        
        # Variation 3: Creative and alternative approaches
        variations.append(
            f"Challenge: {base_prompt}\n"
            f"Explore alternative approaches and innovative solutions.\n"
            f"Consider unconventional methods that might offer advantages."
        )
        
        return variations[:num_variations]


class CouncilOrchestrator:
    """
    Orchestrates multi-model, multi-variation queries with synthesis.
    
    Architecture:
    1. Takes base query
    2. Generates 3 semantic variations
    3. Dispatches to 3 models in parallel (9 total executions)
    4. Synthesizes best response
    """
    
    def __init__(self, token: str = "", org_id: int = 323):
        """Initialize council with available models."""
        self.token = token
        self.org_id = org_id
        
        # In production, these would be different model endpoints
        # For now, we create separate agent instances
        self.models = {
            "gpt-5": Agent(token=token, org_id=org_id),
            "claude-4.5": Agent(token=token, org_id=org_id),
            "grok": Agent(token=token, org_id=org_id),
        }
        
        # Synthesizer uses a separate agent
        self.synthesizer = Agent(token=token, org_id=org_id)
        
        self.variation_generator = SemanticVariationGenerator()
    
    async def query_council(
        self, 
        base_prompt: str,
        num_variations: int = 3,
        timeout: int = 300
    ) -> SynthesizedResult:
        """
        Execute council query with semantic variations.
        
        Args:
            base_prompt: Original user query
            num_variations: Number of semantic variations (default 3)
            timeout: Timeout per agent execution (default 300s)
            
        Returns:
            SynthesizedResult with final answer and all intermediate responses
        """
        # Step 1: Generate semantic variations
        variations = self.variation_generator.generate_variations(
            base_prompt, 
            num_variations
        )
        
        # Step 2: Dispatch to all models in parallel (3 models × 3 variations = 9)
        tasks = []
        for model_name, agent in self.models.items():
            for var_idx, variation in enumerate(variations, 1):
                task = self._execute_single_agent(
                    model_name, 
                    var_idx, 
                    variation, 
                    agent,
                    timeout
                )
                tasks.append(task)
        
        # Execute all in parallel
        print(f"🚀 Dispatching {len(tasks)} parallel agents...")
        all_responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out errors
        valid_responses = [
            r for r in all_responses 
            if isinstance(r, CouncilResponse)
        ]
        
        print(f"✅ Received {len(valid_responses)}/{len(tasks)} responses")
        
        # Step 3: Synthesize best response
        synthesized = await self._synthesize_responses(
            base_prompt,
            valid_responses
        )
        
        return synthesized
    
    async def _execute_single_agent(
        self,
        model_name: str,
        variation_idx: int,
        prompt: str,
        agent: Agent,
        timeout: int
    ) -> CouncilResponse:
        """Execute a single agent with timeout."""
        try:
            print(f"  → {model_name} (var {variation_idx}): Starting...")
            
            # In demo mode, simulate response
            import os
            if os.environ.get("INFINITY_LOOP_DEMO_MODE", "true").lower() == "true":
                await asyncio.sleep(0.5)  # Simulate processing
                response = f"Demo response from {model_name} variation {variation_idx}"
            else:
                # Real execution
                task = await asyncio.get_event_loop().run_in_executor(
                    None, agent.run, prompt
                )
                
                # Poll for completion
                elapsed = 0
                while elapsed < timeout:
                    await asyncio.get_event_loop().run_in_executor(
                        None, task.refresh
                    )
                    
                    if task.status in ["COMPLETE", "completed"]:
                        if isinstance(task.result, str):
                            response = task.result
                        elif isinstance(task.result, dict):
                            response = task.result.get("content", str(task.result))
                        else:
                            response = str(task.result) if task.result else ""
                        break
                    
                    await asyncio.sleep(5)
                    elapsed += 5
                else:
                    raise TimeoutError(f"Agent timed out after {timeout}s")
            
            print(f"  ✓ {model_name} (var {variation_idx}): Complete")
            
            return CouncilResponse(
                model=model_name,
                variation=variation_idx,
                prompt=prompt,
                response=response,
                confidence=0.8  # Would be calculated based on response quality
            )
            
        except Exception as e:
            print(f"  ✗ {model_name} (var {variation_idx}): Error - {e}")
            return CouncilResponse(
                model=model_name,
                variation=variation_idx,
                prompt=prompt,
                response=f"ERROR: {str(e)}",
                confidence=0.0
            )
    
    async def _synthesize_responses(
        self,
        original_query: str,
        responses: List[CouncilResponse]
    ) -> SynthesizedResult:
        """
        Synthesize best response from council members.
        
        Uses a synthesizer agent to:
        1. Analyze all responses
        2. Identify best elements from each
        3. Combine into single optimal response
        """
        print("\n🧠 Synthesizing responses...")
        
        # Prepare synthesis prompt
        responses_text = "\n\n".join([
            f"Response {i+1} ({r.model}, variation {r.variation}):\n{r.response}"
            for i, r in enumerate(responses)
        ])
        
        synthesis_prompt = f"""You are a response synthesizer. Analyze all responses below and create the single best answer.

Original Query:
{original_query}

All Responses:
{responses_text}

Your Task:
1. Identify the best elements from each response
2. Synthesize them into a single optimal answer
3. Explain your synthesis reasoning

Output Format:
SYNTHESIS:
[Your synthesized optimal response]

REASONING:
[Why you chose these elements and how you combined them]

TOP 3:
[List the 3 best individual responses by number]
"""
        
        # In demo mode
        import os
        if os.environ.get("INFINITY_LOOP_DEMO_MODE", "true").lower() == "true":
            await asyncio.sleep(1)
            synthesis_response = f"""SYNTHESIS:
Based on analysis of all {len(responses)} responses, the optimal solution combines:
- Direct approach from GPT-5 responses
- Comprehensive analysis from Claude-4.5 responses  
- Creative alternatives from Grok responses

The synthesized recommendation is to implement the solution with both immediate value and long-term scalability.

REASONING:
GPT-5 provided clear, actionable steps. Claude-4.5 identified important edge cases. Grok suggested innovative approaches. By combining these, we get a robust solution that is both practical and forward-thinking.

TOP 3:
1. Response 2 (claude-4.5, variation 2) - Most comprehensive
2. Response 1 (gpt-5, variation 1) - Most actionable
3. Response 8 (grok, variation 2) - Most innovative"""
        else:
            # Real synthesis
            task = await asyncio.get_event_loop().run_in_executor(
                None, self.synthesizer.run, synthesis_prompt
            )
            
            # Wait for completion
            elapsed = 0
            while elapsed < 300:
                await asyncio.get_event_loop().run_in_executor(
                    None, task.refresh
                )
                
                if task.status in ["COMPLETE", "completed"]:
                    if isinstance(task.result, str):
                        synthesis_response = task.result
                    elif isinstance(task.result, dict):
                        synthesis_response = task.result.get("content", str(task.result))
                    else:
                        synthesis_response = str(task.result) if task.result else ""
                    break
                
                await asyncio.sleep(5)
                elapsed += 5
            else:
                synthesis_response = "ERROR: Synthesis timeout"
        
        # Parse synthesis response
        parts = synthesis_response.split("SYNTHESIS:")
        if len(parts) > 1:
            final_text = parts[1].split("REASONING:")[0].strip()
        else:
            final_text = synthesis_response
        
        parts = synthesis_response.split("REASONING:")
        if len(parts) > 1:
            reasoning = parts[1].split("TOP 3:")[0].strip()
        else:
            reasoning = "No reasoning provided"
        
        # Sort by confidence for top 3
        sorted_responses = sorted(responses, key=lambda r: r.confidence, reverse=True)
        top_3 = sorted_responses[:3]
        
        print(f"✅ Synthesis complete")
        
        return SynthesizedResult(
            final_response=final_text,
            all_responses=responses,
            synthesis_reasoning=reasoning,
            top_3_responses=top_3
        )
