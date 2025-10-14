#!/bin/bash
# send_request.sh - Send a custom request to the Codegen API

set -e  # Exit on error

echo "📤 Codegen API Request Tool"
echo ""

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "❌ Virtual environment not found. Please run ./setup.sh first"
    exit 1
fi

# Activate virtual environment
source .venv/bin/activate

# Check if credentials are set
if [ -z "$CODEGEN_ORG_ID" ] || [ -z "$CODEGEN_TOKEN" ]; then
    echo "❌ Error: CODEGEN_ORG_ID and CODEGEN_TOKEN are not set"
    echo ""
    echo "Please set your credentials:"
    echo "  export CODEGEN_ORG_ID='your-org-id'"
    echo "  export CODEGEN_TOKEN='your-api-token'"
    echo ""
    echo "Get them from: https://codegen.com/token"
    exit 1
fi

# Get prompt from command line argument or ask for it
if [ -z "$1" ]; then
    echo "Usage: $0 \"Your prompt here\""
    echo ""
    echo "Example:"
    echo "  $0 \"Create a function to validate email addresses\""
    echo ""
    read -p "Enter your prompt: " PROMPT
else
    PROMPT="$*"
fi

if [ -z "$PROMPT" ]; then
    echo "❌ Error: No prompt provided"
    exit 1
fi

# Create a temporary Python script to send the request
cat > /tmp/codegen_request.py << EOF
import os
from codegen.agents.agent import Agent

org_id = os.getenv("CODEGEN_ORG_ID")
token = os.getenv("CODEGEN_TOKEN")
prompt = """$PROMPT"""

print("🤖 Initializing Codegen Agent...")
agent = Agent(org_id=org_id, token=token)

print(f"\n📤 Sending prompt: {prompt}")
print("⏳ Running agent...\n")

task = agent.run(prompt=prompt)

print(f"📊 Status: {task.status}")
print(f"🆔 Task ID: {task.id}")
print()

# Wait and refresh
import time
max_wait = 60  # Maximum wait time in seconds
wait_time = 0
interval = 5

while task.status not in ["completed", "failed", "cancelled"] and wait_time < max_wait:
    print(f"⏳ Waiting... ({wait_time}s / {max_wait}s)")
    time.sleep(interval)
    wait_time += interval
    task.refresh()
    print(f"📊 Status: {task.status}")

if task.status == "completed":
    print("\n✅ Task completed successfully!")
    print("\n" + "="*60)
    print("RESULT:")
    print("="*60)
    print(task.result)
elif task.status == "failed":
    print("\n❌ Task failed")
    if hasattr(task, 'error'):
        print(f"Error: {task.error}")
else:
    print(f"\n⏳ Task is still running after {max_wait}s")
    print(f"   Task ID: {task.id}")
    print("   Check the Codegen dashboard for updates")
EOF

# Run the request
python /tmp/codegen_request.py

# Clean up
rm /tmp/codegen_request.py

echo ""
echo "✅ Request completed!"

