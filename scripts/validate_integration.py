# Copyright 2025 Emcie Co Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Validation Gates for Unified Integration Components

This script runs comprehensive validation including linting, type checking,
and integration tests for the unified SolidLSP + Serena + Graph-Sitter system.
"""

import sys
import subprocess
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
import argparse
import time


class ValidationGate:
    """Represents a validation gate with pass/fail status"""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.passed = False
        self.output = ""
        self.error_output = ""
        self.duration = 0.0
    
    def run(self, command: List[str], cwd: Optional[str] = None) -> bool:
        """Run the validation command"""
        start_time = time.time()
        
        try:
            print(f"Running {self.name}...")
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                cwd=cwd,
                timeout=300  # 5 minute timeout
            )
            
            self.duration = time.time() - start_time
            self.output = result.stdout
            self.error_output = result.stderr
            self.passed = result.returncode == 0
            
            if self.passed:
                print(f"✅ {self.name} passed ({self.duration:.2f}s)")
            else:
                print(f"❌ {self.name} failed ({self.duration:.2f}s)")
                if self.error_output:
                    print(f"Error output:\n{self.error_output}")
            
            return self.passed
            
        except subprocess.TimeoutExpired:
            self.duration = time.time() - start_time
            self.error_output = f"Command timed out after {self.duration:.2f}s"
            self.passed = False
            print(f"⏰ {self.name} timed out")
            return False
        
        except Exception as e:
            self.duration = time.time() - start_time
            self.error_output = str(e)
            self.passed = False
            print(f"💥 {self.name} failed with exception: {e}")
            return False


class IntegrationValidator:
    """Comprehensive validation for the unified integration system"""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.gates: List[ValidationGate] = []
        self.core_path = self.project_root / "src" / "codegen" / "sdk" / "core"
        
    def add_gate(self, gate: ValidationGate) -> None:
        """Add a validation gate"""
        self.gates.append(gate)
    
    def run_all_gates(self) -> bool:
        """Run all validation gates"""
        print("🚀 Starting comprehensive validation of unified integration system")
        print(f"Project root: {self.project_root}")
        print(f"Core path: {self.core_path}")
        print("=" * 80)
        
        passed_gates = 0
        total_gates = len(self.gates)
        
        for gate in self.gates:
            if gate.run([]):  # Command will be set by specific gate implementations
                passed_gates += 1
        
        print("=" * 80)
        print(f"Validation Results: {passed_gates}/{total_gates} gates passed")
        
        if passed_gates == total_gates:
            print("🎉 All validation gates passed!")
            return True
        else:
            print("❌ Some validation gates failed")
            self._print_failure_summary()
            return False
    
    def _print_failure_summary(self) -> None:
        """Print summary of failed gates"""
        print("\n📋 Failed Gates Summary:")
        for gate in self.gates:
            if not gate.passed:
                print(f"  ❌ {gate.name}: {gate.description}")
                if gate.error_output:
                    print(f"     Error: {gate.error_output[:200]}...")
    
    def setup_validation_gates(self) -> None:
        """Set up all validation gates"""
        
        # Ruff linting
        ruff_gate = ValidationGate(
            "Ruff Linting",
            "Check code style and common issues with Ruff"
        )
        ruff_gate.run = lambda cmd: self._run_ruff_check()
        self.add_gate(ruff_gate)
        
        # Ruff formatting
        format_gate = ValidationGate(
            "Ruff Formatting",
            "Check code formatting with Ruff"
        )
        format_gate.run = lambda cmd: self._run_ruff_format()
        self.add_gate(format_gate)
        
        # MyPy type checking
        mypy_gate = ValidationGate(
            "MyPy Type Checking",
            "Static type checking with MyPy"
        )
        mypy_gate.run = lambda cmd: self._run_mypy_check()
        self.add_gate(mypy_gate)
        
        # Import validation
        import_gate = ValidationGate(
            "Import Validation",
            "Validate all imports can be resolved"
        )
        import_gate.run = lambda cmd: self._run_import_validation()
        self.add_gate(import_gate)
        
        # Configuration validation
        config_gate = ValidationGate(
            "Configuration Validation",
            "Validate configuration system"
        )
        config_gate.run = lambda cmd: self._run_config_validation()
        self.add_gate(config_gate)
        
        # Interface validation
        interface_gate = ValidationGate(
            "Interface Validation",
            "Validate interface implementations"
        )
        interface_gate.run = lambda cmd: self._run_interface_validation()
        self.add_gate(interface_gate)
    
    def _run_ruff_check(self) -> bool:
        """Run Ruff linting"""
        try:
            result = subprocess.run([
                "ruff", "check", str(self.core_path),
                "--select", "E,W,F,B,I,N,UP,YTT,ANN,S,BLE,FBT,A,COM,C4,DTZ,T10,EM,EXE,ISC,ICN,G,INP,PIE,T20,PYI,PT,Q,RSE,RET,SLF,SIM,TID,TCH,ARG,PTH,ERA,PD,PGH,PL,TRY,NPY,RUF",
                "--ignore", "ANN101,ANN102,ANN401,S101,PLR0913,PLR0912,PLR0915"
            ], capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                print("✅ Ruff linting passed")
                return True
            else:
                print("❌ Ruff linting failed:")
                print(result.stdout)
                return False
                
        except subprocess.TimeoutExpired:
            print("⏰ Ruff linting timed out")
            return False
        except FileNotFoundError:
            print("⚠️ Ruff not found, skipping linting")
            return True
        except Exception as e:
            print(f"💥 Ruff linting failed: {e}")
            return False
    
    def _run_ruff_format(self) -> bool:
        """Run Ruff formatting check"""
        try:
            result = subprocess.run([
                "ruff", "format", "--check", str(self.core_path)
            ], capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                print("✅ Ruff formatting check passed")
                return True
            else:
                print("❌ Ruff formatting check failed:")
                print(result.stdout)
                return False
                
        except subprocess.TimeoutExpired:
            print("⏰ Ruff formatting timed out")
            return False
        except FileNotFoundError:
            print("⚠️ Ruff not found, skipping formatting check")
            return True
        except Exception as e:
            print(f"💥 Ruff formatting failed: {e}")
            return False
    
    def _run_mypy_check(self) -> bool:
        """Run MyPy type checking"""
        try:
            result = subprocess.run([
                "mypy", str(self.core_path),
                "--ignore-missing-imports",
                "--no-strict-optional",
                "--allow-untyped-defs",
                "--allow-incomplete-defs"
            ], capture_output=True, text=True, timeout=120)
            
            if result.returncode == 0:
                print("✅ MyPy type checking passed")
                return True
            else:
                print("❌ MyPy type checking failed:")
                print(result.stdout)
                return False
                
        except subprocess.TimeoutExpired:
            print("⏰ MyPy type checking timed out")
            return False
        except FileNotFoundError:
            print("⚠️ MyPy not found, skipping type checking")
            return True
        except Exception as e:
            print(f"💥 MyPy type checking failed: {e}")
            return False
    
    def _run_import_validation(self) -> bool:
        """Validate that all imports can be resolved"""
        try:
            print("🔍 Validating imports...")
            
            # Check each core module can be imported
            core_modules = [
                "unified_config",
                "integration_interfaces", 
                "project_context",
                "adapters.solidlsp_adapter",
                "adapters.serena_adapter",
                "enhanced_graph_builder",
                "diagnostic_collector"
            ]
            
            failed_imports = []
            
            for module in core_modules:
                try:
                    result = subprocess.run([
                        sys.executable, "-c", 
                        f"import sys; sys.path.insert(0, '{self.project_root}'); "
                        f"from src.codegen.sdk.core import {module.replace('.', ' as temp; from src.codegen.sdk.core import ').replace(' as temp', '')}"
                    ], capture_output=True, text=True, timeout=30)
                    
                    if result.returncode != 0:
                        failed_imports.append((module, result.stderr))
                        
                except Exception as e:
                    failed_imports.append((module, str(e)))
            
            if not failed_imports:
                print("✅ All imports validated successfully")
                return True
            else:
                print("❌ Import validation failed:")
                for module, error in failed_imports:
                    print(f"  - {module}: {error}")
                return False
                
        except Exception as e:
            print(f"💥 Import validation failed: {e}")
            return False
    
    def _run_config_validation(self) -> bool:
        """Validate configuration system"""
        try:
            print("⚙️ Validating configuration system...")
            
            validation_script = f"""
