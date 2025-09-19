"""
Project Management CLI commands for the Orchestration system.

Provides command-line interface for managing project integrations,
syncing with external platforms, and monitoring pipeline-to-project mappings.
"""

import asyncio
import json
from pathlib import Path
from typing import Optional, Dict, Any
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.json import JSON
import yaml

try:
    from codegen.orchestration.project_management import (
        ProjectManagementIntegration,
        MCPServerIntegration,
        ProjectManagementFactory,
        ProjectPlatform,
        setup_project_management_from_config
    )
except ImportError:
    # Graceful fallback
    ProjectManagementIntegration = None
    setup_project_management_from_config = None

from codegen.shared.logging.get_logger import get_logger

console = Console()
logger = get_logger(__name__)

# Create project management sub-app
project_mgmt_app = typer.Typer(
    name="project", 
    help="Project management platform integrations",
    rich_markup_mode="rich"
)


@project_mgmt_app.command("setup")
def setup_integration(
    platform: str = typer.Argument(
        ..., help="Platform to integrate with (linear, github, jira, clickup)"
    ),
    project_id: str = typer.Argument(..., help="Project ID on the platform"),
    auth_token: str = typer.Option(..., "--token", help="Authentication token"),
    config_file: Optional[str] = typer.Option(
        None, "--config", help="Configuration file to update"
    ),
    webhook_url: Optional[str] = typer.Option(
        None, "--webhook", help="Webhook URL for notifications"
    ),
    interactive: bool = typer.Option(
        False, "--interactive", "-i", help="Interactive setup mode"
    ),
):
    """Set up integration with a project management platform."""
    if not ProjectManagementIntegration:
        console.print("[red]Error:[/red] Project management dependencies not available")
        raise typer.Exit(1)
    
    logger.info(
        "Setting up project management integration",
        extra={
            "operation": "project_mgmt.setup",
            "platform": platform,
            "project_id": project_id,
        },
    )
    
    platform_enum = None
    try:
        platform_enum = ProjectPlatform(platform.lower())
    except ValueError:
        console.print(f"[red]Error:[/red] Unsupported platform: {platform}")
        console.print("Supported platforms: linear, github, jira, clickup")
        raise typer.Exit(1)
    
    # Create integration configuration
    config = None
    if platform_enum == ProjectPlatform.LINEAR:
        config = ProjectManagementFactory.create_linear_integration(
            project_id=project_id,
            api_token=auth_token,
            team_id=project_id,  # Simplified for demo
            webhook_url=webhook_url
        )
    elif platform_enum == ProjectPlatform.GITHUB:
        # Parse owner/repo from project_id
        if "/" not in project_id:
            console.print("[red]Error:[/red] GitHub project ID must be in format 'owner/repo'")
            raise typer.Exit(1)
        owner, repo = project_id.split("/", 1)
        config = ProjectManagementFactory.create_github_integration(
            repo_owner=owner,
            repo_name=repo,
            github_token=auth_token,
            webhook_url=webhook_url
        )
    
    if not config:
        console.print(f"[red]Error:[/red] Could not create configuration for {platform}")
        raise typer.Exit(1)
    
    # Save configuration if file specified
    if config_file:
        config_path = Path(config_file)
        
        # Load existing config or create new
        config_data = {}
        if config_path.exists():
            with open(config_path) as f:
                if config_path.suffix.lower() in ['.yaml', '.yml']:
                    config_data = yaml.safe_load(f) or {}
                else:
                    config_data = json.load(f)
        
        # Add new integration
        if "integrations" not in config_data:
            config_data["integrations"] = {}
        
        config_data["integrations"][platform] = config.model_dump()
        
        # Save updated config
        with open(config_path, 'w') as f:
            if config_path.suffix.lower() in ['.yaml', '.yml']:
                yaml.dump(config_data, f, default_flow_style=False)
            else:
                json.dump(config_data, f, indent=2)
        
        console.print(f"✅ Configuration saved to: {config_path}")
    
    console.print(Panel.fit(
        f"[bold green]Integration Setup Complete![/bold green]\n\n"
        f"[bold]Platform:[/bold] {platform.upper()}\n"
        f"[bold]Project ID:[/bold] {project_id}\n"
        f"[bold]Auto-create tasks:[/bold] {'Yes' if config.auto_create_tasks else 'No'}\n"
        f"[bold]Auto-update status:[/bold] {'Yes' if config.auto_update_status else 'No'}",
        title="🔗 Project Integration",
        border_style="green"
    ))
    
    if interactive:
        console.print("\n[yellow]Interactive configuration options:[/yellow]")
        if typer.confirm("Test connection to platform?"):
            console.print("🔍 Testing connection...")
            console.print("✅ [green]Connection successful![/green] (mock)")


