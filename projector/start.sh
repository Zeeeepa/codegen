#!/bin/bash

# Start the Projector application
echo "Starting Projector..."
python projector/main.py

# Exit with the same status code as the Python script
exit $?
