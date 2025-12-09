"""
Phase 1 Test: Diagnostic - Find WHY agents timeout

This test will:
1. Call a single agent with minimal input
2. Time each operation
3. Capture the raw output
4. Identify where the 300s goes
"""

import asyncio
import time
import sys
sys.path.insert(0, 'src')

from codegen.agents.agent import Agent
import os

CODEGEN_API_KEY = os.getenv("CODEGEN_API_KEY", "sk-92083737-4e5b-4a48-a2a1-f870a3a096a6")
CODEGEN_ORG_ID = int(os.getenv("CODEGEN_ORG_ID", "323"))


async def test_minimal_agent():
    """Test with absolutely minimal input."""
    print("="*80)
    print("TEST 1: MINIMAL AGENT CALL")
    print("="*80)
    
    agent = Agent(token=CODEGEN_API_KEY, org_id=CODEGEN_ORG_ID)
    
    # Super minimal prompt
    prompt = "Hello, respond with 'OK'"
    
    print(f"\n📝 Prompt: {prompt}")
    print(f"⏱️  Starting timer...")
    
    start = time.time()
    
    try:
        # Create task
        print(f"\n[{time.time() - start:.1f}s] Running agent...")
        task = agent.run(prompt=prompt)
        print(f"[{time.time() - start:.1f}s] Task created: {task.id}")
        
        # Poll for completion
        print(f"[{time.time() - start:.1f}s] Polling for completion...")
        
        poll_count = 0
        elapsed = 0
        poll_interval = 3
        timeout_limit = 120  # 2 minute timeout for minimal test
        
        while elapsed < timeout_limit:
            poll_count += 1
            task.refresh()
            status = task.status
            
            if poll_count % 10 == 0:  # Log every 10 polls (30s)
                print(f"[{time.time() - start:.1f}s] Status: {status} (poll #{poll_count})")
            
            if status in ("COMPLETE", "FAILED", "CANCELLED", "completed", "failed", "cancelled"):
                break
            
            await asyncio.sleep(poll_interval)
            elapsed += poll_interval
        
        elapsed = time.time() - start
        print(f"\n[{elapsed:.1f}s] ✅ {status}")
        
        # Get response
        response = ""
        if status in ("COMPLETE", "completed"):
            response = task.result or ""
            print(f"\n📤 Response ({len(response)} chars):")
            print(f"   {response[:200]}...")
            
            # Save to file
            with open("test_output_minimal.txt", "w") as f:
                f.write(response)
            print(f"\n💾 Saved full response to test_output_minimal.txt")
        
        return {"elapsed": elapsed, "status": status, "response_len": len(response)}
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        return None


async def test_small_code_analysis():
    """Test with small code snippet."""
    print("\n\n" + "="*80)
    print("TEST 2: SMALL CODE ANALYSIS")
    print("="*80)
    
    agent = Agent(token=CODEGEN_API_KEY, org_id=CODEGEN_ORG_ID)
    
    # Small code snippet
    code = '''
def hello():
    print("Hello World")
'''
    
    prompt = f"""Analyze this code for improvements:

{code}

List 2-3 specific improvements. Keep response under 200 words."""
    
    print(f"\n📝 Prompt length: {len(prompt)} chars")
    print(f"⏱️  Starting timer...")
    
    start = time.time()
    
    try:
        print(f"\n[{time.time() - start:.1f}s] Running agent...")
        task = agent.run(prompt=prompt)
        print(f"[{time.time() - start:.1f}s] Task created: {task.id}")
        
        print(f"[{time.time() - start:.1f}s] Polling for completion...")
        
        poll_count = 0
        elapsed = 0
        poll_interval = 3
        timeout_limit = 180  # 3 minute timeout
        
        while elapsed < timeout_limit:
            poll_count += 1
            task.refresh()
            status = task.status
            
            if poll_count % 10 == 0:
                print(f"[{time.time() - start:.1f}s] Status: {status} (poll #{poll_count})")
            
            if status in ("COMPLETE", "FAILED", "CANCELLED", "completed", "failed", "cancelled"):
                break
            
            await asyncio.sleep(poll_interval)
            elapsed += poll_interval
        
        elapsed = time.time() - start
        print(f"\n[{elapsed:.1f}s] ✅ {status}")
        
        response = ""
        if status in ("COMPLETE", "completed"):
            response = task.result or ""
            print(f"\n📤 Response ({len(response)} chars):")
            print(f"   {response[:300]}...")
            
            with open("test_output_code_analysis.txt", "w") as f:
                f.write(response)
            print(f"\n💾 Saved full response to test_output_code_analysis.txt")
        
        return {"elapsed": elapsed, "status": status, "response_len": len(response)}
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        return None


async def main():
    print("\n🔬 DIAGNOSTIC TIMEOUT TESTS")
    print("="*80)
    print("Goal: Understand WHERE the time goes")
    print("="*80)
    
    # Test 1: Minimal
    result1 = await test_minimal_agent()
    
    # Test 2: Small code
    result2 = await test_small_code_analysis()
    
    # Summary
    print("\n\n" + "="*80)
    print("📊 SUMMARY")
    print("="*80)
    
    if result1:
        print(f"\n✅ Test 1 (Minimal): {result1['elapsed']:.1f}s - {result1['status']}")
        print(f"   Response: {result1['response_len']} chars")
    else:
        print(f"\n❌ Test 1 (Minimal): FAILED")
    
    if result2:
        print(f"\n✅ Test 2 (Code Analysis): {result2['elapsed']:.1f}s - {result2['status']}")
        print(f"   Response: {result2['response_len']} chars")
    else:
        print(f"\n❌ Test 2 (Code Analysis): FAILED")
    
    print("\n" + "="*80)
    print("🎯 CONCLUSION:")
    if result1 and result2:
        avg_time = (result1['elapsed'] + result2['elapsed']) / 2
        print(f"   Average completion time: {avg_time:.1f}s")
        if avg_time < 60:
            print(f"   ✅ Agents complete in reasonable time")
        else:
            print(f"   ⚠️  Agents are slow but completing")
    else:
        print(f"   ❌ Agents are timing out - need to reduce scope")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(main())
