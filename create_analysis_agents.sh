#!/bin/bash
# Mass Repository CI/CD Analysis using Codegen Agent API
# Creates 956 agent runs sequentially with rate limiting

set -euo pipefail

# Configuration
CODEGEN_API_URL="${CODEGEN_API_URL:-https://api.codegen.com}"
CODEGEN_API_KEY="${CODEGEN_API_KEY:-}"
ORG_NAME="Zeeeepa"
BRANCH_NAME="analysis/cicd-ratings-$(date +%s)"
MAX_PER_MINUTE=30
DELAY_BETWEEN_REQUESTS=2  # seconds

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_progress() { echo -e "${BLUE}[PROGRESS]${NC} $1"; }

# Check API key
if [ -z "$CODEGEN_API_KEY" ]; then
    log_error "CODEGEN_API_KEY environment variable not set!"
    echo "Please set it with: export CODEGEN_API_KEY='your-key'"
    exit 1
fi

log_info "Starting Mass Repository Analysis"
echo "=================================="
log_info "Organization: $ORG_NAME"
log_info "Target Branch: $BRANCH_NAME"
log_info "Rate Limit: $MAX_PER_MINUTE agents/minute"
echo ""

# Fetch all repository names
log_info "Fetching repository list..."

# This would call the Codegen API to get all repos
# For now, create a repos list file
REPOS_FILE="repos_list.txt"

if [ ! -f "$REPOS_FILE" ]; then
    log_warn "Repository list not found. Please create $REPOS_FILE with one repo name per line."
    echo "Example:"
    echo "  -Linux-"
    echo "  1Panel"
    echo "  3x-ui"
    exit 1
fi

# Read repos into array
mapfile -t REPOS < "$REPOS_FILE"
TOTAL_REPOS=${#REPOS[@]}

log_info "Found $TOTAL_REPOS repositories to analyze"
log_info "Estimated time: ~$((TOTAL_REPOS / MAX_PER_MINUTE)) minutes"
echo ""

# Analysis instructions template
read -r -d '' ANALYSIS_TEMPLATE << 'TEMPLATE_END' || true
Analyze repository {{REPO_NAME}} using Repomix for Enterprise CI/CD Compatibility.

Rate on these criteria (1-10 scale):
1. Build System Maturity
2. CI/CD Integration Readiness  
3. Code Quality & Standards
4. Documentation Quality
5. Containerization
6. Testing Infrastructure
7. Security Practices
8. Enterprise Compatibility

Create file: ratings/{{REPO_NAME}}.json with:
{
  "repo_name": "{{REPO_NAME}}",
  "overall_score": <average>,
  "ratings": {
    "build_system": <1-10>,
    "cicd_readiness": <1-10>,
    "code_quality": <1-10>,
    "documentation": <1-10>,
    "containerization": <1-10>,
    "testing": <1-10>,
    "security": <1-10>,
    "enterprise": <1-10>
  },
  "summary": "<brief-summary>",
  "recommendations": ["<improvement-1>", "<improvement-2>"]
}

Push to branch: {{BRANCH}}
TEMPLATE_END

# Results tracking
SUCCESS_COUNT=0
FAILED_COUNT=0
RESULTS_FILE="analysis_runs_$(date +%s).json"

echo "[" > "$RESULTS_FILE"

# Create agent runs
log_info "Creating agent runs..."
echo ""

for i in "${!REPOS[@]}"; do
    REPO_NAME="${REPOS[$i]}"
    INDEX=$((i + 1))
    
    log_progress "[$INDEX/$TOTAL_REPOS] Processing: $REPO_NAME"
    
    # Prepare instructions
    INSTRUCTIONS="${ANALYSIS_TEMPLATE//\{\{REPO_NAME\}\}/$REPO_NAME}"
    INSTRUCTIONS="${INSTRUCTIONS//\{\{BRANCH\}\}/$BRANCH_NAME}"
    
    # Create API payload
    PAYLOAD=$(jq -n \
        --arg repo "$ORG_NAME/$REPO_NAME" \
        --arg branch "$BRANCH_NAME" \
        --arg msg "Analyze $REPO_NAME for CI/CD compatibility" \
        --arg inst "$INSTRUCTIONS" \
        '{
            repository: $repo,
            branch: $branch,
            message: $msg,
            instructions: $inst,
            create_branch: true
        }')
    
    # Make API request
    RESPONSE=$(curl -s -w "\n%{http_code}" \
        -X POST "$CODEGEN_API_URL/v1/agent-runs" \
        -H "Authorization: Bearer $CODEGEN_API_KEY" \
        -H "Content-Type: application/json" \
        -d "$PAYLOAD")
    
    HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
    BODY=$(echo "$RESPONSE" | sed '$d')
    
    if [ "$HTTP_CODE" = "201" ] || [ "$HTTP_CODE" = "200" ]; then
        RUN_ID=$(echo "$BODY" | jq -r '.id // .run_id // "unknown"')
        log_info "  ✓ Created run: $RUN_ID"
        
        SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
        
        # Save to results
        echo "$BODY" | jq -c ". + {repo_name: \"$REPO_NAME\"}" >> "$RESULTS_FILE"
        if [ $INDEX -lt $TOTAL_REPOS ]; then
            echo "," >> "$RESULTS_FILE"
        fi
    else
        log_error "  ✗ Failed: HTTP $HTTP_CODE"
        log_error "  Response: $BODY"
        FAILED_COUNT=$((FAILED_COUNT + 1))
    fi
    
    # Rate limiting
    if [ $INDEX -lt $TOTAL_REPOS ]; then
        if [ $((INDEX % MAX_PER_MINUTE)) -eq 0 ]; then
            log_warn "  ⏸️  Rate limit pause ($INDEX/$TOTAL_REPOS processed)..."
            sleep 60
        else
            sleep $DELAY_BETWEEN_REQUESTS
        fi
    fi
done

echo "]" >> "$RESULTS_FILE"

# Summary
echo ""
echo "=================================="
log_info "Analysis Complete!"
echo "=================================="
echo ""
echo "📊 Summary:"
echo "   ✓ Successful: $SUCCESS_COUNT"
echo "   ✗ Failed: $FAILED_COUNT"
echo "   📁 Results: $RESULTS_FILE"
echo "   🌿 Branch: $BRANCH_NAME"
echo ""
echo "⏳ Agent runs are now processing (~ 30 minutes total)"
echo "   Monitor progress in Codegen dashboard"
echo "   All ratings will be pushed to branch: $BRANCH_NAME"
echo ""
echo "📝 Next step: Create PR from $BRANCH_NAME when complete!"
echo ""

