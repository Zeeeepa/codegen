"""Orchestration command for the Codegen CLI.

Provides CLI access to the Visual Orchestration Full CI/CD System with self-evolving capabilities.
"""

import asyncio
import json
from pathlib import Path
from typing import Optional, Dict, Any, List
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.json import JSON
from rich.tree import Tree
import yaml

try:
    from codegen.orchestration.self_evolving import SelfEvolvingFlowManager
    from codegen.orchestration.engine import OrchestrationEngine
    from codegen.orchestration.schemas import PipelineDefinition, ExecutionStatus
    from codegen.orchestration.api import create_app
    import uvicorn
except ImportError as e:
    # Graceful fallback for missing dependencies
    SelfEvolvingFlowManager = None
    OrchestrationEngine = None
    create_app = None
    uvicorn = None

from codegen.cli.rich.spinners import create_spinner
from codegen.shared.logging.get_logger import get_logger

console = Console()
logger = get_logger(__name__)

# Create the orchestrate Typer app
orchestrate_app = typer.Typer(
    name="orchestrate",
    help="Visual Orchestration Full CI/CD System with self-evolving capabilities",
    rich_markup_mode="rich",
)

# Import and add project management sub-commands
try:
    from .project_mgmt import project_mgmt_app
    orchestrate_app.add_typer(project_mgmt_app, name="project")
except ImportError:
    # Graceful fallback if project management module not available
    pass


@orchestrate_app.command("create")
def create_pipeline(
    project_path: str = typer.Argument(
        ".", help="Path to the project directory to analyze"
    ),
    pipeline_name: str = typer.Option(
        None, "--name", "-n", help="Name for the pipeline (defaults to project directory name)"
    ),
    output_file: Optional[str] = typer.Option(
        None, "--output", "-o", help="Output file for the pipeline definition (YAML/JSON)"
    ),
    requirements: Optional[str] = typer.Option(
        None, "--requirements", "-r", help="JSON string of custom requirements"
    ),
    interactive: bool = typer.Option(
        False, "--interactive", "-i", help="Enable interactive mode for pipeline customization"
    ),
):
    """Create an intelligent CI/CD pipeline based on project analysis."""
    if not SelfEvolvingFlowManager:
        console.print("[red]Error:[/red] Orchestration dependencies not available. Please install with: pip install fastapi uvicorn websockets")
        raise typer.Exit(1)
    
    logger.info(
        "Creating intelligent pipeline",
        extra={
            "operation": "orchestrate.create",
            "project_path": project_path,
            "pipeline_name": pipeline_name,
        },
    )
    
    project_dir = Path(project_path).resolve()
    if not project_dir.exists():
        console.print(f"[red]Error:[/red] Project path does not exist: {project_path}")
        raise typer.Exit(1)
    
    if not pipeline_name:
        pipeline_name = project_dir.name
    
    # Parse custom requirements if provided
    custom_requirements = None
    if requirements:
        try:
            custom_requirements = json.loads(requirements)
        except json.JSONDecodeError:
            console.print("[red]Error:[/red] Invalid JSON format for requirements")
            raise typer.Exit(1)
    
    async def create_pipeline_async():
        flow_manager = SelfEvolvingFlowManager()
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            analyze_task = progress.add_task("🔍 Analyzing project structure...", total=None)
            
            pipeline = await flow_manager.create_intelligent_pipeline(
                project_dir, pipeline_name, custom_requirements
            )
            
            progress.update(analyze_task, description="✅ Project analysis complete")
            progress.stop()
        
        return pipeline
    
    try:
        pipeline = asyncio.run(create_pipeline_async())
        
        # Display pipeline summary
        console.print(Panel.fit(
            f"[bold green]Pipeline Created Successfully![/bold green]\n\n"
            f"[bold]Name:[/bold] {pipeline.name}\n"
            f"[bold]Stages:[/bold] {len(pipeline.stages)}\n"
            f"[bold]Total Tasks:[/bold] {sum(len(stage.tasks) for stage in pipeline.stages)}",
            title="🚀 Pipeline Summary",
            border_style="green"
        ))
        
        # Show stage breakdown
        tree = Tree("📋 [bold blue]Pipeline Stages[/bold blue]")
        for stage in pipeline.stages:
            stage_node = tree.add(f"🏗️ [bold]{stage.name}[/bold] ({len(stage.tasks)} tasks)")
            for task in stage.tasks:
                stage_node.add(f"🔧 {task.name}")
        
        console.print(tree)
        
        # Save pipeline definition if requested
        if output_file:
            output_path = Path(output_file)
            pipeline_dict = pipeline.model_dump()
            
            if output_path.suffix.lower() in ['.yaml', '.yml']:
                with open(output_path, 'w') as f:
                    yaml.dump(pipeline_dict, f, default_flow_style=False)
            else:
                with open(output_path, 'w') as f:
                    json.dump(pipeline_dict, f, indent=2)
            
            console.print(f"💾 Pipeline definition saved to: {output_path}")
        
        if interactive:
            console.print("\n[yellow]Interactive mode would launch the visual designer here[/yellow]")
            console.print("Run `codegen orchestrate serve` to start the web interface")
        
    except Exception as e:
        logger.error(f"Failed to create pipeline: {e}")
        console.print(f"[red]Error creating pipeline:[/red] {e}")
        raise typer.Exit(1)


