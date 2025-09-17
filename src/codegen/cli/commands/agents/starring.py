"""Agent run starring functionality for Codegen CLI."""

import typer
from rich.console import Console
from rich.table import Table

from codegen.cli.storage.dashboard_db import get_dashboard_db
from codegen.cli.storage.models import StarredAgent
from codegen.shared.logging.get_logger import get_logger

logger = get_logger(__name__)
console = Console()


def star_agent_command(
    agent_id: str = typer.Argument(..., help="Agent run ID to star"),
    metadata: str = typer.Option("", "--metadata", "-m", help="Optional metadata as JSON string")
):
    """Star an agent run for easy access."""
    try:
        db = get_dashboard_db()
        
        # Parse metadata if provided
        import json
        metadata_dict = {}
        if metadata:
            try:
                metadata_dict = json.loads(metadata)
            except json.JSONDecodeError:
                console.print(f"[red]Invalid JSON metadata: {metadata}[/red]")
                raise typer.Exit(1)
        
        # Star the agent
        success = db.star_agent(agent_id, metadata_dict)
        
        if success:
            console.print(f"[green]✓[/green] Agent run [bold]{agent_id}[/bold] has been starred!")
            logger.info(f"Agent starred via CLI: {agent_id}", 
                       extra={"operation": "cli.star_agent", "agent_id": agent_id})
        else:
            console.print(f"[red]✗[/red] Failed to star agent run [bold]{agent_id}[/bold]")
            raise typer.Exit(1)
            
    except Exception as e:
        console.print(f"[red]Error starring agent: {e}[/red]")
        logger.error(f"Failed to star agent {agent_id}: {e}", 
                    extra={"operation": "cli.star_agent_error", "agent_id": agent_id})
        raise typer.Exit(1)


def unstar_agent_command(
    agent_id: str = typer.Argument(..., help="Agent run ID to unstar")
):
    """Unstar an agent run."""
    try:
        db = get_dashboard_db()
        
        # Check if agent is currently starred
        if not db.is_agent_starred(agent_id):
            console.print(f"[yellow]Agent run [bold]{agent_id}[/bold] is not currently starred[/yellow]")
            return
        
        # Unstar the agent
        success = db.unstar_agent(agent_id)
        
        if success:
            console.print(f"[green]✓[/green] Agent run [bold]{agent_id}[/bold] has been unstarred")
            logger.info(f"Agent unstarred via CLI: {agent_id}", 
                       extra={"operation": "cli.unstar_agent", "agent_id": agent_id})
        else:
            console.print(f"[red]✗[/red] Failed to unstar agent run [bold]{agent_id}[/bold]")
            raise typer.Exit(1)
            
    except Exception as e:
        console.print(f"[red]Error unstarring agent: {e}[/red]")
        logger.error(f"Failed to unstar agent {agent_id}: {e}", 
                    extra={"operation": "cli.unstar_agent_error", "agent_id": agent_id})
        raise typer.Exit(1)


def list_starred_agents_command(
    limit: int = typer.Option(20, "--limit", "-l", help="Maximum number of starred agents to show"),
    show_metadata: bool = typer.Option(False, "--metadata", "-m", help="Show metadata for starred agents")
):
    """List all starred agent runs."""
    try:
        db = get_dashboard_db()
        starred_agents = db.get_starred_agents()
        
        if not starred_agents:
            console.print("[yellow]No starred agent runs found[/yellow]")
            console.print("Use [bold]codegen star <agent_id>[/bold] to star an agent run")
            return
        
        # Limit results
        if limit > 0:
            starred_agents = starred_agents[:limit]
        
        # Create table
        table = Table(title=f"Starred Agent Runs ({len(starred_agents)} total)")
        table.add_column("Agent ID", style="cyan", no_wrap=True)
        table.add_column("Starred At", style="green")
        
        if show_metadata:
            table.add_column("Metadata", style="dim")
        
        for agent in starred_agents:
            row = [
                agent['agent_id'],
                agent['starred_at'][:19] if agent['starred_at'] else "Unknown"  # Format timestamp
            ]
            
            if show_metadata:
                import json
                metadata = json.loads(agent.get('metadata', '{}'))
                metadata_str = json.dumps(metadata, indent=2) if metadata else "None"
                row.append(metadata_str)
            
            table.add_row(*row)
        
        console.print(table)
        
        # Show usage hints
        console.print("\n[dim]Commands:[/dim]")
        console.print("  [bold]codegen unstar <agent_id>[/bold] - Unstar an agent")
        console.print("  [bold]codegen resume <agent_id>[/bold] - Resume a starred agent")
        console.print("  [bold]codegen tui[/bold] - Open dashboard to manage starred agents")
        
        logger.info(f"Listed {len(starred_agents)} starred agents via CLI", 
                   extra={"operation": "cli.list_starred", "count": len(starred_agents)})
        
    except Exception as e:
        console.print(f"[red]Error listing starred agents: {e}[/red]")
        logger.error(f"Failed to list starred agents: {e}", 
                    extra={"operation": "cli.list_starred_error"})
        raise typer.Exit(1)


