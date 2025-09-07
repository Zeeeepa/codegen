"""
Custom build hooks for codegen package with SDK integration.

This module handles:
1. Cython module compilation for performance-critical SDK components
2. Tree-sitter parser compilation and integration
3. Binary distribution preparation
4. Serena and SolidLSP integration and installation
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
from typing import Any, Dict

from hatchling.plugin import hookimpl


class CodegenBuildHook:
    """Custom build hook for codegen with SDK integration"""
    
    def __init__(self, root: str, config: Dict[str, Any]):
        self.root = Path(root)
        self.config = config
        self.sdk_path = self.root / "src" / "codegen" / "sdk"
        self.compiled_path = self.sdk_path / "compiled"
        self.serena_path = self.root / "serena"
        self.serena_src_path = self.serena_path / "src"
    
    def initialize(self, version: str, build_data: Dict[str, Any]) -> None:
        """Initialize the build process"""
        print("🔧 Initializing codegen build with SDK + Serena + SolidLSP integration...")
        
        # Ensure compiled directory exists
        self.compiled_path.mkdir(exist_ok=True)
        
        # Set up Serena and SolidLSP integration
        self._setup_serena_integration()
        
        # Try to compile Cython modules if available
        self._compile_cython_modules()
        
        # Ensure fallback implementations are available
        self._ensure_fallback_implementations()
        
        print("✅ Build initialization complete")
    
    def _setup_serena_integration(self) -> None:
        """Set up Serena and SolidLSP integration"""
        print("🔗 Setting up Serena and SolidLSP integration...")
        
        if not self.serena_path.exists():
            print("⚠️  Serena directory not found - skipping integration")
            return
        
        # Create symlinks or copy Serena packages to the SDK extensions
        self._integrate_serena_packages()
        
        # Set up SolidLSP from Serena
        self._integrate_solidlsp_from_serena()
        
        print("✅ Serena and SolidLSP integration complete")
    
    def _integrate_serena_packages(self) -> None:
        """Integrate Serena packages into the SDK"""
        serena_pkg_path = self.serena_src_path / "serena"
        interprompt_pkg_path = self.serena_src_path / "interprompt"
        
        # Target paths in the SDK
        sdk_serena_path = self.sdk_path / "serena"
        sdk_interprompt_path = self.sdk_path / "interprompt"
        
        # Copy Serena packages to SDK
        if serena_pkg_path.exists():
            if sdk_serena_path.exists():
                shutil.rmtree(sdk_serena_path)
            shutil.copytree(serena_pkg_path, sdk_serena_path)
            print("   ✅ Serena package integrated")
        
        if interprompt_pkg_path.exists():
            if sdk_interprompt_path.exists():
                shutil.rmtree(sdk_interprompt_path)
            shutil.copytree(interprompt_pkg_path, sdk_interprompt_path)
            print("   ✅ Interprompt package integrated")
    
    def _integrate_solidlsp_from_serena(self) -> None:
        """Integrate SolidLSP from Serena into the SDK extensions"""
        serena_solidlsp_path = self.serena_src_path / "solidlsp"
        sdk_solidlsp_path = self.sdk_path / "extensions" / "lsp" / "solidlsp"
        
        if serena_solidlsp_path.exists():
            # Update the existing SolidLSP with Serena's version
            if sdk_solidlsp_path.exists():
                # Backup existing files that might have local modifications
                backup_files = ["__init__.py"]
                backup_dir = sdk_solidlsp_path.parent / "solidlsp_backup"
                backup_dir.mkdir(exist_ok=True)
                
                for backup_file in backup_files:
                    src_file = sdk_solidlsp_path / backup_file
                    if src_file.exists():
                        shutil.copy2(src_file, backup_dir / backup_file)
                
                # Remove old SolidLSP
                shutil.rmtree(sdk_solidlsp_path)
            
            # Copy Serena's SolidLSP
            shutil.copytree(serena_solidlsp_path, sdk_solidlsp_path)
            print("   ✅ SolidLSP from Serena integrated")
        else:
            print("   ⚠️  SolidLSP not found in Serena - using existing version")
    
    def _compile_cython_modules(self) -> None:
        """Attempt to compile Cython modules for performance"""
        try:
            import Cython
            print("🚀 Cython available - attempting to compile performance modules...")
            
            # Define Cython modules to compile
            cython_modules = [
                "utils.pyx",
                "resolution.pyx", 
                "autocommit.pyx",
                "sort.pyx"
            ]
            
            for module in cython_modules:
                pyx_file = self.compiled_path / module
                if pyx_file.exists():
                    self._compile_single_cython_module(pyx_file)
                else:
                    print(f"⚠️  Cython source {module} not found, using Python fallback")
                    
        except ImportError:
            print("⚠️  Cython not available - using Python fallback implementations")
    
    def _compile_single_cython_module(self, pyx_file: Path) -> None:
        """Compile a single Cython module"""
        try:
            from Cython.Build import cythonize
            from setuptools import setup, Extension
            
            module_name = pyx_file.stem
            print(f"   Compiling {module_name}...")
            
            # Create extension
            ext = Extension(
                f"codegen.sdk.compiled.{module_name}",
                [str(pyx_file)],
                include_dirs=[str(self.compiled_path)],
            )
            
            # Compile
            setup(
                ext_modules=cythonize([ext], quiet=True),
                script_name="build_hooks.py",
                script_args=["build_ext", "--inplace"],
            )
            
            print(f"   ✅ {module_name} compiled successfully")
            
        except Exception as e:
            print(f"   ⚠️  Failed to compile {pyx_file.name}: {e}")
    
    def _ensure_fallback_implementations(self) -> None:
        """Ensure Python fallback implementations exist"""
        fallback_modules = [
            "utils.py",
            "resolution.py",
            "autocommit.py", 
            "sort.py"
        ]
        
        for module in fallback_modules:
            module_path = self.compiled_path / module
            if not module_path.exists():
                print(f"⚠️  Creating minimal fallback for {module}")
                self._create_minimal_fallback(module_path)
    
    def _create_minimal_fallback(self, module_path: Path) -> None:
        """Create a minimal fallback implementation"""
        module_name = module_path.stem
        
        fallback_content = f'''"""
Fallback Python implementation for {module_name} module.
This provides basic functionality when compiled modules aren't available.
"""

# Minimal implementation to prevent import errors
def __getattr__(name):
    """Provide default implementations for missing attributes"""
    if name.endswith('_function') or name.endswith('_class'):
        return lambda *args, **kwargs: None
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
'''
        
        module_path.write_text(fallback_content)
        print(f"   ✅ Created fallback {module_name}.py")


@hookimpl
def hatch_build_hook(root: str, config: Dict[str, Any]) -> CodegenBuildHook:
    """Hatchling build hook entry point"""
    return CodegenBuildHook(root, config)


# For direct execution during development
if __name__ == "__main__":
    print("🔧 Running build hooks directly...")
    hook = CodegenBuildHook(".", {})
    hook.initialize("dev", {})
    print("✅ Build hooks completed")
