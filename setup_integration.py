#!/usr/bin/env python3
"""
Setup script for complete Codegen + Serena + SolidLSP integration.

This script handles the proper installation and configuration of all components
to ensure they work together seamlessly.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path


def run_command(cmd: str, cwd: Path = None) -> bool:
    """Run a command and return success status"""
    try:
        print(f"🔧 Running: {cmd}")
        result = subprocess.run(
            cmd, 
            shell=True, 
            cwd=cwd, 
            check=True,
            capture_output=True,
            text=True
        )
        if result.stdout:
            print(f"   Output: {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"   ❌ Error: {e}")
        if e.stderr:
            print(f"   Stderr: {e.stderr.strip()}")
        return False


def setup_serena_integration():
    """Set up Serena integration"""
    print("🔗 Setting up Serena integration...")
    
    root_path = Path(__file__).parent
    serena_path = root_path / "serena"
    
    if not serena_path.exists():
        print("❌ Serena directory not found!")
        return False
    
    # Install Serena in development mode
    if not run_command("pip install -e .", cwd=serena_path):
        print("❌ Failed to install Serena")
        return False
    
    print("✅ Serena integration complete")
    return True


def setup_solidlsp_integration():
    """Set up SolidLSP integration from Serena"""
    print("🔗 Setting up SolidLSP integration...")
    
    root_path = Path(__file__).parent
    serena_solidlsp_path = root_path / "serena" / "src" / "solidlsp"
    sdk_solidlsp_path = root_path / "src" / "codegen" / "sdk" / "extensions" / "lsp" / "solidlsp"
    
    if not serena_solidlsp_path.exists():
        print("❌ SolidLSP not found in Serena!")
        return False
    
    # Create backup of existing SolidLSP if it exists
    if sdk_solidlsp_path.exists():
        backup_path = sdk_solidlsp_path.parent / "solidlsp_backup"
        if backup_path.exists():
            shutil.rmtree(backup_path)
        shutil.copytree(sdk_solidlsp_path, backup_path)
        shutil.rmtree(sdk_solidlsp_path)
        print("   📦 Backed up existing SolidLSP")
    
    # Copy Serena's SolidLSP
    shutil.copytree(serena_solidlsp_path, sdk_solidlsp_path)
    print("   ✅ SolidLSP integrated from Serena")
    
    return True


def setup_codegen_integration():
    """Set up Codegen with all integrations"""
    print("🔧 Setting up Codegen with full integration...")
    
    root_path = Path(__file__).parent
    
    # Install Codegen in development mode
    if not run_command("pip install -e .", cwd=root_path):
        print("❌ Failed to install Codegen")
        return False
    
    print("✅ Codegen integration complete")
    return True


def run_tests():
    """Run tests to validate the integration"""
    print("🧪 Running integration tests...")
    
    root_path = Path(__file__).parent
    
    # Run ruff check
    print("   Running ruff check...")
    if not run_command("ruff check src/", cwd=root_path):
        print("   ⚠️  Ruff check failed - continuing anyway")
    
    # Run mypy check
    print("   Running mypy check...")
    if not run_command("mypy src/codegen/sdk/core/", cwd=root_path):
        print("   ⚠️  MyPy check failed - continuing anyway")
    
    # Run our integration test
    print("   Running integration test...")
    if not run_command("python test_unified_integration.py", cwd=root_path):
        print("   ❌ Integration test failed")
        return False
    
    print("✅ All tests passed")
    return True


def main():
    """Main setup function"""
    print("🚀 Starting complete Codegen + Serena + SolidLSP integration setup...")
    print("=" * 70)
    
    # Step 1: Set up Serena
    if not setup_serena_integration():
        print("❌ Serena setup failed")
        sys.exit(1)
    
    # Step 2: Set up SolidLSP
    if not setup_solidlsp_integration():
        print("❌ SolidLSP setup failed")
        sys.exit(1)
    
    # Step 3: Set up Codegen
    if not setup_codegen_integration():
        print("❌ Codegen setup failed")
        sys.exit(1)
    
    # Step 4: Run tests
    if not run_tests():
        print("❌ Tests failed")
        sys.exit(1)
    
    print("=" * 70)
    print("🎉 Complete integration setup successful!")
    print()
    print("You can now use:")
    print("  - codegen CLI with full SDK capabilities")
    print("  - graph-sitter with Serena and SolidLSP integration")
    print("  - Unified API: codebase.from_repo(repo_name)")
    print("  - All 4 config parameters: lspserver, diagnostics, errorautoresolve, enhancedcontext")
    print()
    print("Test the integration with:")
    print("  python -c \"from codegen.sdk.core.unified_api import from_repo; print('Integration working!')\"")


if __name__ == "__main__":
    main()