def check_agent_starred_command(
    agent_id: str = typer.Argument(..., help="Agent run ID to check")
):
    """Check if an agent run is starred."""
    try:
        db = get_dashboard_db()
        is_starred = db.is_agent_starred(agent_id)
        
        if is_starred:
            console.print(f"[green]✓[/green] Agent run [bold]{agent_id}[/bold] is starred")
        else:
            console.print(f"[dim]Agent run [bold]{agent_id}[/bold] is not starred[/dim]")
            console.print(f"Use [bold]codegen star {agent_id}[/bold] to star it")
        
        logger.debug(f"Checked agent starred status: {agent_id} = {is_starred}", 
                    extra={"operation": "cli.check_starred", "agent_id": agent_id, "starred": is_starred})
        
    except Exception as e:
        console.print(f"[red]Error checking agent status: {e}[/red]")
        logger.error(f"Failed to check if agent {agent_id} is starred: {e}", 
                    extra={"operation": "cli.check_starred_error", "agent_id": agent_id})
        raise typer.Exit(1)


def toggle_agent_star_command(
    agent_id: str = typer.Argument(..., help="Agent run ID to toggle star status")
):
    """Toggle star status of an agent run."""
    try:
        db = get_dashboard_db()
        is_starred = db.is_agent_starred(agent_id)
        
        if is_starred:
            # Unstar
            success = db.unstar_agent(agent_id)
            if success:
                console.print(f"[yellow]★ → ☆[/yellow] Agent run [bold]{agent_id}[/bold] unstarred")
            else:
                console.print(f"[red]✗[/red] Failed to unstar agent run [bold]{agent_id}[/bold]")
                raise typer.Exit(1)
        else:
            # Star
            success = db.star_agent(agent_id)
            if success:
                console.print(f"[yellow]☆ → ★[/yellow] Agent run [bold]{agent_id}[/bold] starred")
            else:
                console.print(f"[red]✗[/red] Failed to star agent run [bold]{agent_id}[/bold]")
                raise typer.Exit(1)
        
        logger.info(f"Toggled agent star status: {agent_id} -> {'unstarred' if is_starred else 'starred'}", 
                   extra={"operation": "cli.toggle_star", "agent_id": agent_id, "action": "unstar" if is_starred else "star"})
        
    except Exception as e:
        console.print(f"[red]Error toggling agent star: {e}[/red]")
        logger.error(f"Failed to toggle star for agent {agent_id}: {e}", 
                    extra={"operation": "cli.toggle_star_error", "agent_id": agent_id})
        raise typer.Exit(1)


