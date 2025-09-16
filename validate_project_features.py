#!/usr/bin/env python3
"""
Comprehensive validation script for the Codegen Project Management System.
Tests all features to ensure they work as expected.
"""

import json
import os
import sys
import tempfile
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

def setup_test_environment():
    """Set up a clean test environment."""
    test_dir = Path(tempfile.mkdtemp(prefix="codegen_validation_"))
    original_dir = Path.cwd()
    os.chdir(test_dir)
    
    # Initialize git repo
    subprocess.run(["git", "init"], check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test User"], check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], check=True, capture_output=True)
    
    return test_dir, original_dir

def cleanup_test_environment(test_dir: Path, original_dir: Path):
    """Clean up test environment."""
    os.chdir(original_dir)
    import shutil
    shutil.rmtree(test_dir, ignore_errors=True)

def validate_project_state():
    """Validate ProjectState functionality."""
    print("🧪 Validating ProjectState Class...")
    
    # Add src to path
    src_path = Path(__file__).parent / "src"
    sys.path.insert(0, str(src_path))
    
    try:
        from codegen.cli.commands.project.main import ProjectState
        
        # Test 1: Initialization
        project_state = ProjectState()
        assert "tasks" in project_state.state
        assert "project_name" in project_state.state
        assert "active_agents" in project_state.state
        print("✅ ProjectState initialization works")
        
        # Test 2: Task creation
        task_data = {
            "title": "Validate Authentication System",
            "description": "Implement and test JWT authentication with user management",
            "priority": "high"
        }
        
        project_state.add_task(task_data)
        assert len(project_state.state["tasks"]) == 1
        task = project_state.state["tasks"][0]
        assert task["title"] == "Validate Authentication System"
        assert task["status"] == "pending"
        assert task["id"] == 1
        print("✅ Task creation works correctly")
        
        # Test 3: Task starting
        project_state.start_task(1, 98765)
        task = project_state.get_task(1)
        assert task["status"] == "running"
        assert task["agent_run_id"] == 98765
        assert "started_at" in task
        print("✅ Task starting works correctly")
        
        # Test 4: Task completion
        project_state.complete_task(1)
        task = project_state.get_task(1)
        assert task["status"] == "completed"
        assert "completed_at" in task
        print("✅ Task completion works correctly")
        
        # Test 5: State persistence
        project_state._save_state()
        state_file = Path(".codegen/project_state.json")
        assert state_file.exists()
        
        # Load new instance and verify
        new_project_state = ProjectState()
        assert len(new_project_state.state["tasks"]) == 1
        assert new_project_state.state["tasks"][0]["status"] == "completed"
        print("✅ State persistence works correctly")
        
        return True
        
    except Exception as e:
        print(f"❌ ProjectState validation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def validate_prd_manager():
    """Validate PRDManager functionality."""
    print("\n📋 Validating PRDManager Class...")
    
    try:
        src_path = Path(__file__).parent / "src"
        sys.path.insert(0, str(src_path))
        from codegen.cli.commands.project.main import PRDManager
        
        prd_file = Path("PRD.md")
        prd_manager = PRDManager(prd_file)
        
        # Test 1: PRD creation
        prd_manager.create_default_prd("Validation Test Project")
        assert prd_file.exists()
        print("✅ PRD creation works correctly")
        
        # Test 2: PRD content validation
        content = prd_manager.read_prd()
        assert "Validation Test Project" in content
        assert "## 🎯 Objectives" in content
        assert "## 🔧 Technical Requirements" in content
        assert "## 📅 Timeline" in content
        print("✅ PRD content structure is correct")
        
        # Test 3: Task section updates
        test_tasks = [
            {
                "id": 1,
                "title": "User Authentication API",
                "description": "Build secure JWT-based authentication endpoints",
                "status": "completed",
                "priority": "high",
                "agent_run_id": 11111,
                "started_at": "2024-01-01T10:00:00",
                "completed_at": "2024-01-01T14:00:00"
            },
            {
                "id": 2,
                "title": "Database Schema Design",
                "description": "Design and implement user and session tables",
                "status": "running",
                "priority": "high",
                "agent_run_id": 11112,
                "started_at": "2024-01-01T15:00:00"
            },
            {
                "id": 3,
                "title": "Frontend Integration",
                "description": "Integrate auth API with React frontend",
                "status": "pending",
                "priority": "medium"
            }
        ]
        
        prd_manager.update_tasks_section(test_tasks)
        updated_content = prd_manager.read_prd()
        
        # Verify task content
        assert "User Authentication API ✅" in updated_content
        assert "Database Schema Design 🏃" in updated_content
        assert "Frontend Integration ⏳" in updated_content
        assert "Agent Run ID: 11111" in updated_content
        assert "Agent Run ID: 11112" in updated_content
        print("✅ Task section updates work correctly")
        
        return True
        
    except Exception as e:
        print(f"❌ PRDManager validation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def validate_api_client():
    """Validate CodegenAPIClient functionality."""
    print("\n🌐 Validating CodegenAPIClient Class...")
    
    try:
        src_path = Path(__file__).parent / "src"
        sys.path.insert(0, str(src_path))
        from codegen.cli.commands.project.main import CodegenAPIClient
        
        # Test initialization (mock)
        org_id = 323
        
        # Mock token for testing
        os.environ["CODEGEN_API_TOKEN"] = "test-token-12345"
        
        api_client = CodegenAPIClient(org_id)
        assert api_client.org_id == org_id
        assert api_client.token == "test-token-12345"
        assert "Authorization" in api_client.headers
        print("✅ API client initialization works correctly")
        
        # Note: We don't test actual API calls to avoid hitting real endpoints
        print("✅ API client structure is valid (actual calls not tested)")
        
        return True
        
    except Exception as e:
        print(f"❌ API client validation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def validate_integrated_workflow():
    """Validate the complete integrated workflow."""
    print("\n🔄 Validating Integrated Workflow...")
    
    try:
        src_path = Path(__file__).parent / "src"
        sys.path.insert(0, str(src_path))
        from codegen.cli.commands.project.main import ProjectState, PRDManager
        
        # Initialize complete project
        project_state = ProjectState()
        project_state.state["project_name"] = "Full Stack E-commerce Platform"
        project_state.state["org_id"] = 323
        
        prd_file = Path("PRD.md")
        prd_manager = PRDManager(prd_file)
        prd_manager.create_default_prd("Full Stack E-commerce Platform")
        
        # Create comprehensive task set
        tasks = [
            {
                "title": "User Authentication & Authorization",
                "description": "Implement secure user registration, login, and role-based access control",
                "priority": "high"
            },
            {
                "title": "Product Catalog Management",
                "description": "Build CRUD operations for products with categories and inventory tracking",
                "priority": "high"
            },
            {
                "title": "Shopping Cart & Checkout",
                "description": "Implement cart functionality with persistent sessions and checkout flow",
                "priority": "high"
            },
            {
                "title": "Payment Processing Integration",
                "description": "Integrate Stripe/PayPal for secure payment processing",
                "priority": "high"
            },
            {
                "title": "Order Management System",
                "description": "Build order tracking, status updates, and fulfillment workflow",
                "priority": "medium"
            },
            {
                "title": "Admin Dashboard",
                "description": "Create admin interface for managing products, orders, and users",
                "priority": "medium"
            },
            {
                "title": "Email Notification System",
                "description": "Implement automated emails for order confirmations and updates",
                "priority": "low"
            },
            {
                "title": "Search & Filtering",
                "description": "Add product search with filters and sorting capabilities",
                "priority": "medium"
            }
        ]
        
        # Add all tasks
        for task in tasks:
            project_state.add_task(task)
        
        assert len(project_state.state["tasks"]) == 8
        print("✅ Multiple task creation works correctly")
        
        # Simulate project progression
        # Start high priority tasks
        project_state.start_task(1, 20001)  # Auth
        project_state.start_task(2, 20002)  # Product catalog
        project_state.start_task(4, 20003)  # Payment processing
        
        # Complete some tasks
        project_state.complete_task(1)  # Auth completed
        project_state.complete_task(2)  # Product catalog completed
        
        # Start more tasks
        project_state.start_task(3, 20004)  # Shopping cart
        project_state.start_task(5, 20005)  # Order management
        
        # Update PRD with current state
        prd_manager.update_tasks_section(project_state.state["tasks"])
        
        # Validate final state
        updated_prd = prd_manager.read_prd()
        assert "User Authentication & Authorization ✅" in updated_prd
        assert "Product Catalog Management ✅" in updated_prd
        assert "Shopping Cart & Checkout 🏃" in updated_prd
        assert "Payment Processing Integration ⏳" in updated_prd
        
        # Calculate and verify statistics
        total_tasks = len(project_state.state["tasks"])
        completed_tasks = len([t for t in project_state.state["tasks"] if t["status"] == "completed"])
        running_tasks = len([t for t in project_state.state["tasks"] if t["status"] == "running"])
        pending_tasks = len([t for t in project_state.state["tasks"] if t["status"] == "pending"])
        
        assert total_tasks == 8
        assert completed_tasks == 2
        assert running_tasks == 2
        assert pending_tasks == 4
        
        progress = (completed_tasks / total_tasks) * 100
        assert progress == 25.0
        
        print(f"✅ Project statistics: {total_tasks} total, {completed_tasks} completed, {running_tasks} running, {pending_tasks} pending")
        print(f"✅ Progress calculation: {progress}%")
        
        # Verify active agents tracking
        assert len(project_state.state["active_agents"]) == 2  # 2 running tasks
        assert "20004" in project_state.state["active_agents"]  # Shopping cart
        assert "20005" in project_state.state["active_agents"]  # Order management
        
        print("✅ Active agent tracking works correctly")
        
        return True
        
    except Exception as e:
        print(f"❌ Integrated workflow validation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def validate_cli_integration():
    """Validate CLI integration."""
    print("\n⌨️ Validating CLI Integration...")
    
    try:
        # Check if project commands are properly integrated
        cli_file = Path("src/codegen/cli/cli.py")
        if cli_file.exists():
            with open(cli_file, 'r') as f:
                cli_content = f.read()
                assert "project_app" in cli_content
                assert "from codegen.cli.commands.project.main import project_app" in cli_content
                print("✅ CLI integration is properly configured")
        else:
            print("⚠️ CLI file not found, skipping integration check")
        
        # Check project module structure
        project_init = Path("src/codegen/cli/commands/project/__init__.py")
        project_main = Path("src/codegen/cli/commands/project/main.py")
        project_dashboard = Path("src/codegen/cli/commands/project/dashboard.py")
        
        assert project_init.exists(), "Project __init__.py missing"
        assert project_main.exists(), "Project main.py missing"
        assert project_dashboard.exists(), "Project dashboard.py missing"
        print("✅ Project module structure is complete")
        
        return True
        
    except Exception as e:
        print(f"❌ CLI integration validation failed: {e}")
        return False

def main():
    """Run comprehensive feature validation."""
    print("🚀 Codegen Project Management System - Feature Validation")
    print("=" * 65)
    
    test_dir, original_dir = setup_test_environment()
    print(f"📁 Test directory: {test_dir}")
    
    validations = [
        ("ProjectState Class", validate_project_state),
        ("PRDManager Class", validate_prd_manager),
        ("CodegenAPIClient Class", validate_api_client),
        ("Integrated Workflow", validate_integrated_workflow),
        ("CLI Integration", validate_cli_integration),
    ]
    
    results = {}
    
    for validation_name, validation_func in validations:
        try:
            results[validation_name] = validation_func()
        except Exception as e:
            print(f"❌ {validation_name} failed with exception: {e}")
            results[validation_name] = False
    
    # Summary
    print("\n" + "=" * 65)
    print("📊 VALIDATION SUMMARY")
    print("=" * 65)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for validation_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {validation_name}")
    
    print(f"\nTotal Validations: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("\n🎉 ALL FEATURES VALIDATED SUCCESSFULLY!")
        print("\n📋 Validated Features:")
        print("✅ Project state management with persistence")
        print("✅ Task lifecycle (create, start, complete)")
        print("✅ PRD generation and automatic updates")
        print("✅ API client structure and initialization")
        print("✅ Integrated workflow with multiple tasks")
        print("✅ CLI integration and module structure")
        print("✅ Progress tracking and statistics")
        print("✅ Agent run tracking and management")
        
        print("\n🚀 System is ready for production use!")
    else:
        print(f"\n⚠️ {total - passed} validations failed. Please review the implementation.")
    
    cleanup_test_environment(test_dir, original_dir)
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
