#!/usr/bin/env python3
"""
Mass Repository Analysis using Codegen Python SDK
Analyzes all 956 repositories for Enterprise CI/CD compatibility
Creates agent runs at 30/minute with automatic rate limiting
"""
import os
import sys
import time
import json
from datetime import datetime
from typing import List, Dict

# Import Codegen SDK
try:
    from codegen import Codegen
except ImportError:
    print("❌ ERROR: Codegen SDK not installed!")
    print("   Install with: pip install codegen")
    sys.exit(1)

# Configuration
ORG_NAME = "Zeeeepa"
BRANCH_NAME = f"analysis/cicd-ratings-{int(time.time())}"
RATE_LIMIT = 30  # agents per minute
DELAY = 2  # seconds between requests

# Analysis instructions template
ANALYSIS_INSTRUCTIONS = """
**Task: Analyze {repo_name} for Enterprise CI/CD Compatibility**

Use Repomix to perform a comprehensive codebase analysis, then rate the repository on these 8 criteria (1-10 scale):

1. **Build System Maturity** (1-10)
   - Build configuration presence (package.json, Makefile, CMakeLists.txt, etc.)
   - Build script completeness
   - Dependency management quality

2. **CI/CD Integration Readiness** (1-10)
   - CI configuration files (.github/workflows, .gitlab-ci.yml, Jenkinsfile, etc.)
   - Automated testing in CI
   - Deployment automation

3. **Code Quality & Standards** (1-10)
   - Linting configuration (.eslintrc, .pylintrc, etc.)
   - Code formatting setup (prettier, black, etc.)
   - Static analysis tools

4. **Documentation Quality** (1-10)
   - README completeness
   - API documentation
   - Setup/deployment instructions

5. **Containerization** (1-10)
   - Dockerfile presence and quality
   - Docker Compose configuration
   - Multi-stage builds

6. **Testing Infrastructure** (1-10)
   - Unit tests presence
   - Integration tests
   - Test coverage configuration

7. **Security Practices** (1-10)
   - Security scanning configuration
   - Dependency vulnerability checks
   - Secrets management

8. **Enterprise Compatibility** (1-10)
   - Clear licensing
   - Enterprise features
   - Scalability considerations

**Output Requirements:**

1. Create directory: `ratings/` if it doesn't exist
2. Create file: `ratings/{repo_name}.json` with this exact structure:

```json
{{
  "repo_name": "{repo_name}",
  "analyzed_at": "<ISO8601-timestamp>",
  "overall_score": <average-of-8-ratings>,
  "ratings": {{
    "build_system": <1-10>,
    "cicd_readiness": <1-10>,
    "code_quality": <1-10>,
    "documentation": <1-10>,
    "containerization": <1-10>,
    "testing": <1-10>,
    "security": <1-10>,
    "enterprise": <1-10>
  }},
  "strengths": ["<strength-1>", "<strength-2>", "<strength-3>"],
  "weaknesses": ["<weakness-1>", "<weakness-2>"],
  "summary": "<2-3 sentence summary>",
  "recommendations": [
    "<actionable-recommendation-1>",
    "<actionable-recommendation-2>",
    "<actionable-recommendation-3>"
  ],
  "notable_files": ["<key-file-1>", "<key-file-2>"]
}}
```

3. Commit the rating file to branch: `{branch_name}`
4. Use descriptive commit message: "Add CI/CD rating for {repo_name}"

**Important:**
- Use Repomix to analyze the full repository structure
- Be objective in ratings
- Provide specific, actionable recommendations
- Consider the repository type (library, application, tool, etc.)
"""

def fetch_all_repos_from_api(codegen_client):
    """Fetch all repository names from the organization"""
    print("📋 Fetching repository list from Codegen API...")
    
    all_repos = []
    page = 1
    
    while True:
        try:
            # This would use the actual Codegen SDK method
            # For now, we'll use a placeholder
            # repos_page = codegen_client.repos.list(org=ORG_NAME, page=page)
            
            # Placeholder: load from file
            break
        except Exception as e:
            print(f"❌ Error fetching repos: {e}")
            break
    
    return all_repos

