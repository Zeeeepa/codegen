#!/usr/bin/env python3
"""
🚀 Enhanced Dependency Installer for Ultimate Code Quality System
================================================================

Installs and verifies ALL dependencies for comprehensive code analysis:
- Core Python linting/formatting tools (ruff, black, mypy, pylint, etc.)
- Security analysis tools (bandit, safety, pip-audit)
- Complexity analysis tools (radon, xenon, vulture, cohesion)
- Documentation tools (pydocstyle, interrogate)
- Testing tools (pytest, coverage)
- LSP servers (python-lsp-server, pyright)
- Advanced analysis tools (semgrep, prospector)
- Dependency analyzers (pipdeptree, pydeps)

USAGE:
    python install_dependencies.py                  # Install all
    python install_dependencies.py --verbose        # Verbose output
    python install_dependencies.py --skip-node      # Skip Node.js tools
    python install_dependencies.py --verify-only    # Only verify existing
    python install_dependencies.py --upgrade        # Upgrade existing
"""

import subprocess
import sys
import os
import time
from typing import List, Dict, Optional, Tuple
from pathlib import Path


class DependencyInstaller:
    """Enhanced dependency installer with comprehensive verification."""
    
    def __init__(self, verbose: bool = False, upgrade: bool = False):
        self.verbose = verbose
        self.upgrade = upgrade
        self.installed_tools = set()
        self.failed_tools = set()
        self.skipped_tools = set()
        self.verified_tools = {}  # tool -> version
        self.installation_times = {}
        
    def install_all(self, skip_node: bool = False):
        """Install all required dependencies."""
        print("=" * 80)
        print("🚀 ULTIMATE CODE QUALITY SYSTEM - DEPENDENCY INSTALLER")
        print("=" * 80)
        
        start_time = time.time()
        
        # Core Python packages (organized by category)
        package_groups = {
            "🔍 Linters & Formatters": [
                "ruff>=0.3.0",
                "black>=24.0.0",
                "isort>=5.13.0",
                "pycodestyle>=2.11.0",
                "pyflakes>=3.2.0",
                "flake8>=7.0.0",
            ],
            "🔬 Type Checkers": [
                "mypy>=1.8.0",
            ],
            "📊 Static Analysis": [
                "pylint>=3.0.0",
                "prospector>=1.10.0",
                "vulture>=2.10",
            ],
            "🔒 Security Analysis": [
                "bandit>=1.7.5",
                "safety>=3.0.0",
                "pip-audit>=2.6.0",
            ],
            "📈 Complexity Analysis": [
                "radon>=6.0.0",
                "xenon>=0.9.0",
                "mccabe>=0.7.0",
                "cohesion>=1.0.0",
            ],
            "📝 Documentation": [
                "pydocstyle>=6.3.0",
                "interrogate>=1.5.0",
            ],
            "🧪 Testing Tools": [
                "pytest>=8.0.0",
                "pytest-cov>=4.0.0",
                "coverage>=7.4.0",
            ],
            "🌐 LSP & IDE Support": [
                "python-lsp-server[all]>=1.10.0",
            ],
            "🔗 Dependency Analysis": [
                "pipdeptree>=2.13.0",
                "pydeps>=1.12.0",
            ],
            "⚡ Advanced Tools": [
                "semgrep>=1.60.0",
                "dlint>=0.14.0",
                "dodgy>=0.2.1",
            ],
            "🎨 UI/Output": [
                "rich>=13.7.0",
                "colorama>=0.4.6",
                "tabulate>=0.9.0",
            ],
            "📦 Utilities": [
                "pyyaml>=6.0.1",
                "click>=8.1.7",
            ],
        }
        
        # Install all Python package groups
        total_packages = sum(len(pkgs) for pkgs in package_groups.values())
        current = 0
        
        for category, packages in package_groups.items():
            print(f"\n{category}")
            print("-" * 80)
            
            for package in packages:
                current += 1
                progress = f"[{current}/{total_packages}]"
                self._install_python_package(package, progress)
        
        # Install Node.js tools if not skipped
        if not skip_node:
            node_packages = {
                "🟢 Node.js Tools": [
                    "pyright",
                    "@typescript-eslint/parser"
                ]
            }
            
            for category, packages in node_packages.items():
                print(f"\n{category}")
                print("-" * 80)
                self._install_node_packages(packages)
        
        # Verify all installations
        print("\n🔍 VERIFICATION")
        print("-" * 80)
        self._verify_installations()
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Show comprehensive summary
        self._show_installation_summary(duration)
    
    def verify_only(self):
        """Only verify existing installations without installing."""
        print("=" * 80)
        print("🔍 VERIFYING EXISTING INSTALLATIONS")
        print("=" * 80)
        
        self._verify_installations()
        self._show_verification_summary()
    
    def _install_python_package(self, package: str, progress: str = ""):
        """Install a single Python package with enhanced feedback."""
        tool_name = package.split(">=")[0].split("==")[0].split("[")[0]
        
        if not self.verbose:
            print(f"{progress} Installing {tool_name}...", end="", flush=True)
        else:
            print(f"\n{progress} Installing {tool_name}")
            print(f"  Package spec: {package}")
        
        start = time.time()
        
        try:
            cmd = [sys.executable, "-m", "pip", "install"]
            if self.upgrade:
                cmd.append("--upgrade")
            cmd.extend([package, "--quiet"])
            
            result = subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            duration = time.time() - start
            self.installation_times[tool_name] = duration
            self.installed_tools.add(tool_name)
            
            if not self.verbose:
                print(f" ✅ ({duration:.1f}s)")
            else:
                print(f"  ✅ Installed successfully in {duration:.1f}s")
                
        except subprocess.TimeoutExpired:
            self.failed_tools.add(tool_name)
            if not self.verbose:
                print(f" ❌ (timeout)")
            else:
                print(f"  ❌ Installation timeout after 300s")
                
        except subprocess.CalledProcessError as e:
            self.failed_tools.add(tool_name)
            if not self.verbose:
                print(f" ❌")
            else:
                print(f"  ❌ Failed: {e}")
                if e.stderr:
                    print(f"  Error: {e.stderr[:200]}")
    
    def _install_node_packages(self, packages: List[str]):
        """Install Node.js packages with enhanced error handling."""
        # Check if npm is available
        try:
            subprocess.run(
                ["npm", "--version"],
                check=True,
                capture_output=True,
                timeout=5
            )
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            print("⚠️  npm not found. Skipping Node.js packages.")
            print("   Install Node.js from: https://nodejs.org/")
            for pkg in packages:
                self.skipped_tools.add(pkg)
            return
        
        for package in packages:
            print(f"Installing {package}...", end="", flush=True)
            
            try:
                subprocess.run(
                    ["npm", "install", "-g", package],
                    check=True,
                    capture_output=True,
                    text=True,
                    timeout=120
                )
                self.installed_tools.add(package)
                print(" ✅")
                
            except subprocess.CalledProcessError as e:
                self.failed_tools.add(package)
                print(" ❌")
                if self.verbose and e.stderr:
                    print(f"  Error: {e.stderr[:200]}")
            except subprocess.TimeoutExpired:
                self.failed_tools.add(package)
                print(" ❌ (timeout)")
    
    def _verify_installations(self):
        """Comprehensive verification of all installed tools."""
        verification_commands = {
            # Core tools
            "ruff": (["ruff", "--version"], "Ruff"),
            "black": (["black", "--version"], "Black"),
            "isort": (["isort", "--version"], "isort"),
            "mypy": (["mypy", "--version"], "Mypy"),
            "pylint": (["pylint", "--version"], "Pylint"),
            "flake8": (["flake8", "--version"], "Flake8"),
            
            # Security
            "bandit": (["bandit", "--version"], "Bandit"),
            "safety": (["safety", "--version"], "Safety"),
            
            # Complexity
            "radon": (["radon", "--version"], "Radon"),
            "xenon": (["xenon", "--version"], "Xenon"),
            "vulture": (["vulture", "--version"], "Vulture"),
            
            # Documentation
            "pydocstyle": (["pydocstyle", "--version"], "pydocstyle"),
            "interrogate": (["interrogate", "--version"], "Interrogate"),
            
            # Testing
            "pytest": (["pytest", "--version"], "Pytest"),
            "coverage": (["coverage", "--version"], "Coverage"),
            
            # Style
            "pycodestyle": (["pycodestyle", "--version"], "pycodestyle"),
            "pyflakes": (["pyflakes", "--version"], "Pyflakes"),
            
            # Advanced
            "semgrep": (["semgrep", "--version"], "Semgrep"),
            "prospector": (["prospector", "--version"], "Prospector"),
            
            # Node.js
            "pyright": (["pyright", "--version"], "Pyright"),
            
            # Dependency
            "pipdeptree": (["pipdeptree", "--version"], "pipdeptree"),
        }
        
        print("\nVerifying installations...")
        verified_count = 0
        
        for tool, (command, display_name) in verification_commands.items():
            try:
                result = subprocess.run(
                    command,
                    check=True,
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                # Extract version from output
                version = result.stdout.strip().split('\n')[0]
                self.verified_tools[display_name] = version
                verified_count += 1
                
                if self.verbose:
                    print(f"✅ {display_name}: {version}")
                    
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
                if self.verbose:
                    print(f"❌ {display_name}: Not found or failed")
        
        if not self.verbose:
            print(f"Verified: {verified_count}/{len(verification_commands)} tools")
    
    def _show_installation_summary(self, duration: float):
        """Show comprehensive installation summary."""
        print("\n" + "=" * 80)
        print("📊 INSTALLATION SUMMARY")
        print("=" * 80)
        
        total = len(self.installed_tools) + len(self.failed_tools) + len(self.skipped_tools)
        
        print(f"\n⏱️  Total Duration: {duration:.2f}s")
        print(f"📦 Total Packages: {total}")
        
        if self.installed_tools:
            print(f"\n✅ Successfully Installed: {len(self.installed_tools)}")
            if self.verbose:
                for tool in sorted(self.installed_tools):
                    install_time = self.installation_times.get(tool, 0)
                    print(f"   • {tool:<30} ({install_time:.1f}s)")
        
        if self.verified_tools:
            print(f"\n🔍 Verified & Working: {len(self.verified_tools)}")
            if self.verbose:
                for tool, version in sorted(self.verified_tools.items()):
                    print(f"   • {tool:<30} {version}")
        
        if self.skipped_tools:
            print(f"\n⏭️  Skipped: {len(self.skipped_tools)}")
            for tool in sorted(self.skipped_tools):
                print(f"   • {tool}")
        
        if self.failed_tools:
            print(f"\n❌ Failed Installations: {len(self.failed_tools)}")
            for tool in sorted(self.failed_tools):
                print(f"   • {tool}")
            
            print("\n💡 Troubleshooting Tips:")
            print("   • Some tools require additional system dependencies")
            print("   • Try: pip install <tool-name> --verbose")
            print("   • Check your Python version (3.7+ required)")
            print("   • Ensure internet connectivity for pip/npm")
            print("   • Some tools (semgrep) may need specific OS support")
        
        # Show next steps
        print("\n" + "=" * 80)
        print("🚀 NEXT STEPS")
        print("=" * 80)
        print("\n1. Run the ultimate quality checker:")
        print("   python code_quality_ultimate.py --help")
        print("\n2. Quick test:")
        print("   python code_quality_ultimate.py lint")
        print("\n3. Full analysis with reports:")
        print("   python code_quality_ultimate.py --html report.html")
        print("\n4. Git-aware checking:")
        print("   python code_quality_ultimate.py --git-diff main --json results.json")
        
        # Success/failure indicator
        success_rate = len(self.verified_tools) / total * 100 if total > 0 else 0
        
        print(f"\n{'🎉' if success_rate > 80 else '⚠️'} Installation Success Rate: {success_rate:.1f}%")
        
        if success_rate > 80:
            print("✨ Ready for comprehensive code analysis!")
        elif success_rate > 50:
            print("⚠️ Partial installation. Core tools are available.")
        else:
            print("❌ Many tools failed to install. Check errors above.")
    
    def _show_verification_summary(self):
        """Show verification-only summary."""
        print("\n" + "=" * 80)
        print("📊 VERIFICATION SUMMARY")
        print("=" * 80)
        
        if self.verified_tools:
            print(f"\n✅ Found & Working: {len(self.verified_tools)} tools")
            for tool, version in sorted(self.verified_tools.items()):
                print(f"   • {tool:<30} {version}")
        else:
            print("\n❌ No tools verified!")
            print("   Run without --verify-only to install")


def main():
    """Main entry point with enhanced CLI."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="🚀 Enhanced Dependency Installer for Ultimate Code Quality System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python install_dependencies.py                  # Install all dependencies
  python install_dependencies.py --verbose        # Show detailed output
  python install_dependencies.py --skip-node      # Skip Node.js packages
  python install_dependencies.py --verify-only    # Only verify existing
  python install_dependencies.py --upgrade        # Upgrade existing packages
  python install_dependencies.py --verbose --upgrade  # Verbose upgrade

After installation, run:
  python code_quality_ultimate.py --help
        """
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show verbose installation output"
    )
    parser.add_argument(
        "--skip-node",
        action="store_true",
        help="Skip Node.js package installation"
    )
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Only verify existing installations"
    )
    parser.add_argument(
        "--upgrade",
        action="store_true",
        help="Upgrade existing packages to latest versions"
    )
    
    args = parser.parse_args()
    
    try:
        installer = DependencyInstaller(verbose=args.verbose, upgrade=args.upgrade)
        
        if args.verify_only:
            installer.verify_only()
        else:
            installer.install_all(skip_node=args.skip_node)
            
    except KeyboardInterrupt:
        print("\n\n⚠️ Installation interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()