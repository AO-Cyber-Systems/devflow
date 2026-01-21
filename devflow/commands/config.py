"""Configuration management commands."""

from typing import Optional

import typer
from rich.console import Console
from rich.syntax import Syntax

app = typer.Typer(no_args_is_help=True)
console = Console()


@app.command()
def show(
    format: str = typer.Option("yaml", "--format", "-f", help="Output format (yaml, json)"),
) -> None:
    """Show current configuration."""
    from pathlib import Path

    import yaml

    from devflow.core.config import load_project_config

    config = load_project_config()
    if not config:
        console.print("[red]No devflow.yml found. Run 'devflow init' first.[/red]")
        raise typer.Exit(1)

    config_path = Path.cwd() / "devflow.yml"
    content = config_path.read_text()

    syntax = Syntax(content, "yaml", theme="monokai", line_numbers=True)
    console.print(syntax)


@app.command()
def validate() -> None:
    """Validate current configuration."""
    from pathlib import Path

    from devflow.core.config import load_project_config, validate_config

    config_path = Path.cwd() / "devflow.yml"
    if not config_path.exists():
        console.print("[red]No devflow.yml found. Run 'devflow init' first.[/red]")
        raise typer.Exit(1)

    errors = validate_config(config_path)

    if errors:
        console.print("[red]Configuration errors found:[/red]\n")
        for error in errors:
            console.print(f"  [red]{error}[/red]")
        raise typer.Exit(1)
    else:
        console.print("[green]Configuration is valid.[/green]")


@app.command()
def env(
    environment: Optional[str] = typer.Argument(None, help="Environment to switch to"),
) -> None:
    """Show or switch the current environment."""
    from devflow.core.config import get_current_env, set_current_env

    if environment:
        set_current_env(environment)
        console.print(f"Switched to [bold]{environment}[/bold] environment.")
    else:
        current = get_current_env()
        console.print(f"Current environment: [bold]{current}[/bold]")


@app.command("set")
def set_value(
    key: str = typer.Argument(..., help="Configuration key (e.g., 'database.migrations.directory')"),
    value: str = typer.Argument(..., help="Value to set"),
) -> None:
    """Set a configuration value."""
    console.print("[yellow]Configuration editing not yet implemented.[/yellow]")
    console.print(f"Would set {key} = {value}")
