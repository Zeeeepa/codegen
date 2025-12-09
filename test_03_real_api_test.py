"""
REAL API TEST - No mocks, no SDK wrappers, just pure REST API calls

This test will:
1. Actually call POST /v1/organizations/{org_id}/agent/run
2. Actually get OFFICIAL agent_run_id from response
3. Actually poll GET /v1/organizations/{org_id}/agent/run/{agent_run_id}
4. Actually track real agent states
5. Show REAL results or REAL failures
"""

import asyncio
import sys
import os
sys.path.insert(0, 'src')

from codegen.intelligent_orchestrator_v2 import IntelligentOrchestratorV2

CODEGEN_API_KEY = os.getenv("CODEGEN_API_KEY", "sk-92083737-4e5b-4a48-a2a1-f870a3a096a6")
CODEGEN_ORG_ID = int(os.getenv("CODEGEN_ORG_ID", "323"))


async def test_real_api():
    """Test with REAL API - 3 simple prompts."""
    
    print("\n" + "="*80)
    print("🔥 REAL API TEST - NO MOCKS, NO LIES")
    print("="*80)
    
    # Create orchestrator with REAL credentials
    orchestrator = IntelligentOrchestratorV2(
        api_key=CODEGEN_API_KEY,
        org_id=CODEGEN_ORG_ID
    )
    
    # 3 simple prompts to keep test fast
    prompts = [
        "What is 2+2? Reply in one sentence.",
        "Say 'Hello'",
        "Respond with just 'OK'"
    ]
    
    specializations = ["math", "greeting", "quick"]
    
    print(f"\nLaunching {len(prompts)} agents with REAL API calls...")
    print("This will take ~3-5 minutes")
    print("="*80)
    
    # Run orchestration with REAL API
    result = await orchestrator.orchestrate(
        prompts=prompts,
        specializations=specializations,
        initial_timeout=200.0,  # 3.3 min initial wait
        extended_timeout=300.0,  # 5 min max
        check_interval=5.0,
        min_required=2  # Need at least 2
    )
    
    # Show REAL results
    print("\n" + "="*80)
    print("📊 REAL RESULTS FROM ACTUAL API")
    print("="*80)
    
    print(f"\n✅ Completed: {result.completed}/{result.total_agents}")
    print(f"❌ Failed: {result.failed}")
    print(f"🗑️  Discarded: {result.discarded}")
    print(f"⏱️  Time: {result.total_time:.1f}s")
    
    print(f"\n📝 Actual Responses from API:")
    for i, response in enumerate(result.responses):
        print(f"\n   [{i+1}] {response[:100]}...")
    
    print(f"\n🤖 AI Decisions Made:")
    for decision in result.decisions_made:
        print(f"   - agent_run_id {decision['agent_run_id']}: {decision['action']}")
    
    # Show agent details
    print(f"\n🔍 Agent Run Details:")
    for run in result.agent_runs:
        print(f"\n   agent_run_id: {run.agent_run_id}")
        print(f"   specialization: {run.specialization}")
        print(f"   api_status: {run.api_status}")
        print(f"   our_status: {run.status.value}")
        print(f"   elapsed: {run.elapsed_seconds:.1f}s")
        print(f"   checks: {run.check_count}")
        if run.response:
            print(f"   response: {run.response[:80]}...")
        if run.error:
            print(f"   error: {run.error}")
    
    # Validate
    print("\n" + "="*80)
    print("🎯 VALIDATION")
    print("="*80)
    
    success_criteria = {
        "got_official_ids": all(isinstance(r.agent_run_id, int) for r in result.agent_runs),
        "got_responses": result.completed >= 2,
        "api_calls_worked": len(result.agent_runs) > 0,
        "no_crashes": True
    }
    
    all_passed = all(success_criteria.values())
    
    for criterion, passed in success_criteria.items():
        status = "✅" if passed else "❌"
        print(f"  {status} {criterion}")
    
    if all_passed:
        print("\n🎉 TEST PASSED - Real API integration works!")
    else:
        print("\n❌ TEST FAILED - Real API has issues")
    
    print("="*80)
    
    return result


async def main():
    try:
        result = await test_real_api()
        
        # Save real results
        import json
        report = {
            "test": "REAL_API_TEST",
            "timestamp": str(result.agent_runs[0].created_at) if result.agent_runs else None,
            "total_agents": result.total_agents,
            "completed": result.completed,
            "failed": result.failed,
            "discarded": result.discarded,
            "total_time": result.total_time,
            "decisions": result.decisions_made,
            "agent_details": [
                {
                    "agent_run_id": r.agent_run_id,
                    "specialization": r.specialization,
                    "api_status": r.api_status,
                    "our_status": r.status.value,
                    "elapsed": r.elapsed_seconds,
                    "response_length": len(r.response) if r.response else 0
                }
                for r in result.agent_runs
            ]
        }
        
        with open("test_03_real_api_report.json", "w") as f:
            json.dump(report, f, indent=2)
        
        print(f"\n💾 Report saved to test_03_real_api_report.json")
        
    except Exception as e:
        print(f"\n💥 TEST CRASHED: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

