#!/bin/bash

# Exit on error
set -e

# Get the directory of the script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is required but not installed. Please install Python 3 and try again."
    exit 1
fi

# Check if Modal is installed
if ! python3 -c "import modal" &> /dev/null; then
    echo "Modal is not installed. Installing now..."
    pip install modal
fi

# Check if Modal token is set up
if ! modal token list &> /dev/null; then
    echo "Modal token not set up. Please run 'modal token new' to set up your Modal token."
    exit 1
fi

# Function to deploy a single example
deploy_example() {
    local example_dir="$1"
    local example_name=$(basename "$example_dir")
    
    if [ -f "$example_dir/deploy.sh" ]; then
        echo "Deploying $example_name..."
        (cd "$example_dir" && bash deploy.sh)
        return $?
    else
        echo "No deploy.sh script found for $example_name. Skipping."
        return 1
    fi
}

# Find all examples with deploy.sh scripts
examples=()
for dir in "$SCRIPT_DIR"/*/; do
    if [ -f "${dir}deploy.sh" ]; then
        examples+=("$(basename "$dir")")
    fi
done

if [ ${#examples[@]} -eq 0 ]; then
    echo "No deployable examples found."
    exit 1
fi

# Display menu
echo "Available examples for deployment:"
echo ""

for i in "${!examples[@]}"; do
    echo "[$((i+1))] ${examples[$i]}"
done

echo ""
echo "[a] Deploy all examples"
echo "[q] Quit"
echo ""

# Get user selection
selected_indices=()
while true; do
    read -p "Select examples to deploy (e.g., '1 3 5' or 'a' for all, 'q' to quit, 'd' when done): " selection
    
    if [ "$selection" == "q" ]; then
        echo "Exiting without deployment."
        exit 0
    elif [ "$selection" == "a" ]; then
        for i in "${!examples[@]}"; do
            selected_indices+=($i)
        done
        break
    elif [ "$selection" == "d" ]; then
        if [ ${#selected_indices[@]} -eq 0 ]; then
            echo "No examples selected. Please select at least one example."
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
                    echo "Added ${examples[$idx]} to deployment list."
                else
                    echo "${examples[$idx]} is already selected."
                fi
            else
                echo "Invalid selection: $num. Please enter numbers between 1 and ${#examples[@]}."
            fi
        done
    fi
done

# Show selected examples
echo ""
echo "Selected examples for deployment:"
for idx in "${selected_indices[@]}"; do
    echo "- ${examples[$idx]}"
done
echo ""

# Confirm deployment
read -p "Deploy these examples? (y/n): " confirm
if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
    echo "Deployment cancelled."
    exit 0
fi

# Deploy selected examples concurrently
echo "Starting deployment of selected examples..."
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
echo "Deployment Summary:"
echo "=================="
success_count=0
failure_count=0

for i in "${!selected_indices[@]}"; do
    idx="${selected_indices[$i]}"
    example="${examples[$idx]}"
    result="${results[$i]}"
    
    if [ "$result" -eq 0 ]; then
        echo "✅ ${example}: SUCCESS"
        ((success_count++))
    else
        echo "❌ ${example}: FAILED"
        ((failure_count++))
    fi
done

echo ""
echo "Total: $((success_count + failure_count)), Successful: $success_count, Failed: $failure_count"

if [ "$failure_count" -gt 0 ]; then
    echo ""
    echo "Some deployments failed. Check the logs above for details."
    exit 1
fi

echo ""
echo "All deployments completed successfully!"

