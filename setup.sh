#!/bin/bash
# setup.sh - Initialize the Codegen SDK demo environment

set -e  # Exit on error

echo "🚀 Setting up Codegen SDK Demo Environment..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

# Check Python version
python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo "✓ Found Python $python_version"

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv .venv
else
    echo "✓ Virtual environment already exists"
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source .venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip --quiet

# Install the codegen package
echo "📥 Installing Codegen SDK..."
pip install -e . --quiet

# Create demo.py if it doesn't exist
if [ ! -f "demo.py" ]; then
    echo "📝 Creating demo.py file..."
    cat > demo.py << 'EOF'
"""
Codegen SDK Demo
-----------------
This demo shows how to use the Codegen SDK to interact with AI coding agents.
"""

import os
from codegen.agents.agent import Agent

def main():
    # Get credentials from environment variables
    org_id = os.getenv("CODEGEN_ORG_ID")
    token = os.getenv("CODEGEN_TOKEN")
    
    if not org_id or not token:
        print("❌ Error: Please set CODEGEN_ORG_ID and CODEGEN_TOKEN environment variables")
        print("\nGet your credentials from: https://codegen.com/token")
        print("\nSet them using:")
        print("  export CODEGEN_ORG_ID='your-org-id'")
        print("  export CODEGEN_TOKEN='your-api-token'")
        return
    
    print("🤖 Initializing Codegen Agent...")
    agent = Agent(org_id=org_id, token=token)
    
    # Example prompt
    prompt = "Create a simple Python function to calculate the factorial of a number"
    
    print(f"\n📤 Sending prompt: {prompt}")
    print("⏳ Running agent (this may take a moment)...\n")
    
    # Run the agent
    task = agent.run(prompt=prompt)
    
    print(f"📊 Initial Status: {task.status}")
    print(f"🆔 Task ID: {task.id}")
    
    # Refresh to get updated status
    print("\n🔄 Refreshing task status...")
    task.refresh()
    
    print(f"📊 Updated Status: {task.status}")
    
    # Display result if completed
    if task.status == "completed":
        print("\n✅ Task completed successfully!")
        print("\n" + "="*60)
        print("RESULT:")
        print("="*60)
        print(task.result)
    elif task.status == "failed":
        print("\n❌ Task failed")
    else:
        print(f"\n⏳ Task is still running. Current status: {task.status}")
        print("   Run this script again or check the Codegen dashboard")

if __name__ == "__main__":
    main()
EOF
    chmod +x demo.py
fi

# Create .env.example file
if [ ! -f ".env.example" ]; then
    echo "📝 Creating .env.example file..."
    cat > .env.example << 'EOF'
# Codegen API Credentials
# Get yours from: https://codegen.com/token

CODEGEN_ORG_ID=your-org-id-here
CODEGEN_TOKEN=your-api-token-here
EOF
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "📋 Next steps:"
echo "   1. Get your credentials from: https://codegen.com/token"
echo "   2. Export your credentials:"
echo "      export CODEGEN_ORG_ID='your-org-id'"
echo "      export CODEGEN_TOKEN='your-api-token'"
echo "   3. Run the demo:"
echo "      ./start.sh"
echo ""
echo "   Or use the all-in-one script:"
echo "      ./all.sh"
echo ""

