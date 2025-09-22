#!/usr/bin/env python3
"""
Setup script for Enhanced Chinese to English Translation Tool

This script will:
1. Check system requirements
2. Install Python dependencies
3. Clone the web-ui-python-sdk
4. Setup the environment
5. Run a test to verify everything works

Usage:
    python setup_enhanced.py
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path


def run_command(command, description="", check=True):
    """Run a system command with error handling"""
    print(f"🔄 {description}")
    print(f"Running: {command}")
    
    try:
        result = subprocess.run(command, shell=True, check=check, 
                              capture_output=True, text=True)
        if result.stdout:
            print(f"✓ {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {e}")
        if e.stderr:
            print(f"Stderr: {e.stderr}")
        return False


def check_python_version():
    """Check if Python version is compatible"""
    version = sys.version_info
    print(f"🐍 Python version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 7):
        print("❌ Python 3.7+ is required")
        return False
    
    print("✓ Python version is compatible")
    return True


def check_git():
    """Check if git is installed"""
    try:
        result = subprocess.run(['git', '--version'], capture_output=True, text=True)
        print(f"✓ Git is available: {result.stdout.strip()}")
        return True
    except FileNotFoundError:
        print("❌ Git is not installed. Please install Git first:")
        print("   https://git-scm.com/downloads")
        return False


def install_pip_requirements():
    """Install Python package requirements"""
    print("📦 Installing Python dependencies...")
    
    # Basic requirements
    requirements = [
        "requests>=2.28.0",
        "tqdm>=4.64.0"
    ]
    
    for requirement in requirements:
        print(f"Installing {requirement}...")
        if not run_command(f"{sys.executable} -m pip install {requirement}", 
                          f"Installing {requirement}", check=False):
            print(f"⚠️ Failed to install {requirement}, but continuing...")
    
    # Try to install optional tkinter-modern
    print("Installing optional tkinter styling...")
    run_command(f"{sys.executable} -m pip install tkinter-modern", 
               "Installing tkinter-modern (optional)", check=False)
    
    return True


def check_tkinter():
    """Check if tkinter is available"""
    try:
        import tkinter
        print("✓ Tkinter is available")
        return True
    except ImportError:
        print("❌ Tkinter is not available")
        print("On Ubuntu/Debian: sudo apt-get install python3-tk")
        print("On macOS: Usually included with Python")
        print("On Windows: Should be included with Python installation")
        return False


def clone_sdk():
    """Clone the web-ui-python-sdk repository"""
    sdk_dir = "web-ui-python-sdk"
    
    if os.path.exists(sdk_dir):
        print(f"✓ SDK directory already exists: {sdk_dir}")
        return True
    
    print("📥 Cloning web-ui-python-sdk...")
    success = run_command(
        "git clone https://github.com/Zeeeepa/web-ui-python-sdk.git",
        "Cloning web-ui-python-sdk repository"
    )
    
    if success and os.path.exists(sdk_dir):
        print(f"✓ SDK cloned successfully to: {os.path.abspath(sdk_dir)}")
        return True
    else:
        print("❌ Failed to clone SDK repository")
        return False


def setup_environment():
    """Setup the environment for the translation tool"""
    print("🔧 Setting up environment...")
    
    # Check if we can import from the SDK
    sdk_dir = os.path.abspath("web-ui-python-sdk")
    
    if not os.path.exists(sdk_dir):
        print(f"❌ SDK directory not found: {sdk_dir}")
        return False
    
    # Add SDK to Python path (for this session)
    if sdk_dir not in sys.path:
        sys.path.insert(0, sdk_dir)
        print(f"✓ Added SDK to Python path: {sdk_dir}")
    
    # Test import
    try:
        from client import ZAIClient
        print("✓ Successfully imported ZAIClient from SDK")
        return True
    except ImportError as e:
        print(f"❌ Failed to import SDK: {e}")
        print(f"Make sure the enhanced translation script is in the same directory as {sdk_dir}")
        return False


def run_test():
    """Run a basic test to verify the setup"""
    print("🧪 Running basic functionality test...")
    
    try:
        # Test GUI creation (without showing it)
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()  # Hide the window
        root.destroy()
        print("✓ Tkinter GUI creation test passed")
        
        # Test SDK import
        from client import ZAIClient
        print("✓ SDK import test passed")
        
        print("🎉 All tests passed! The enhanced translation tool should work correctly.")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False


def main():
    """Main setup function"""
    print("🚀 Enhanced Chinese to English Translation Tool - Setup")
    print("=" * 60)
    
    success_count = 0
    total_checks = 6
    
    # System checks
    if check_python_version():
        success_count += 1
    
    if check_git():
        success_count += 1
    
    if check_tkinter():
        success_count += 1
    
    # Installation steps
    if install_pip_requirements():
        success_count += 1
    
    if clone_sdk():
        success_count += 1
    
    if setup_environment():
        success_count += 1
    
    print("\n" + "=" * 60)
    print(f"Setup Summary: {success_count}/{total_checks} steps completed")
    
    if success_count == total_checks:
        print("🎉 Setup completed successfully!")
        
        if run_test():
            print("\n✅ Ready to use the enhanced translation tool!")
            print("\nTo run the tool:")
            print("1. Make sure you're in the directory with both:")
            print("   - multiple_language_standalone_enhanced.py")
            print("   - web-ui-python-sdk/ (directory)")
            print("2. Run: python multiple_language_standalone_enhanced.py")
        else:
            print("\n⚠️ Setup completed but tests failed")
            print("You may need to troubleshoot the issues above")
    else:
        failed = total_checks - success_count
        print(f"❌ Setup incomplete: {failed} issues need to be resolved")
        print("Please address the issues above and run setup again")
    
    print("\n📚 For help and documentation:")
    print("GitHub: https://github.com/Zeeeepa/web-ui-python-sdk")
    

if __name__ == "__main__":
    main()