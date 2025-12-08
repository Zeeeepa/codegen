#!/usr/bin/env python3
"""
Run Self-Improvement Loop on Codegen Repository

This script continuously analyzes, improves, benchmarks, and integrates
changes to the codebase using multi-agent orchestration.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from codegen.orchestration import SelfImprovementLoop


async def main():
    """Run the self-improvement loop."""
    print("🚀 Starting Self-Improvement Loop for Codegen Repository")
    print("="*80)
    print("Target: Optimize multi-agent orchestration system")
    print("Goal: <60s per agent, >90% success rate, production-ready CICD loop")
    print("="*80)
    
    loop = SelfImprovementLoop(
        repo_path=".",
        target_files=["src/codegen/orchestration.py"]
    )
    
    results = await loop.run_improvement_cycle(max_iterations=3)
    
    print("\n\n" + "="*80)
    print("📊 FINAL RESULTS")
    print("="*80)
    
    print(f"\nIterations completed: {len(results['iterations'])}")
    print(f"Improvements applied: {len(results['improvements_applied'])}")
    
    if results['improvements_applied']:
        print("\n✅ Applied improvements:")
        for improvement in results['improvements_applied']:
            print(f"  - {improvement}")
    
    print("\n📈 Performance Metrics:")
    for metric in results['metrics']:
        print(f"\n  Iteration {metric['iteration']}:")
        print(f"    Time: {metric['execution_time_seconds']:.1f}s")
        print(f"    Success Rate: {metric['agent_success_rate']:.0%}")
        print(f"    Quality Score: {metric['response_quality_score']}/10")
    
    print("\n" + "="*80)
    print("✅ Self-Improvement Loop Complete!")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(main())