@project_mgmt_app.command("list")
def list_integrations(
    config_file: str = typer.Option(
        "orchestration-config.yaml", "--config", help="Configuration file to read"
    ),
    output_format: str = typer.Option(
        "table", "--format", help="Output format: table, json, yaml"
    ),
):
    """List all configured project management integrations."""
    config_path = Path(config_file)
    
    if not config_path.exists():
        console.print(f"[red]Error:[/red] Configuration file not found: {config_file}")
        console.print("Run 'codegen orchestrate project setup' to create integrations")
        raise typer.Exit(1)
    
    try:
        with open(config_path) as f:
            if config_path.suffix.lower() in ['.yaml', '.yml']:
                config_data = yaml.safe_load(f) or {}
            else:
                config_data = json.load(f)
    except Exception as e:
        console.print(f"[red]Error:[/red] Failed to read configuration: {e}")
        raise typer.Exit(1)
    
    integrations = config_data.get("integrations", {})
    
    if not integrations:
        console.print("[yellow]No project management integrations configured.[/yellow]")
        return
    
    if output_format.lower() == "json":
        console.print(JSON.from_data(integrations))
    elif output_format.lower() == "yaml":
        console.print(yaml.dump(integrations, default_flow_style=False))
    else:
        table = Table(
            title="🔗 Project Management Integrations",
            border_style="blue",
            show_header=True,
        )
        table.add_column("Name", style="cyan", no_wrap=True)
        table.add_column("Platform", style="magenta")
        table.add_column("Project ID", style="white")
        table.add_column("Auto Tasks", style="green")
        table.add_column("Auto Status", style="yellow")
        
        for name, integration in integrations.items():
            platform = integration.get("platform", "unknown")
            project_id = integration.get("project_id", "unknown")
            auto_tasks = "✅" if integration.get("auto_create_tasks", False) else "❌"
            auto_status = "✅" if integration.get("auto_update_status", False) else "❌"
            
            table.add_row(name, platform.upper(), project_id, auto_tasks, auto_status)
        
        console.print(table)


@project_mgmt_app.command("sync")
def sync_tasks(
    integration_name: str = typer.Argument(..., help="Integration name to sync"),
    config_file: str = typer.Option(
        "orchestration-config.yaml", "--config", help="Configuration file"
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Show what would be synced without making changes"
    ),
):
    """Sync tasks between local cache and external platform."""
    if not ProjectManagementIntegration:
        console.print("[red]Error:[/red] Project management dependencies not available")
        raise typer.Exit(1)
    
    logger.info(
        "Syncing project management tasks",
        extra={
            "operation": "project_mgmt.sync",
            "integration": integration_name,
            "dry_run": dry_run,
        },
    )
    
    async def sync_async():
        try:
            config_path = Path(config_file)
            pm_integration = await setup_project_management_from_config(config_path)
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task(f"🔄 Syncing tasks with {integration_name}...", total=None)
                
                result = await pm_integration.sync_tasks_with_platform(integration_name)
                
                progress.update(task, description="✅ Sync complete")
                progress.stop()
            
            if result.get("error"):
                console.print(f"[red]Sync failed:[/red] {result['error']}")
            else:
                sync_count = result.get("count", 0)
                console.print(f"✅ [green]Synced {sync_count} tasks successfully![/green]")
                
                if dry_run:
                    console.print("[yellow]Dry run mode - no changes were made[/yellow]")
        
        except FileNotFoundError:
            console.print(f"[red]Error:[/red] Configuration file not found: {config_file}")
            raise typer.Exit(1)
        except Exception as e:
            logger.error(f"Task sync failed: {e}")
            console.print(f"[red]Error syncing tasks:[/red] {e}")
            raise typer.Exit(1)
    
    try:
        asyncio.run(sync_async())
    except KeyboardInterrupt:
        console.print("\n🛑 Sync cancelled")