def bulk_star_agents_command(
    agent_ids: str = typer.Argument(..., help="Comma-separated list of agent IDs to star"),
    force: bool = typer.Option(False, "--force", "-f", help="Force star even if already starred")
):
    """Star multiple agent runs at once."""
    try:
        db = get_dashboard_db()
        
        # Parse agent IDs
        ids = [aid.strip() for aid in agent_ids.split(',') if aid.strip()]
        if not ids:
            console.print("[red]No valid agent IDs provided[/red]")
            raise typer.Exit(1)
        
        console.print(f"Starring {len(ids)} agent runs...")
        
        success_count = 0
        skip_count = 0
        error_count = 0
        
        for agent_id in ids:
            try:
                # Check if already starred
                if not force and db.is_agent_starred(agent_id):
                    console.print(f"[dim]Skipping {agent_id} (already starred)[/dim]")
                    skip_count += 1
                    continue
                
                # Star the agent
                if db.star_agent(agent_id):
                    console.print(f"[green]✓[/green] Starred {agent_id}")
                    success_count += 1
                else:
                    console.print(f"[red]✗[/red] Failed to star {agent_id}")
                    error_count += 1
                    
            except Exception as e:
                console.print(f"[red]✗[/red] Error starring {agent_id}: {e}")
                error_count += 1
        
        # Summary
        console.print(f"\n[bold]Summary:[/bold]")
        console.print(f"  [green]Starred: {success_count}[/green]")
        if skip_count > 0:
            console.print(f"  [yellow]Skipped: {skip_count}[/yellow]")
        if error_count > 0:
            console.print(f"  [red]Errors: {error_count}[/red]")
        
        logger.info(f"Bulk starred agents: {success_count} success, {skip_count} skipped, {error_count} errors", 
                   extra={"operation": "cli.bulk_star", "success": success_count, "skipped": skip_count, "errors": error_count})
        
        if error_count > 0:
            raise typer.Exit(1)
            
    except Exception as e:
        console.print(f"[red]Error in bulk starring: {e}[/red]")
        logger.error(f"Failed to bulk star agents: {e}", 
                    extra={"operation": "cli.bulk_star_error"})
        raise typer.Exit(1)


def clear_starred_agents_command(
    confirm: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt")
):
    """Clear all starred agent runs."""
    try:
        db = get_dashboard_db()
        starred_agents = db.get_starred_agents()
        
        if not starred_agents:
            console.print("[yellow]No starred agents to clear[/yellow]")
            return
        
        # Confirmation
        if not confirm:
            response = typer.confirm(f"Are you sure you want to unstar all {len(starred_agents)} agent runs?")
            if not response:
                console.print("Operation cancelled")
                return
        
        # Clear all starred agents
        success_count = 0
        error_count = 0
        
        for agent in starred_agents:
            try:
                if db.unstar_agent(agent['agent_id']):
                    success_count += 1
                else:
                    error_count += 1
            except Exception as e:
                console.print(f"[red]Error unstarring {agent['agent_id']}: {e}[/red]")
                error_count += 1
        
        console.print(f"[green]✓[/green] Cleared {success_count} starred agents")
        if error_count > 0:
            console.print(f"[red]✗[/red] {error_count} errors occurred")
        
        logger.info(f"Cleared starred agents: {success_count} success, {error_count} errors", 
                   extra={"operation": "cli.clear_starred", "success": success_count, "errors": error_count})
        
    except Exception as e:
        console.print(f"[red]Error clearing starred agents: {e}[/red]")
        logger.error(f"Failed to clear starred agents: {e}", 
                    extra={"operation": "cli.clear_starred_error"})
        raise typer.Exit(1)


# Create the starring app
starring_app = typer.Typer(
    name="star",
    help="Manage starred agent runs",
    rich_markup_mode="rich"
)

# Add commands
starring_app.command("add", help="Star an agent run")(star_agent_command)
starring_app.command("remove", help="Unstar an agent run")(unstar_agent_command)
starring_app.command("list", help="List starred agent runs")(list_starred_agents_command)
starring_app.command("check", help="Check if agent is starred")(check_agent_starred_command)
starring_app.command("toggle", help="Toggle star status")(toggle_agent_star_command)
starring_app.command("bulk", help="Star multiple agents")(bulk_star_agents_command)
starring_app.command("clear", help="Clear all starred agents")(clear_starred_agents_command)

# Aliases for convenience
star_command = star_agent_command
unstar_command = unstar_agent_command
starred_command = list_starred_agents_command

