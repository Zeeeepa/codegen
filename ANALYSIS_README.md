# Mass Repository CI/CD Analysis System

Automated system to analyze all 956 repositories in the Zeeeepa organization for Enterprise CI/CD compatibility using Codegen agents and Repomix.

## 🎯 Overview

This system creates 956 independent Codegen agent runs that:
1. Use Repomix to analyze each repository's full codebase structure
2. Rate the repository on 8 Enterprise CI/CD criteria (1-10 scale)
3. Generate detailed ratings with recommendations
4. Commit all ratings to a single branch → create one PR

## 📊 Rating Criteria

Each repository is rated on:

1. **Build System Maturity** - Build configuration and dependency management
2. **CI/CD Integration Readiness** - Automation and deployment capabilities
3. **Code Quality & Standards** - Linting, formatting, static analysis
4. **Documentation Quality** - README, API docs, setup instructions
5. **Containerization** - Docker configuration and practices
6. **Testing Infrastructure** - Unit, integration tests, coverage
7. **Security Practices** - Scanning, vulnerability checks, secrets management
8. **Enterprise Compatibility** - Licensing, scalability, enterprise features

## 🚀 Quick Start

### Prerequisites

```bash
# Install Codegen SDK
pip install codegen

# Set API key
export CODEGEN_API_KEY='your-api-key-here'
```

### Step 1: Populate Repository List

```bash
# Create repos_list.txt with all 956 repo names
# One repository name per line

# Example content:
# -Linux-
# 1Panel
# 3x-ui
# ...etc
```

### Step 2: Run Analysis

**Option A: Python Script (Recommended)**

```bash
python3 mass_repo_analysis.py
```

**Option B: Bash Script**

```bash
chmod +x create_analysis_agents.sh
./create_analysis_agents.sh
```

### Step 3: Monitor Progress

- Agent runs process at ~30/minute
- Total time: ~30 minutes for 956 repos
- Monitor in Codegen dashboard
- All ratings pushed to single branch

### Step 4: Create PR

```bash
# Once all agents complete, create PR from the analysis branch
# Branch name format: analysis/cicd-ratings-<timestamp>
```

## 📁 Output Structure

Each repository gets a rating file:

```
ratings/
├── -Linux-.json
├── 1Panel.json
├── 3x-ui.json
└── ...956 files total
```

### Rating File Format

```json
{
  "repo_name": "example-repo",
  "analyzed_at": "2025-12-26T01:30:00Z",
  "overall_score": 7.5,
  "ratings": {
    "build_system": 8,
    "cicd_readiness": 7,
    "code_quality": 8,
    "documentation": 7,
    "containerization": 9,
    "testing": 6,
    "security": 7,
    "enterprise": 8
  },
  "strengths": [
    "Excellent Docker configuration with multi-stage builds",
    "Comprehensive CI/CD pipeline with automated testing",
    "Well-documented API with examples"
  ],
  "weaknesses": [
    "Limited test coverage in backend modules",
    "Missing security scanning in CI pipeline"
  ],
  "summary": "Solid enterprise-ready application with strong containerization and CI/CD practices. Main improvement area is expanding test coverage.",
  "recommendations": [
    "Add security scanning (e.g., Trivy, Snyk) to CI pipeline",
    "Increase backend test coverage to >80%",
    "Document deployment process for production environments"
  ],
  "notable_files": [
    "Dockerfile",
    ".github/workflows/ci.yml",
    "docker-compose.yml"
  ]
}
```

## ⚙️ Configuration

### Rate Limiting

- **Default**: 30 agent runs per minute
- **Delay**: 2 seconds between requests
- **Pause**: 60 seconds after every 30 requests

Modify in scripts:
- Python: `RATE_LIMIT = 30`, `DELAY = 2`
- Bash: `MAX_PER_MINUTE=30`, `DELAY_BETWEEN_REQUESTS=2`

### Branch Naming

Default format: `analysis/cicd-ratings-<unix-timestamp>`

Change by setting `BRANCH_NAME` variable in scripts.

## 🔧 How It Works

1. **Fetch Repository List**
   - Loads all 956 repository names from `repos_list.txt`

2. **Create Agent Runs**
   - For each repository, creates a Codegen agent run
   - Passes detailed analysis instructions
   - Sets target branch for all commits

3. **Agent Execution**  
   - Each agent independently:
     - Uses Repomix to analyze the repository
     - Evaluates against 8 criteria
     - Generates structured JSON rating
     - Commits rating to analysis branch

4. **Consolidation**
   - All 956 ratings collected in `ratings/` directory
   - All changes in single branch
   - Create one PR with complete analysis

## 📝 Analysis Instructions Template

Each agent receives:
- Repository name to analyze
- Target branch for commits
- 8 rating criteria with detailed descriptions
- Output format specification
- Instructions to use Repomix for analysis

See `mass_repo_analysis.py` for full template.

## 🎯 Success Criteria

- ✅ All 956 repositories analyzed
- ✅ Each gets objective 1-10 ratings on 8 criteria
- ✅ Actionable recommendations provided
- ✅ All ratings in structured JSON format
- ✅ Single branch with all changes
- ✅ One PR for review

## 📊 Results Tracking

Analysis results saved to: `analysis_results_<timestamp>.json`

Contains:
- Start/completion timestamps
- Target branch name
- Successful agent runs (with run IDs)
- Failed runs (with error details)
- Summary statistics

## 🚨 Troubleshooting

### API Key Issues
```bash
# Verify API key is set
echo $CODEGEN_API_KEY

# Test API access
curl -H "Authorization: Bearer $CODEGEN_API_KEY" \
  https://api.codegen.com/v1/user
```

### Rate Limiting
- Script automatically handles 30/minute limit
- If hitting issues, increase `DELAY` in scripts

### Failed Runs
- Check `analysis_results_*.json` for failed repositories
- Retry failed repos individually
- Common causes: repo access, API errors, timeout

## 📚 Related Files

- `mass_repo_analysis.py` - Main Python implementation
- `create_analysis_agents.sh` - Bash alternative
- `analyze_all_repos.py` - Backup implementation
- `repos_list.txt` - Repository names (one per line)
- `ANALYSIS_README.md` - This file

## 🤝 Contributing

To add new rating criteria:
1. Update `ANALYSIS_INSTRUCTIONS` template
2. Add criteria to rating schema
3. Update output format in instructions
4. Document in this README

## 📄 License

Same as parent repository.

## 🎉 Credits

Built for efficient mass repository analysis using:
- **Codegen SDK** - Agent orchestration
- **Repomix** - Codebase analysis
- **Enterprise CI/CD best practices** - Rating criteria

---

**Ready to analyze 956 repositories in ~30 minutes!** 🚀