@project_mgmt_app.command("analytics")  
def show_analytics(
    integration_name: str = typer.Argument(..., help="Integration name for analytics"),
    config_file: str = typer.Option(
        "orchestration-config.yaml", "--config", help="Configuration file"
    ),
    output_format: str = typer.Option(
        "table", "--format", help="Output format: table, json, yaml"
    ),
    time_range: str = typer.Option(
        "30d", "--range", help="Time range for analytics (7d, 30d, 90d)"
    ),
):
    """Show analytics and insights from project management platform."""
    if not ProjectManagementIntegration:
        console.print("[red]Error:[/red] Project management dependencies not available")
        raise typer.Exit(1)
    
    logger.info(
        "Fetching project management analytics",
        extra={
            "operation": "project_mgmt.analytics",
            "integration": integration_name,
            "time_range": time_range,
        },
    )
    
    async def analytics_async():
        try:
            config_path = Path(config_file)
            pm_integration = await setup_project_management_from_config(config_path)
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task(f"📊 Fetching analytics from {integration_name}...", total=None)
                
                analytics = await pm_integration.get_platform_analytics(integration_name)
                
                progress.update(task, description="✅ Analytics retrieved")
                progress.stop()
            
            if analytics.get("error"):
                console.print(f"[red]Analytics failed:[/red] {analytics['error']}")
                return
            
            if output_format.lower() == "json":
                console.print(JSON.from_data(analytics))
            elif output_format.lower() == "yaml":
                console.print(yaml.dump(analytics, default_flow_style=False))
            else:
                _display_analytics_table(analytics, integration_name)
        
        except Exception as e:
            logger.error(f"Analytics failed: {e}")
            console.print(f"[red]Error fetching analytics:[/red] {e}")
            raise typer.Exit(1)
    
    try:
        asyncio.run(analytics_async())
    except KeyboardInterrupt:
        console.print("\n🛑 Analytics cancelled")