def create_agent_run(codegen_client, repo_name: str, branch_name: str) -> Dict:
    """Create a Codegen agent run for repository analysis"""
    
    instructions = ANALYSIS_INSTRUCTIONS.format(
        repo_name=repo_name,
        branch_name=branch_name
    )
    
    try:
        # Create agent run using Codegen SDK
        run = codegen_client.runs.create(
            repo=f"{ORG_NAME}/{repo_name}",
            message=f"Analyze {repo_name} for Enterprise CI/CD compatibility using Repomix",
            instructions=instructions,
            branch=branch_name,
            create_branch=True
        )
        
        return {
            "success": True,
            "run_id": run.id,
            "repo": repo_name,
            "created_at": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        return {
            "success": False,
            "repo": repo_name,
            "error": str(e)
        }

def main():
    print("="*70)
    print("  🤖 MASS REPOSITORY CI/CD ANALYSIS AUTOMATION")
    print("="*70)
    print()
    
    # Initialize Codegen client
    api_key = os.getenv("CODEGEN_API_KEY")
    if not api_key:
        print("❌ ERROR: CODEGEN_API_KEY environment variable not set!")
        print("   Set it with: export CODEGEN_API_KEY='your-api-key'")
        return 1
    
    print("🔑 Initializing Codegen client...")
    try:
        codegen = Codegen(api_key=api_key)
    except Exception as e:
        print(f"❌ Failed to initialize Codegen client: {e}")
        return 1
    
    # Load repository list
    print(f"📊 Loading repository list for organization: {ORG_NAME}")
    
    # For this script, load from repos_list.txt
    repos_file = "repos_list.txt"
    if not os.path.exists(repos_file):
        print(f"❌ Repository list file not found: {repos_file}")
        print(f"   Create it with one repository name per line")
        return 1
    
    with open(repos_file, 'r') as f:
        repos = [line.strip() for line in f if line.strip()]
    
    total_repos = len(repos)
    print(f"✅ Found {total_repos} repositories to analyze")
    print(f"⏱️  Estimated time: ~{(total_repos / RATE_LIMIT):.1f} minutes")
    print(f"🌿 Target branch: {BRANCH_NAME}")
    print()
    
    # Confirm before proceeding
    response = input(f"🚀 Create {total_repos} agent runs? (yes/no): ")
    if response.lower() not in ['yes', 'y']:
        print("❌ Cancelled by user")
        return 0
    
    print()
    print("="*70)
    print("  🏃 CREATING AGENT RUNS")
    print("="*70)
    print()
    
    # Track results
    results = {
        "started_at": datetime.utcnow().isoformat(),
        "branch": BRANCH_NAME,
        "total_repos": total_repos,
        "successful": [],
        "failed": []
    }
    
    # Create agent runs with rate limiting
    for idx, repo_name in enumerate(repos, 1):
        print(f"[{idx}/{total_repos}] Creating run for: {repo_name}")
        
        run_result = create_agent_run(codegen, repo_name, BRANCH_NAME)
        
        if run_result["success"]:
            print(f"  ✅ Created: {run_result['run_id']}")
            results["successful"].append(run_result)
        else:
            print(f"  ❌ Failed: {run_result['error']}")
            results["failed"].append(run_result)
        
        # Rate limiting
        if idx < total_repos:
            if idx % RATE_LIMIT == 0:
                print(f"  ⏸️  Rate limit pause ({idx}/{total_repos} processed)...")
                time.sleep(60)
            else:
                time.sleep(DELAY)
    
    # Save results
    results["completed_at"] = datetime.utcnow().isoformat()
    results_file = f"analysis_results_{int(time.time())}.json"
    
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print()
    print("="*70)
    print("  ✅ AGENT RUNS CREATED SUCCESSFULLY")
    print("="*70)
    print()
    print(f"📊 Summary:")
    print(f"   ✅ Successful: {len(results['successful'])}")
    print(f"   ❌ Failed: {len(results['failed'])}")
    print()
    print(f"📁 Results saved to: {results_file}")
    print(f"🌿 All analyses will push to branch: {BRANCH_NAME}")
    print()
    print("⏳ Agent runs are now processing (~30 minutes total)")
    print("   Monitor progress in Codegen dashboard")
    print()
    print(f"📝 Next step: Create PR from {BRANCH_NAME} when complete!")
    print()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