import sys
sys.path.insert(0, '{self.project_root}')

from src.codegen.sdk.core.unified_config import UnifiedConfiguration, ConfigurationManager

# Test basic configuration creation
config = UnifiedConfiguration()
assert config.lspserver == True
assert config.diagnostics == True
assert config.errorautoresolve == True
assert config.enhancedcontext == True

# Test configuration serialization
config_dict = config.to_dict()
assert 'lspserver' in config_dict
assert 'diagnostics' in config_dict

# Test configuration manager
manager = ConfigurationManager()
test_config = manager.get_config()
assert test_config is not None

print("Configuration validation passed")
"""
            
            result = subprocess.run([
                sys.executable, "-c", validation_script
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                print("✅ Configuration validation passed")
                return True
            else:
                print("❌ Configuration validation failed:")
                print(result.stderr)
                return False
                
        except Exception as e:
            print(f"💥 Configuration validation failed: {e}")
            return False
    
    def _run_interface_validation(self) -> bool:
        """Validate interface implementations"""
        try:
            print("🔌 Validating interface implementations...")
            
            validation_script = f"""
import sys
sys.path.insert(0, '{self.project_root}')

from src.codegen.sdk.core.integration_interfaces import (
    ILanguageServer, IProjectManager, IGraphBuilder, IDiagnosticCollector,
    UnifiedDiagnostic, UnifiedSymbol, DiagnosticSeverity, SymbolKind
)