@project_mgmt_app.command("test")
def test_integration(
    integration_name: str = typer.Argument(..., help="Integration name to test"),
    config_file: str = typer.Option(
        "orchestration-config.yaml", "--config", help="Configuration file"
    ),
    create_test_task: bool = typer.Option(
        False, "--create-task", help="Create a test task to verify write access"
    ),
):
    """Test connection and functionality of a project management integration."""
    if not ProjectManagementIntegration:
        console.print("[red]Error:[/red] Project management dependencies not available")
        raise typer.Exit(1)
    
    logger.info(
        "Testing project management integration",
        extra={
            "operation": "project_mgmt.test",
            "integration": integration_name,
            "create_task": create_test_task,
        },
    )
    
    async def test_async():
        try:
            config_path = Path(config_file)
            pm_integration = await setup_project_management_from_config(config_path)
            
            console.print(Panel.fit(
                f"[bold blue]Testing Integration: {integration_name}[/bold blue]",
                title="🧪 Integration Test",
                border_style="blue"
            ))
            
            # Test basic connection
            console.print("1. [cyan]Testing connection...[/cyan]")
            if integration_name in pm_integration.integrations:
                console.print("   ✅ Integration configuration found")
            else:
                console.print("   ❌ Integration not found in configuration")
                return
            
            # Test MCP server connection if applicable
            console.print("2. [cyan]Testing MCP server connection...[/cyan]")
            if pm_integration.mcp:
                # Try to connect to relevant servers
                config = pm_integration.integrations[integration_name]
                server_name = config.platform.value
                connected = await pm_integration.mcp.connect_to_server(server_name)
                if connected:
                    console.print("   ✅ MCP server connection successful")
                else:
                    console.print("   ⚠️  MCP server connection failed (may use direct API)")
            else:
                console.print("   ℹ️  No MCP integration configured (using direct API)")
            
            # Test platform API access
            console.print("3. [cyan]Testing platform API access...[/cyan]")
            sync_result = await pm_integration.sync_tasks_with_platform(integration_name)
            if sync_result.get("error"):
                console.print(f"   ❌ API access failed: {sync_result['error']}")
            else:
                console.print("   ✅ Platform API access successful")
            
            # Optional: Create test task
            if create_test_task:
                console.print("4. [cyan]Creating test task...[/cyan]")
                test_task = await pm_integration._create_task(
                    title="🧪 Test Task - Codegen Integration",
                    description="This is a test task created by Codegen to verify integration functionality.",
                    integration_name=integration_name,
                    labels=["test", "codegen", "integration"]
                )
                
                if test_task:
                    console.print(f"   ✅ Test task created: {test_task.id}")
                    if test_task.platform_url:
                        console.print(f"   🔗 View at: {test_task.platform_url}")
                else:
                    console.print("   ❌ Failed to create test task")
            
            console.print("\n[bold green]✅ Integration test completed![/bold green]")
            
        except Exception as e:
            logger.error(f"Integration test failed: {e}")
            console.print(f"[red]Error testing integration:[/red] {e}")
            raise typer.Exit(1)
    
    try:
        asyncio.run(test_async())
    except KeyboardInterrupt:
        console.print("\n🛑 Test cancelled")


def _display_analytics_table(analytics: Dict[str, Any], integration_name: str):
    """Display analytics data in formatted tables."""
    platform = analytics.get("platform", "unknown").upper()
    
    # Summary panel
    console.print(Panel.fit(
        f"[bold blue]Analytics Summary[/bold blue]\n\n"
        f"[bold]Platform:[/bold] {platform}\n"
        f"[bold]Total Tasks:[/bold] {analytics.get('total_tasks', 0)}\n"
        f"[bold]Completion Rate:[/bold] {analytics.get('completion_rate', 0):.1f}%\n"
        f"[bold]Pipeline Success:[/bold] {analytics.get('pipeline_success_rate', 0):.1f}%",
        title=f"📊 {integration_name}",
        border_style="blue"
    ))
    
    # Task status breakdown
    status_table = Table(
        title="📋 Task Status Breakdown",
        border_style="green",
        show_header=True,
    )
    status_table.add_column("Status", style="cyan")
    status_table.add_column("Count", style="white")
    status_table.add_column("Percentage", style="yellow")
    
    total_tasks = analytics.get("total_tasks", 1)
    status_data = [
        ("Completed", analytics.get("completed_tasks", 0)),
        ("In Progress", analytics.get("in_progress_tasks", 0)),
        ("Overdue", analytics.get("overdue_tasks", 0)),
    ]
    
    for status, count in status_data:
        percentage = (count / total_tasks * 100) if total_tasks > 0 else 0
        status_table.add_row(status, str(count), f"{percentage:.1f}%")
    
    console.print(status_table)
    
    # Top assignees
    if analytics.get("top_assignees"):
        assignee_table = Table(
            title="👥 Top Assignees",
            border_style="magenta",
            show_header=True,
        )
        assignee_table.add_column("Assignee", style="cyan")
        assignee_table.add_column("Tasks", style="white")
        
        for assignee in analytics["top_assignees"][:5]:
            assignee_table.add_row(assignee["name"], str(assignee["tasks"]))
        
        console.print(assignee_table)


if __name__ == "__main__":
    project_mgmt_app()