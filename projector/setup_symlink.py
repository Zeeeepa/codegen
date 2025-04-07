#!/usr/bin/env python3
"""
Setup script to create a symbolic link structure for the projector module.

This script creates a symbolic link structure that allows the projector module
to be imported as agentgen.application.projector, which is needed for compatibility
with the agentgen repository.
"""

import os
import sys
import shutil
from pathlib import Path

def setup_symlinks():
    """Create the necessary symbolic link structure."""
    # Get the current directory (should be the projector directory)
    current_dir = Path(__file__).parent.absolute()
    
    # Create the agentgen/application directory structure
    agentgen_dir = current_dir.parent / "agentgen"
    application_dir = agentgen_dir / "application"
    
    # Create directories if they don't exist
    os.makedirs(application_dir, exist_ok=True)
    
    # Create a symbolic link from agentgen/application/projector to the projector directory
    projector_symlink = application_dir / "projector"
    
    # Remove the symlink if it already exists
    if os.path.islink(projector_symlink):
        os.unlink(projector_symlink)
    
    # Create the symlink
    os.symlink(current_dir, projector_symlink, target_is_directory=True)
    
    # Create an __init__.py file in the agentgen directory
    with open(agentgen_dir / "__init__.py", "w") as f:
        f.write("# This file is needed for the agentgen package to be importable\n")
    
    # Create an __init__.py file in the application directory
    with open(application_dir / "__init__.py", "w") as f:
        f.write("# This file is needed for the agentgen.application package to be importable\n")
    
    print(f"Created symbolic link: {projector_symlink} -> {current_dir}")
    print("You can now import the projector module as agentgen.application.projector")

if __name__ == "__main__":
    setup_symlinks()