"""
Phase 2 Test: Intelligent Multi-Agent Orchestration

This test demonstrates:
1. Launching 10 agents simultaneously
2. Tracking all run IDs
3. Monitoring progress intelligently
4. AI analyzing stuck agents
5. Making decisions (wait/skip/retry)
6. Gracefully handling partial completion
"""

import asyncio
import sys
import os
sys.path.insert(0, 'src')

from codegen.intelligent_orchestrator import IntelligentOrchestrator

CODEGEN_API_KEY = os.getenv("CODEGEN_API_KEY", "sk-92083737-4e5b-4a48-a2a1-f870a3a096a6")
CODEGEN_ORG_ID = int(os.getenv("CODEGEN_ORG_ID", "323"))


async def test_intelligent_orchestration():
    """Test with 10 agents - some fast, some slow."""
    
    print("\n" + "="*80)
    print("🧠 INTELLIGENT MULTI-AGENT ORCHESTRATION TEST")
    print("="*80)
    print("\nScenario: Launch 10 agents with varying complexity")
    print("Expected: System intelligently handles slow/stuck agents")
    print("="*80)
    
    # Create orchestrator
    orchestrator = IntelligentOrchestrator(
        api_key=CODEGEN_API_KEY,
        org_id=CODEGEN_ORG_ID
    )
    
    # Create 10 prompts with varying complexity
    prompts = [
        # Fast agents (should complete in ~120s)
        "Respond with just 'OK'",
        "What is 2+2?",
        "Say hello",
        
        # Medium agents (should complete in ~150s)
        "List 3 benefits of Python",
        "Explain what a function is in one sentence",
        "What is a variable?",
        
        # Slow agents (might take 180s+)
        "Analyze this code and suggest improvements:\ndef process(data):\n    return data",
        "Explain the concept of object-oriented programming briefly",
        
        # Very fast
        "Yes or no?",
        "Reply with 'DONE'"
    ]
    
    specializations = [
        "quick_response",
        "math",
        "greeting",
        "explanation",
        "definition",
        "definition",
        "code_analysis",
        "concept_explanation",
        "quick_response",
        "quick_response"
    ]
    
    # Run orchestration
    result = await orchestrator.orchestrate(
        prompts=prompts,
        specializations=specializations,
        initial_timeout=180.0,  # Wait 3 min initially
        extended_timeout=360.0,  # Max 6 min total
        check_interval=3.0,
        min_required=7  # Need at least 7 responses
    )
    
    # Display results
    print("\n" + "="*80)
    print("📊 FINAL RESULTS")
    print("="*80)
    
    print(f"\n✅ Completed: {result.completed}/{result.total_agents}")
    print(f"❌ Failed: {result.failed}")
    print(f"🗑️  Discarded: {result.discarded}")
    print(f"⏱️  Total time: {result.total_time:.1f}s ({result.total_time/60:.1f} min)")
    
    print(f"\n📝 Responses captured: {len(result.responses)}")
    for i, response in enumerate(result.responses[:3]):
        print(f"\n   Response {i+1}: {response[:100]}...")
    
    print(f"\n🧠 AI Decisions Made: {len(result.decisions_made)}")
    for decision in result.decisions_made:
        print(f"   - {decision['run_id']}: {decision['action']}")
    
    print("\n" + "="*80)
    print("🎯 TEST EVALUATION")
    print("="*80)
    
    # Evaluate success
    success_criteria = {
        "got_responses": result.completed >= 7,
        "made_decisions": len(result.decisions_made) > 0 if result.total_agents - result.completed > 0 else True,
        "completed_in_time": result.total_time < 360.0,
        "no_hard_failures": result.failed < 3
    }
    
    all_passed = all(success_criteria.values())
    
    print("\nCriteria:")
    for criterion, passed in success_criteria.items():
        status = "✅" if passed else "❌"
        print(f"  {status} {criterion}")
    
    if all_passed:
        print("\n🎉 TEST PASSED - Intelligent orchestration working!")
    else:
        print("\n⚠️  TEST PARTIAL - Some criteria not met")
    
    print("="*80)
    
    return result


async def main():
    result = await test_intelligent_orchestration()
    
    # Save detailed report
    report = {
        "total_agents": result.total_agents,
        "completed": result.completed,
        "failed": result.failed,
        "discarded": result.discarded,
        "total_time": result.total_time,
        "decisions": result.decisions_made,
        "agent_details": [
            {
                "run_id": r.run_id,
                "specialization": r.specialization,
                "status": r.status.value,
                "elapsed": r.elapsed_seconds,
                "response_length": len(r.response) if r.response else 0,
                "decision": r.decision.value if r.decision else None
            }
            for r in result.agent_runs
        ]
    }
    
    import json
    with open("test_02_report.json", "w") as f:
        json.dump(report, f, indent=2)
    
    print(f"\n💾 Detailed report saved to test_02_report.json")


if __name__ == "__main__":
    asyncio.run(main())

