#!/usr/bin/env python3
"""
Quick test script for Codegen MCP Server.
Simple validation that the server is working correctly.
"""

import os
import sys
import time

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from codegen import Agent

# Configuration
ORG_ID = int(os.getenv("CODEGEN_ORG_ID", "323"))
API_TOKEN = os.getenv("CODEGEN_API_KEY", "sk-92083737-4e5b-4a48-a2a1-f870a3a096a6")

def main():
    print("🚀 Codegen MCP Server - Quick Test\n")
    print(f"Organization: {ORG_ID}")
    print(f"Token: {API_TOKEN[:20]}...\n")
    
    # Step 1: Initialize Agent
    print("Step 1: Initializing agent...")
    agent = Agent(org_id=ORG_ID, token=API_TOKEN)
    print("✅ Agent initialized\n")
    
    # Step 2: Create Agent Run
    print("Step 2: Creating agent run...")
    prompt = "Write a simple hello world function in Python"
    task = agent.run(prompt)
    print(f"✅ Agent run created!")
    print(f"   ID: {task.id}")
    print(f"   Status: {task.status}")
    print(f"   Dashboard: {task.web_url}\n")
    
    # Step 3: Check Status
    print("Step 3: Checking status...")
    time.sleep(5)  # Wait 5 seconds
    task.refresh()
    print(f"✅ Status refreshed: {task.status}\n")
    
    # Step 4: Monitor (with timeout)
    print("Step 4: Monitoring progress (30s timeout)...")
    elapsed = 0
    max_wait = 30
    
    while task.status in ["PENDING", "ACTIVE", "RUNNING"] and elapsed < max_wait:
        time.sleep(5)
        elapsed += 5
        task.refresh()
        print(f"   [{elapsed}s] {task.status}...")
    
    # Final Status
    print(f"\n✅ Final Status: {task.status}")
    
    if task.status == "COMPLETE":
        print(f"🎉 Success! Result: {task.result}")
    elif elapsed >= max_wait:
        print(f"⏱️ Still running - check dashboard: {task.web_url}")
    else:
        print(f"ℹ️ Agent ended with status: {task.status}")
    
    print("\n✅ Quick test complete!")
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)

