# Codegen SDK Demo Scripts

This directory contains convenience scripts to quickly set up and use the Codegen SDK.

## 📁 Scripts Overview

### 🔧 `setup.sh`
**Purpose:** Initialize the development environment

**What it does:**
- Checks Python installation (requires Python 3.8+)
- Creates a virtual environment (`.venv`)
- Installs the Codegen SDK
- Creates a `demo.py` file with example code
- Creates `.env.example` for credential reference

**Usage:**
```bash
./setup.sh
```

**When to use:** Run this once when first setting up the project, or when you need to reset your environment.

---

### ▶️ `start.sh`
**Purpose:** Run the demo application

**What it does:**
- Activates the virtual environment
- Validates that credentials are set
- Runs the `demo.py` script
- Shows task status and results

**Usage:**
```bash
# First, set your credentials:
export CODEGEN_ORG_ID='your-org-id'
export CODEGEN_TOKEN='your-api-token'

# Then run:
./start.sh
```

**When to use:** After setup is complete and you want to run the demo.

---

### 📤 `send_request.sh`
**Purpose:** Send custom prompts to the Codegen API

**What it does:**
- Accepts a custom prompt as an argument
- Sends it to the Codegen API
- Waits for completion (up to 60 seconds)
- Displays the result

**Usage:**
```bash
# With a prompt as argument:
./send_request.sh "Create a function to validate email addresses"

# Or run without arguments to be prompted:
./send_request.sh
```

**Examples:**
```bash
./send_request.sh "Write a Python function to calculate Fibonacci numbers"
./send_request.sh "Create a REST API endpoint for user authentication"
./send_request.sh "Generate unit tests for a sorting algorithm"
```

**When to use:** When you want to quickly test the API with custom prompts.

---

### 🚀 `all.sh`
**Purpose:** Complete setup and run workflow (all-in-one)

**What it does:**
1. Runs `setup.sh` to initialize the environment
2. Checks that credentials are configured
3. Runs `start.sh` to execute the demo
4. Shows a summary and next steps

**Usage:**
```bash
# Set credentials first:
export CODEGEN_ORG_ID='your-org-id'
export CODEGEN_TOKEN='your-api-token'

# Run everything:
./all.sh
```

**When to use:** Perfect for first-time setup or when you want to run everything in one command.

---

## 🔑 Getting Credentials

1. Visit [codegen.com/token](https://codegen.com/token)
2. Sign in or create an account
3. Copy your Organization ID and API Token
4. Set them as environment variables:

```bash
export CODEGEN_ORG_ID='your-org-id-here'
export CODEGEN_TOKEN='your-api-token-here'
```

**Tip:** Add these to your `~/.bashrc` or `~/.zshrc` to persist them across sessions:

```bash
echo 'export CODEGEN_ORG_ID="your-org-id-here"' >> ~/.bashrc
echo 'export CODEGEN_TOKEN="your-api-token-here"' >> ~/.bashrc
source ~/.bashrc
```

---

## 🎯 Quick Start Guide

### Option 1: All-in-One (Recommended for first time)

```bash
# 1. Get credentials from https://codegen.com/token
# 2. Set environment variables
export CODEGEN_ORG_ID='your-org-id'
export CODEGEN_TOKEN='your-api-token'

# 3. Run everything
./all.sh
```

### Option 2: Step-by-Step

```bash
# Step 1: Setup environment
./setup.sh

# Step 2: Set credentials
export CODEGEN_ORG_ID='your-org-id'
export CODEGEN_TOKEN='your-api-token'

# Step 3: Run demo
./start.sh

# Step 4 (Optional): Try custom prompts
./send_request.sh "Your custom prompt here"
```

---

## 📋 Workflow Diagram

```
┌─────────────┐
│  setup.sh   │  ← Initialize environment
└──────┬──────┘
       │
       ├── Creates virtual environment
       ├── Installs dependencies
       ├── Creates demo.py
       └── Creates .env.example
       
┌─────────────┐
│  start.sh   │  ← Run the demo
└──────┬──────┘
       │
       ├── Activates venv
       ├── Validates credentials
       └── Runs demo.py
       
┌─────────────────┐
│ send_request.sh │  ← Send custom requests
└──────┬──────────┘
       │
       ├── Accepts custom prompt
       ├── Sends to API
       ├── Waits for response
       └── Displays result
       
┌─────────────┐
│   all.sh    │  ← Do everything at once
└──────┬──────┘
       │
       ├── Runs setup.sh
       ├── Checks credentials
       ├── Runs start.sh
       └── Shows summary
```

---

## 🐛 Troubleshooting

### Error: "Python 3 is not installed"
**Solution:** Install Python 3.8 or higher:
```bash
# On Ubuntu/Debian
sudo apt update && sudo apt install python3 python3-venv python3-pip

# On macOS
brew install python3

# On Windows (WSL)
sudo apt update && sudo apt install python3 python3-venv python3-pip
```

### Error: "CODEGEN_ORG_ID and CODEGEN_TOKEN are not set"
**Solution:** Set your credentials:
```bash
export CODEGEN_ORG_ID='your-org-id'
export CODEGEN_TOKEN='your-api-token'
```

Get them from: https://codegen.com/token

### Error: "Virtual environment not found"
**Solution:** Run setup first:
```bash
./setup.sh
```

### Script won't run: "Permission denied"
**Solution:** Make scripts executable:
```bash
chmod +x setup.sh start.sh send_request.sh all.sh
```

---

## 🧪 Testing the Scripts

To verify all scripts are working:

```bash
# Test syntax
bash -n setup.sh
bash -n start.sh
bash -n send_request.sh
bash -n all.sh

# Run a dry-run of setup
./setup.sh
```

---

## 📚 Additional Resources

- **Main Documentation:** [docs.codegen.com](https://docs.codegen.com)
- **Get API Token:** [codegen.com/token](https://codegen.com/token)
- **Community:** [community.codegen.com](https://community.codegen.com)
- **GitHub:** [github.com/codegen-sh/codegen](https://github.com/codegen-sh/codegen)

---

## 💡 Tips

1. **Environment Variables:** Consider using a `.env` file with a tool like `python-dotenv` for managing credentials
2. **Script Organization:** All scripts follow the same pattern: check dependencies → validate → execute
3. **Error Handling:** Scripts use `set -e` to exit on errors, ensuring failures are caught early
4. **Virtual Environment:** Always activated before running Python code to ensure clean dependencies

---

## 🤝 Contributing

Found an issue or want to improve these scripts? Please submit a PR or open an issue on GitHub!

---

**Last Updated:** October 2025