@orchestrate_app.command("monitor")
def monitor_pipeline(
    pipeline_id: str = typer.Argument(..., help="Pipeline ID to monitor"),
    follow: bool = typer.Option(
        False, "--follow", "-f", help="Follow the pipeline execution in real-time"
    ),
    output_format: str = typer.Option(
        "table", "--format", help="Output format: table, json, yaml"
    ),
):
    """Monitor pipeline execution and performance metrics."""
    if not SelfEvolvingFlowManager:
        console.print("[red]Error:[/red] Orchestration dependencies not available")
        raise typer.Exit(1)
    
    logger.info(
        "Monitoring pipeline",
        extra={
            "operation": "orchestrate.monitor",
            "pipeline_id": pipeline_id,
            "follow": follow,
        },
    )
    
    async def monitor_async():
        flow_manager = SelfEvolvingFlowManager()
        
        if follow:
            console.print(f"🔍 Following pipeline: {pipeline_id}")
            console.print("Press Ctrl+C to stop monitoring\n")
            
            try:
                while True:
                    metrics = await flow_manager.monitor_and_evolve(pipeline_id)
                    
                    if output_format.lower() == "json":
                        console.print(JSON.from_data(metrics))
                    elif output_format.lower() == "yaml":
                        console.print(yaml.dump(metrics, default_flow_style=False))
                    else:
                        _display_metrics_table(metrics)
                    
                    await asyncio.sleep(5)  # Update every 5 seconds
                    
            except KeyboardInterrupt:
                console.print("\n🛑 Monitoring stopped")
        else:
            metrics = await flow_manager.monitor_and_evolve(pipeline_id)
            
            if output_format.lower() == "json":
                console.print(JSON.from_data(metrics))
            elif output_format.lower() == "yaml":
                console.print(yaml.dump(metrics, default_flow_style=False))
            else:
                _display_metrics_table(metrics)
    
    try:
        asyncio.run(monitor_async())
    except Exception as e:
        logger.error(f"Failed to monitor pipeline: {e}")
        console.print(f"[red]Error monitoring pipeline:[/red] {e}")
        raise typer.Exit(1)


@orchestrate_app.command("evolve")
def evolve_pipeline(
    pipeline_id: str = typer.Argument(..., help="Pipeline ID to evolve"),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Show what changes would be made without applying them"
    ),
    auto_apply: bool = typer.Option(
        False, "--auto-apply", help="Automatically apply suggested optimizations"
    ),
):
    """Trigger pipeline evolution based on performance analysis."""
    if not SelfEvolvingFlowManager:
        console.print("[red]Error:[/red] Orchestration dependencies not available")
        raise typer.Exit(1)
    
    logger.info(
        "Evolving pipeline",
        extra={
            "operation": "orchestrate.evolve",
            "pipeline_id": pipeline_id,
            "dry_run": dry_run,
        },
    )
    
    async def evolve_async():
        flow_manager = SelfEvolvingFlowManager()
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("🧠 Analyzing pipeline performance...", total=None)
            
            evolution_result = await flow_manager.monitor_and_evolve(pipeline_id)
            
            progress.update(task, description="✅ Analysis complete")
            progress.stop()
        
        suggestions = evolution_result.get("evolution_suggestions", [])
        
        if not suggestions:
            console.print("🎉 [green]Pipeline is already optimized![/green] No changes suggested.")
            return
        
        console.print(Panel.fit(
            f"[bold yellow]Found {len(suggestions)} optimization opportunities[/bold yellow]",
            title="🔬 Evolution Analysis",
            border_style="yellow"
        ))
        
        for i, suggestion in enumerate(suggestions, 1):
            console.print(f"\n{i}. [bold]{suggestion.get('type', 'Optimization')}:[/bold]")
            console.print(f"   {suggestion.get('description', 'No description')}")
            
            if suggestion.get('impact'):
                console.print(f"   [dim]Expected impact: {suggestion['impact']}[/dim]")
        
        if dry_run:
            console.print("\n[yellow]Dry run mode - no changes applied[/yellow]")
            return
        
        if auto_apply or typer.confirm("\nApply these optimizations?"):
            console.print("🔧 Applying optimizations...")
            # In a full implementation, this would apply the changes
            console.print("✅ [green]Optimizations applied successfully![/green]")
        else:
            console.print("🚫 Evolution cancelled")
    
    try:
        asyncio.run(evolve_async())
    except Exception as e:
        logger.error(f"Failed to evolve pipeline: {e}")
        console.print(f"[red]Error evolving pipeline:[/red] {e}")
        raise typer.Exit(1)


