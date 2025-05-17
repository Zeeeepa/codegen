#!/bin/bash

# Exit on error
set -e

# Get the directory of the script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Define colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Define the list of available examples
declare -a examples=(
    "swebench_agent_run"
    "snapshot_event_handler"
    "slack_chatbot"
    "repo_analytics"
    "pr_review_bot"
    "github_checks"
    "linear_webhooks"
    "modal_repo_analytics"
    "deep_code_research"
    "cyclomatic_complexity"
    "delete_dead_code"
    "document_functions"
    "codegen-mcp-server"
    "codegen_app"
    "ai_impact_analysis"
)

# Function to check if an example is deployable
is_deployable() {
    local example=$1
    if [ -d "$example" ] && [ -f "$example/deploy.sh" ]; then
        return 0 # True
    else
        return 1 # False
    fi
}

# Function to display the menu
display_menu() {
    echo -e "${BLUE}=== Codegen Examples Deployer ===${NC}"
    echo -e "${YELLOW}Select examples to deploy (space-separated numbers, e.g., '1 3 5')${NC}"
    echo -e "${YELLOW}Enter 'all' to select all examples${NC}"
    echo -e "${YELLOW}Enter 'q' to quit${NC}"
    echo ""
    
    local i=1
    for example in "${examples[@]}"; do
        if is_deployable "$example"; then
            echo -e "${GREEN}$i)${NC} $example ${GREEN}[deployable]${NC}"
        else
            echo -e "${RED}$i)${NC} $example ${RED}[not deployable]${NC}"
        fi
        ((i++))
    done
    echo ""
}

# Function to deploy a single example
deploy_example() {
    local example=$1
    local status=0
    
    echo -e "${BLUE}Deploying $example...${NC}"
    
    if [ -d "$example" ] && [ -f "$example/deploy.sh" ]; then
        (cd "$example" && bash ./deploy.sh) || status=$?
        
        if [ $status -eq 0 ]; then
            echo -e "${GREEN}Successfully deployed $example${NC}"
            return 0
        else
            echo -e "${RED}Failed to deploy $example (exit code: $status)${NC}"
            return 1
        fi
    else
        echo -e "${RED}$example is not deployable (missing deploy.sh script)${NC}"
        return 1
    fi
}

# Function to deploy multiple examples concurrently
deploy_examples() {
    local selected_examples=("$@")
    local pids=()
    local results=()
    local example_names=()
    
    echo -e "${BLUE}Starting deployment of ${#selected_examples[@]} examples...${NC}"
    
    # Start all deployments in background
    for example in "${selected_examples[@]}"; do
        if is_deployable "$example"; then
            echo -e "${YELLOW}Starting deployment of $example...${NC}"
            deploy_example "$example" &
            pids+=($!)
            example_names+=("$example")
        else
            echo -e "${RED}Skipping $example (not deployable)${NC}"
        fi
    done
    
    # Wait for all deployments to finish
    for i in "${!pids[@]}"; do
        wait "${pids[$i]}"
        results+=($?)
        if [ ${results[$i]} -eq 0 ]; then
            echo -e "${GREEN}✓ ${example_names[$i]} deployed successfully${NC}"
        else
            echo -e "${RED}✗ ${example_names[$i]} deployment failed${NC}"
        fi
    done
    
    # Print summary
    echo ""
    echo -e "${BLUE}=== Deployment Summary ===${NC}"
    local success_count=0
    local failure_count=0
    
    for i in "${!results[@]}"; do
        if [ ${results[$i]} -eq 0 ]; then
            ((success_count++))
        else
            ((failure_count++))
        fi
    done
    
    echo -e "${GREEN}Successfully deployed: $success_count${NC}"
    echo -e "${RED}Failed deployments: $failure_count${NC}"
    echo ""
    
    if [ $failure_count -gt 0 ]; then
        echo -e "${YELLOW}Some deployments failed. Check the logs above for details.${NC}"
    else
        echo -e "${GREEN}All deployments completed successfully!${NC}"
    fi
}

# Main loop
while true; do
    display_menu
    read -p "Enter your selection: " selection
    
    if [ "$selection" = "q" ]; then
        echo -e "${BLUE}Exiting...${NC}"
        exit 0
    elif [ "$selection" = "all" ]; then
        selected_examples=()
        for example in "${examples[@]}"; do
            if is_deployable "$example"; then
                selected_examples+=("$example")
            fi
        done
        deploy_examples "${selected_examples[@]}"
        break
    else
        selected_examples=()
        for num in $selection; do
            if [[ "$num" =~ ^[0-9]+$ ]] && [ "$num" -ge 1 ] && [ "$num" -le "${#examples[@]}" ]; then
                example="${examples[$((num-1))]}"
                if is_deployable "$example"; then
                    selected_examples+=("$example")
                else
                    echo -e "${RED}Example $example is not deployable. Skipping.${NC}"
                fi
            else
                echo -e "${RED}Invalid selection: $num. Please enter valid numbers.${NC}"
            fi
        done
        
        if [ ${#selected_examples[@]} -gt 0 ]; then
            echo -e "${BLUE}Selected examples: ${selected_examples[*]}${NC}"
            read -p "Proceed with deployment? (y/n): " confirm
            if [ "$confirm" = "y" ] || [ "$confirm" = "Y" ]; then
                deploy_examples "${selected_examples[@]}"
                break
            else
                echo -e "${YELLOW}Deployment cancelled.${NC}"
            fi
        else
            echo -e "${RED}No valid examples selected.${NC}"
        fi
    fi
done

