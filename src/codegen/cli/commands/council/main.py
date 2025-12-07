"""CLI command for running multi-agent councils."""

import typer
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from codegen.agents.agent import Agent
from codegen.cli.auth.token_manager import get_current_token
from codegen.cli.rich.spinners import create_spinner
from codegen.cli.utils.org import resolve_org_id
from codegen.council.models import AgentConfig, CouncilConfig
from codegen.council.orchestrator import CouncilOrchestrator

console = Console()

council_app = typer.Typer(help="Run multi-agent councils for collaborative problem-solving")


@council_app.command("run")
def run_council(
    prompt: str = typer.Option(..., "--prompt", "-p", help="The prompt/question for the council"),
    models: str = typer.Option(
        "gpt-4o,claude-3-5-sonnet-20241022,gemini-2.0-flash-exp",
        "--models",
        "-m",
        help="Comma-separated list of models to use",
    ),
    candidates: int = typer.Option(3, "--candidates", "-c", help="Number of candidates per model"),
    disable_ranking: bool = typer.Option(False, "--no-ranking", help="Skip Stage 2 peer ranking"),
    synthesis_model: str = typer.Option(
        "claude-3-5-sonnet-20241022",
        "--synthesis-model",
        help="Model to use for final synthesis",
    ),
    org_id: int | None = typer.Option(None, help="Organization ID (defaults to saved org)"),
    poll_interval: float = typer.Option(5.0, "--poll", help="Seconds between status checks"),
):
    """Run a multi-agent council to collaboratively solve a problem.
    
    Example:
        codegen council run --prompt "How can I optimize my Python code?" --models gpt-4o,claude-3-5-sonnet
    """
    # Get token
    token = get_current_token()
    if not token:
        console.print("[red]Error:[/red] Not authenticated. Please run 'codegen login' first.")
        raise typer.Exit(1)
    
    # Resolve org ID
    resolved_org_id = resolve_org_id(org_id)
    if resolved_org_id is None:
        console.print(
            "[red]Error:[/red] Organization ID not provided. "
            "Pass --org-id, set CODEGEN_ORG_ID, or run 'codegen login'."
        )
        raise typer.Exit(1)
    
    # Parse models
    model_list = [m.strip() for m in models.split(",")]
    
    # Build config
    agent_configs = [AgentConfig(model=model) for model in model_list]
    
    config = CouncilConfig(
        agents=agent_configs,
        num_candidates=candidates,
        enable_ranking=not disable_ranking,
        synthesis_model=synthesis_model,
    )
    
    console.print(
        Panel(
            f"[cyan]Models:[/cyan] {', '.join(model_list)}\n"
            f"[cyan]Candidates per model:[/cyan] {candidates}\n"
            f"[cyan]Total agent runs:[/cyan] {len(model_list) * candidates}\n"
            f"[cyan]Ranking enabled:[/cyan] {'Yes' if not disable_ranking else 'No'}\n"
            f"[cyan]Synthesis model:[/cyan] {synthesis_model}",
            title="🏛️  [bold]Council Configuration[/bold]",
            border_style="blue",
            box=box.ROUNDED,
        )
    )
    
    # Run council
    orchestrator = CouncilOrchestrator(
        token=token,
        org_id=resolved_org_id,
        config=config,
    )
    
    spinner = create_spinner("Running council...")
    spinner.start()
    
    try:
        result = orchestrator.run(prompt, poll_interval=poll_interval)
    except Exception as e:
        spinner.stop()
        console.print(f"[red]Error running council:[/red] {e}")
        raise typer.Exit(1)
    finally:
        spinner.stop()
    
    # Display results
    console.print("\n")
    console.print(
        Panel(
            result.stage3_synthesis.content if result.stage3_synthesis else "No synthesis generated",
            title="✨ [bold]Final Synthesized Answer[/bold]",
            border_style="green",
            box=box.ROUNDED,
            padding=(1, 2),
        )
    )
    
    # Show candidate responses
    if result.stage1_candidates:
        console.print("\n[bold]Stage 1: Candidate Responses[/bold]")
        table = Table(box=box.ROUNDED)
        table.add_column("Model", style="cyan")
        table.add_column("Agent Run", style="magenta")
        table.add_column("Preview", style="dim")
        
        for cand in result.stage1_candidates:
            preview = cand.content[:100] + "..." if len(cand.content) > 100 else cand.content
            table.add_row(
                cand.model,
                f"#{cand.agent_run_id}",
                preview,
            )
        
        console.print(table)
    
    # Show aggregate rankings
    if result.aggregate_rankings:
        console.print("\n[bold]Stage 2: Aggregate Rankings[/bold]")
        rank_table = Table(box=box.ROUNDED)
        rank_table.add_column("Rank", style="yellow", justify="center")
        rank_table.add_column("Model", style="cyan")
        rank_table.add_column("Avg Score", style="green", justify="right")
        rank_table.add_column("Judgments", style="dim", justify="right")
        
        for idx, ranking in enumerate(result.aggregate_rankings, start=1):
            rank_table.add_row(
                f"#{idx}",
                ranking["model"],
                f"{ranking['average_rank']:.2f}",
                str(ranking["rankings_count"]),
            )
        
        console.print(rank_table)
    
    # Show synthesis info
    if result.stage3_synthesis:
        console.print("\n[dim]💡 Synthesis Details:[/dim]")
        console.print(f"  Method: {result.stage3_synthesis.method}")
        console.print(f"  Agent Run: #{result.stage3_synthesis.agent_run_id}")
        if result.stage3_synthesis.web_url:
            console.print(f"  View: {result.stage3_synthesis.web_url}")
    
    console.print("\n[green]✓[/green] Council completed successfully!")


# Make council_app the default export for CLI integration
council = council_app