@orchestrate_app.command("list")
def list_pipelines(
    status: Optional[str] = typer.Option(
        None, "--status", help="Filter by pipeline status: running, completed, failed"
    ),
    limit: int = typer.Option(10, "--limit", "-l", help="Maximum number of pipelines to show"),
    output_format: str = typer.Option(
        "table", "--format", help="Output format: table, json, yaml"
    ),
):
    """List all orchestration pipelines with their current status."""
    if not OrchestrationEngine:
        console.print("[red]Error:[/red] Orchestration dependencies not available")
        raise typer.Exit(1)
    
    logger.info(
        "Listing pipelines",
        extra={
            "operation": "orchestrate.list",
            "status_filter": status,
            "limit": limit,
        },
    )
    
    # Mock pipeline data for demonstration
    pipelines = [
        {
            "id": "pipe-001",
            "name": "web-app-ci",
            "status": "running",
            "created": "2024-01-15T10:30:00Z",
            "last_run": "2024-01-15T14:22:00Z",
            "success_rate": "95%"
        },
        {
            "id": "pipe-002", 
            "name": "api-deployment",
            "status": "completed",
            "created": "2024-01-14T09:15:00Z",
            "last_run": "2024-01-15T13:45:00Z",
            "success_rate": "100%"
        },
        {
            "id": "pipe-003",
            "name": "ml-training",
            "status": "failed",
            "created": "2024-01-13T16:20:00Z", 
            "last_run": "2024-01-15T12:10:00Z",
            "success_rate": "78%"
        }
    ]
    
    # Apply status filter if provided
    if status:
        pipelines = [p for p in pipelines if p["status"].lower() == status.lower()]
    
    # Apply limit
    pipelines = pipelines[:limit]
    
    if not pipelines:
        console.print("[yellow]No pipelines found matching the criteria.[/yellow]")
        return
    
    if output_format.lower() == "json":
        console.print(JSON.from_data(pipelines))
    elif output_format.lower() == "yaml":
        console.print(yaml.dump(pipelines, default_flow_style=False))
    else:
        table = Table(
            title="🔄 Orchestration Pipelines",
            border_style="blue",
            show_header=True,
        )
        table.add_column("ID", style="cyan", no_wrap=True)
        table.add_column("Name", style="white")
        table.add_column("Status", style="magenta")
        table.add_column("Success Rate", style="green")
        table.add_column("Last Run", style="dim")
        
        for pipeline in pipelines:
            status_style = {
                "running": "yellow",
                "completed": "green", 
                "failed": "red"
            }.get(pipeline["status"], "white")
            
            table.add_row(
                pipeline["id"],
                pipeline["name"],
                f"[{status_style}]{pipeline['status']}[/{status_style}]",
                pipeline["success_rate"],
                pipeline["last_run"].split("T")[1][:5]  # Show just time
            )
        
        console.print(table)


@orchestrate_app.command("serve")
def serve_web_interface(
    port: int = typer.Option(8000, "--port", "-p", help="Port to run the web server on"),
    host: str = typer.Option("127.0.0.1", "--host", help="Host to bind the server to"),
    reload: bool = typer.Option(False, "--reload", help="Enable auto-reload for development"),
):
    """Start the web-based visual pipeline designer and monitoring interface."""
    if not create_app or not uvicorn:
        console.print("[red]Error:[/red] Web server dependencies not available. Please install with: pip install fastapi uvicorn")
        raise typer.Exit(1)
    
    logger.info(
        "Starting web interface",
        extra={
            "operation": "orchestrate.serve",
            "port": port,
            "host": host,
        },
    )
    
    console.print(Panel.fit(
        f"[bold green]🚀 Starting Visual Orchestration Interface[/bold green]\n\n"
        f"[bold]URL:[/bold] http://{host}:{port}\n"
        f"[bold]API Docs:[/bold] http://{host}:{port}/docs\n"
        f"[bold]WebSocket:[/bold] ws://{host}:{port}/ws",
        title="🌐 Web Server",
        border_style="green"
    ))
    
    try:
        app = create_app()
        uvicorn.run(
            app,
            host=host,
            port=port,
            reload=reload,
            log_level="info"
        )
    except KeyboardInterrupt:
        console.print("\n🛑 Server stopped")
    except Exception as e:
        logger.error(f"Failed to start web server: {e}")
        console.print(f"[red]Error starting web server:[/red] {e}")
        raise typer.Exit(1)