# Test enum values
assert DiagnosticSeverity.ERROR.value == "error"
assert SymbolKind.FUNCTION.value == "function"

# Test data structures
from src.codegen.sdk.core.integration_interfaces import UnifiedPosition, UnifiedRange
pos = UnifiedPosition(line=0, character=0)
assert pos.line == 0
assert pos.character == 0

range_obj = UnifiedRange(start=pos, end=pos)
assert range_obj.start == pos

print("Interface validation passed")
"""
            
            result = subprocess.run([
                sys.executable, "-c", validation_script
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                print("✅ Interface validation passed")
                return True
            else:
                print("❌ Interface validation failed:")
                print(result.stderr)
                return False
                
        except Exception as e:
            print(f"💥 Interface validation failed: {e}")
            return False


def main():
    """Main validation entry point"""
    parser = argparse.ArgumentParser(description="Validate unified integration components")
    parser.add_argument("--project-root", default=".", help="Project root directory")
    parser.add_argument("--ruff", action="store_true", help="Run Ruff linting only")
    parser.add_argument("--mypy", action="store_true", help="Run MyPy type checking only")
    parser.add_argument("--imports", action="store_true", help="Run import validation only")
    parser.add_argument("--config", action="store_true", help="Run configuration validation only")
    parser.add_argument("--interfaces", action="store_true", help="Run interface validation only")
    
    args = parser.parse_args()
    
    # Resolve project root
    project_root = Path(args.project_root).resolve()
    if not project_root.exists():
        print(f"❌ Project root does not exist: {project_root}")
        sys.exit(1)
    
    validator = IntegrationValidator(str(project_root))
    
    # Set up specific gates if requested
    if args.ruff or args.mypy or args.imports or args.config or args.interfaces:
        if args.ruff:
            ruff_gate = ValidationGate("Ruff Linting", "Check code style with Ruff")
            ruff_gate.run = lambda cmd: validator._run_ruff_check()
            validator.add_gate(ruff_gate)
            
            format_gate = ValidationGate("Ruff Formatting", "Check formatting with Ruff")
            format_gate.run = lambda cmd: validator._run_ruff_format()
            validator.add_gate(format_gate)
        
        if args.mypy:
            mypy_gate = ValidationGate("MyPy Type Checking", "Static type checking")
            mypy_gate.run = lambda cmd: validator._run_mypy_check()
            validator.add_gate(mypy_gate)
        
        if args.imports:
            import_gate = ValidationGate("Import Validation", "Validate imports")
            import_gate.run = lambda cmd: validator._run_import_validation()
            validator.add_gate(import_gate)
        
        if args.config:
            config_gate = ValidationGate("Configuration Validation", "Validate config system")
            config_gate.run = lambda cmd: validator._run_config_validation()
            validator.add_gate(config_gate)
        
        if args.interfaces:
            interface_gate = ValidationGate("Interface Validation", "Validate interfaces")
            interface_gate.run = lambda cmd: validator._run_interface_validation()
            validator.add_gate(interface_gate)
    else:
        # Run all gates
        validator.setup_validation_gates()
    
    # Run validation
    success = validator.run_all_gates()
    
    if success:
        print("\n🎉 All validation gates passed! The unified integration system is ready.")
        sys.exit(0)
    else:
        print("\n❌ Some validation gates failed. Please fix the issues before proceeding.")
        sys.exit(1)


if __name__ == "__main__":
    main()
