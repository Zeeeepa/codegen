#!/bin/bash

# Exit on error
set -e

# Get the directory of the script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print banner
echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                 Codegen Modal Deployer                     ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Python 3 is required but not installed. Please install Python 3 and try again.${NC}"
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
PYTHON_VERSION_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_VERSION_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ "$PYTHON_VERSION_MAJOR" -lt 3 ] || ([ "$PYTHON_VERSION_MAJOR" -eq 3 ] && [ "$PYTHON_VERSION_MINOR" -lt 9 ]); then
    echo -e "${YELLOW}Warning: Python 3.9+ is recommended. You are using Python $PYTHON_VERSION.${NC}"
    read -p "Continue anyway? (y/n): " continue_anyway
    if [ "$continue_anyway" != "y" ] && [ "$continue_anyway" != "Y" ]; then
        echo "Exiting."
        exit 0
    fi
fi

# Check if Modal is installed
if ! python3 -c "import modal" &> /dev/null; then
    echo -e "${YELLOW}Modal is not installed. Installing now...${NC}"
    pip install modal==1.0.0
fi

# Check Modal version
MODAL_VERSION=$(python3 -c "import modal; print(modal.__version__)")
echo -e "${GREEN}Using Modal version: $MODAL_VERSION${NC}"

# Check if Modal token is set up
if ! modal token list &> /dev/null; then
    echo -e "${RED}Modal token not set up. Please run 'modal token new' to set up your Modal token.${NC}"
    exit 1
fi

# Function to deploy a single example
deploy_example() {
    local example_dir="$1"
    local example_name=$(basename "$example_dir")
    
    if [ -f "$example_dir/deploy.sh" ]; then
        echo -e "${BLUE}Deploying $example_name...${NC}"
        (cd "$example_dir" && bash deploy.sh)
        local status=$?
        if [ $status -eq 0 ]; then
            echo -e "${GREEN}✓ $example_name deployed successfully.${NC}"
        else
            echo -e "${RED}✗ $example_name deployment failed with status $status.${NC}"
        fi
        return $status
    else
        echo -e "${YELLOW}No deploy.sh script found for $example_name. Skipping.${NC}"
        return 1
    fi
}

# Function to verify deployment
verify_deployment() {
    local example_name="$1"
    local app_name="$2"
    
    echo -e "${BLUE}Verifying deployment of $example_name...${NC}"
    if modal app status "$app_name" | grep -q "RUNNING"; then
        echo -e "${GREEN}✓ $example_name is running.${NC}"
        return 0
    else
        echo -e "${YELLOW}! $example_name is not running. It may still be starting up or may have failed to deploy.${NC}"
        return 1
    fi
}