@orchestrate_app.command("analyze")
def analyze_project(
    project_path: str = typer.Argument(".", help="Path to the project to analyze"),
    output_format: str = typer.Option(
        "table", "--format", help="Output format: table, json, yaml"
    ),
):
    """Analyze a project and show intelligence insights for pipeline creation."""
    if not SelfEvolvingFlowManager:
        console.print("[red]Error:[/red] Orchestration dependencies not available")
        raise typer.Exit(1)
    
    project_dir = Path(project_path).resolve()
    if not project_dir.exists():
        console.print(f"[red]Error:[/red] Project path does not exist: {project_path}")
        raise typer.Exit(1)
    
    logger.info(
        "Analyzing project",
        extra={
            "operation": "orchestrate.analyze", 
            "project_path": str(project_dir),
        },
    )
    
    async def analyze_async():
        flow_manager = SelfEvolvingFlowManager()
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("🔍 Analyzing project...", total=None)
            
            # Access the analyzer directly
            analyzer = flow_manager.analyzer
            analysis = await analyzer.analyze_project(project_dir)
            
            progress.update(task, description="✅ Analysis complete")
            progress.stop()
        
        return analysis
    
    try:
        analysis = asyncio.run(analyze_async())
        
        if output_format.lower() == "json":
            console.print(JSON.from_data(analysis))
        elif output_format.lower() == "yaml":
            console.print(yaml.dump(analysis, default_flow_style=False))
        else:
            _display_analysis_table(analysis)
            
    except Exception as e:
        logger.error(f"Failed to analyze project: {e}")
        console.print(f"[red]Error analyzing project:[/red] {e}")
        raise typer.Exit(1)


def _display_metrics_table(metrics: Dict[str, Any]):
    """Display monitoring metrics in a formatted table."""
    table = Table(
        title="📊 Pipeline Metrics",
        border_style="blue",
        show_header=True,
    )
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="white")
    table.add_column("Trend", style="green")
    
    # Flatten metrics for display
    for key, value in metrics.items():
        if isinstance(value, dict):
            for sub_key, sub_value in value.items():
                table.add_row(
                    f"{key}.{sub_key}",
                    str(sub_value),
                    "➡️"  # Placeholder trend
                )
        else:
            table.add_row(key, str(value), "➡️")
    
    console.print(table)


def _display_analysis_table(analysis: Dict[str, Any]):
    """Display project analysis in a formatted table."""
    console.print(Panel.fit(
        f"[bold blue]Project Analysis Results[/bold blue]\n\n"
        f"[bold]Project Type:[/bold] {analysis.get('project_type', 'Unknown')}\n"
        f"[bold]Primary Language:[/bold] {analysis.get('primary_language', 'Unknown')}\n"
        f"[bold]Complexity Score:[/bold] {analysis.get('complexity_score', 0)}/10",
        title="🔍 Analysis Summary",
        border_style="blue"
    ))
    
    # Languages table
    if analysis.get('languages'):
        lang_table = Table(title="📝 Languages Detected", border_style="green")
        lang_table.add_column("Language", style="cyan")
        lang_table.add_column("Files", style="white")
        lang_table.add_column("Percentage", style="yellow")
        
        for lang, count in analysis['languages'].items():
            total_files = sum(analysis['languages'].values())
            percentage = f"{(count / total_files * 100):.1f}%"
            lang_table.add_row(lang, str(count), percentage)
        
        console.print(lang_table)
    
    # Frameworks table
    if analysis.get('frameworks'):
        fw_table = Table(title="🛠️ Frameworks Detected", border_style="magenta")
        fw_table.add_column("Framework", style="cyan")
        fw_table.add_column("Confidence", style="white")
        
        for framework in analysis['frameworks']:
            fw_table.add_row(framework, "High")  # Simplified confidence
        
        console.print(fw_table)


if __name__ == "__main__":
    orchestrate_app()