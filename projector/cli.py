#!/usr/bin/env python3
import sys
import os

# Add the parent directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the main function from main.py
from projector.main import main

if __name__ == "__main__":
    main()