# Find all examples with deploy.sh scripts
examples=()
for dir in "$SCRIPT_DIR"/*/; do
    if [ -f "${dir}deploy.sh" ]; then
        examples+=($(basename "$dir"))
    fi
done

if [ ${#examples[@]} -eq 0 ]; then
    echo -e "${RED}No deployable examples found.${NC}"
    exit 1
fi

# Sort examples alphabetically
IFS=$'\n' examples=($(sort <<<"${examples[*]}"))
unset IFS

# Display menu
echo -e "${GREEN}Available examples for deployment:${NC}"
echo ""

for i in "${!examples[@]}"; do
    echo -e "${BLUE}[$((i+1))] ${examples[$i]}${NC}"
done

echo ""
echo -e "${BLUE}[a] Deploy all examples${NC}"
echo -e "${BLUE}[q] Quit${NC}"
echo ""

# Get user selection
selected_indices=()
while true; do
    read -p "Select examples to deploy (e.g., '1 3 5' or 'a' for all, 'q' to quit, 'd' when done): " selection
    
    if [ "$selection" == "q" ]; then
        echo -e "${YELLOW}Exiting without deployment.${NC}"
        exit 0
    elif [ "$selection" == "a" ]; then
        for i in "${!examples[@]}"; do
            selected_indices+=($i)
        done
        break
    elif [ "$selection" == "d" ]; then
        if [ ${#selected_indices[@]} -eq 0 ]; then
            echo -e "${YELLOW}No examples selected. Please select at least one example.${NC}"
        else
            break
        fi
    else
        # Parse space-separated numbers
        for num in $selection; do
            if [[ "$num" =~ ^[0-9]+$ ]] && [ "$num" -ge 1 ] && [ "$num" -le ${#examples[@]} ]; then
                idx=$((num-1))
                # Check if already selected
                if [[ ! " ${selected_indices[@]} " =~ " ${idx} " ]]; then
                    selected_indices+=($idx)
                    echo -e "${GREEN}Added ${examples[$idx]} to deployment list.${NC}"
                else
                    echo -e "${YELLOW}${examples[$idx]} is already selected.${NC}"
                fi
            else
                echo -e "${RED}Invalid selection: $num. Please enter numbers between 1 and ${#examples[@]}.${NC}"
            fi
        done
    fi
done

# Show selected examples
echo ""
echo -e "${GREEN}Selected examples for deployment:${NC}"
for idx in "${selected_indices[@]}"; do
    echo -e "${BLUE}- ${examples[$idx]}${NC}"
done
echo ""

# Confirm deployment
read -p "Deploy these examples? (y/n): " confirm
if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
    echo -e "${YELLOW}Deployment cancelled.${NC}"
    exit 0
fi

# Deploy selected examples concurrently
echo -e "${GREEN}Starting deployment of selected examples...${NC}"
pids=()
results=()

for idx in "${selected_indices[@]}"; do
    example="${examples[$idx]}"
    example_dir="$SCRIPT_DIR/$example"
    
    # Start deployment in background
    (deploy_example "$example_dir" && echo "SUCCESS: $example" || echo "FAILED: $example") &
    pids+=($!)
    results+=("")
done

# Wait for all deployments to complete
for i in "${!pids[@]}"; do
    wait "${pids[$i]}"
    results[$i]=$?
done

# Print summary
echo ""
echo -e "${BLUE}Deployment Summary:${NC}"
echo -e "${BLUE}==================${NC}"
success_count=0
failure_count=0

for i in "${!selected_indices[@]}"; do
    idx="${selected_indices[$i]}"
    example="${examples[$idx]}"
    result="${results[$i]}"
    
    if [ "$result" -eq 0 ]; then
        echo -e "${GREEN}✓ ${example}: SUCCESS${NC}"
        ((success_count++))
    else
        echo -e "${RED}✗ ${example}: FAILED${NC}"
        ((failure_count++))
    fi
done

echo ""
echo -e "${BLUE}Total: $((success_count + failure_count)), Successful: $success_count, Failed: $failure_count${NC}"

if [ "$failure_count" -gt 0 ]; then
    echo ""
    echo -e "${RED}Some deployments failed. Check the logs above for details.${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}All deployments completed successfully!${NC}"

# Offer to view logs
echo ""
echo -e "${BLUE}Options:${NC}"
echo -e "${BLUE}[l] View logs for a deployed example${NC}"
echo -e "${BLUE}[s] View status of all deployed examples${NC}"
echo -e "${BLUE}[q] Quit${NC}"
echo ""

read -p "Select an option: " option
if [ "$option" == "l" ]; then
    echo ""
    echo -e "${BLUE}Select an example to view logs:${NC}"
    for i in "${!selected_indices[@]}"; do
        idx="${selected_indices[$i]}"
        echo -e "${BLUE}[$((i+1))] ${examples[$idx]}${NC}"
    done
    echo ""
    
    read -p "Enter number: " log_selection
    if [[ "$log_selection" =~ ^[0-9]+$ ]] && [ "$log_selection" -ge 1 ] && [ "$log_selection" -le ${#selected_indices[@]} ]; then
        log_idx=$((log_selection-1))
        selected_idx="${selected_indices[$log_idx]}"
        example="${examples[$selected_idx]}"
        
        # Extract app name from deploy.sh
        app_name=$(grep -o "modal app [a-zA-Z0-9_-]*" "$SCRIPT_DIR/$example/deploy.sh" | head -1 | awk '{print $3}')
        if [ -z "$app_name" ]; then
            # Try to guess app name from example name
            app_name=$(echo "$example" | tr '_' '-')
        fi
        
        echo -e "${BLUE}Viewing logs for $example (app: $app_name)...${NC}"
        modal app logs "$app_name"
    else
        echo -e "${RED}Invalid selection.${NC}"
    fi
elif [ "$option" == "s" ]; then
    echo ""
    echo -e "${BLUE}Status of deployed examples:${NC}"
    for i in "${!selected_indices[@]}"; do
        idx="${selected_indices[$i]}"
        example="${examples[$idx]}"
        
        # Extract app name from deploy.sh
        app_name=$(grep -o "modal app [a-zA-Z0-9_-]*" "$SCRIPT_DIR/$example/deploy.sh" | head -1 | awk '{print $3}')
        if [ -z "$app_name" ]; then
            # Try to guess app name from example name
            app_name=$(echo "$example" | tr '_' '-')
        fi
        
        echo -e "${BLUE}$example (app: $app_name):${NC}"
        modal app status "$app_name" | grep -E "RUNNING|STOPPED|FAILED"
    done
fi

echo -e "${GREEN}Thank you for using the Codegen Modal Deployer!${NC}"
