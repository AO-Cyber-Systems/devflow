"""Database and migration commands."""

from typing import Optional

import typer
from rich.console import Console

app = typer.Typer(no_args_is_help=True)
console = Console()


@app.command()
def status(
    env: str = typer.Option("local", "--env", "-e", help="Environment (local, staging, production)"),
) -> None:
    """Show migration status for the specified environment."""
    console.print(f"[bold]Migration Status[/bold] ({env})\n")

    from devflow.core.config import load_project_config
    from devflow.migrations.tracker import MigrationTracker

    config = load_project_config()
    if not config:
        console.print("[red]No devflow.yml found. Run 'devflow init' first.[/red]")
        raise typer.Exit(1)

    tracker = MigrationTracker(config, env)
    status = tracker.get_status()

    console.print(f"  Applied:  {status['applied']}")
    console.print(f"  Pending:  {status['pending']}")
    console.print(f"  Total:    {status['total']}")

    if status["pending_files"]:
        console.print("\n[yellow]Pending migrations:[/yellow]")
        for f in status["pending_files"]:
            console.print(f"  - {f}")


@app.command()
def migrate(
    env: str = typer.Option("local", "--env", "-e", help="Environment (local, staging, production)"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would be applied without executing"),
    ci: bool = typer.Option(False, "--ci", help="Running in CI mode (non-interactive)"),
) -> None:
    """Apply pending migrations to the specified environment."""
    from devflow.core.config import load_project_config
    from devflow.migrations.engine import MigrationEngine

    config = load_project_config()
    if not config:
        console.print("[red]No devflow.yml found. Run 'devflow init' first.[/red]")
        raise typer.Exit(1)

    # Production requires confirmation
    if env == "production" and not ci and not dry_run:
        confirm = typer.confirm(
            "[yellow]You are about to run migrations on PRODUCTION. Are you sure?[/yellow]",
            default=False,
        )
        if not confirm:
            console.print("Aborted.")
            raise typer.Exit(0)

    engine = MigrationEngine(config, env)

    if dry_run:
        console.print(f"[bold]Dry Run - Migrations for {env}[/bold]\n")
        pending = engine.get_pending_migrations()
        if not pending:
            console.print("[green]No pending migrations.[/green]")
            return

        console.print(f"Would apply {len(pending)} migration(s):")
        for m in pending:
            console.print(f"  - {m}")
    else:
        console.print(f"[bold]Applying migrations to {env}...[/bold]\n")
        result = engine.apply_migrations()

        if result["success"]:
            console.print(f"[green]Applied {result['applied']} migration(s).[/green]")
        else:
            console.print(f"[red]Migration failed: {result['error']}[/red]")
            raise typer.Exit(1)


@app.command()
def create(
    name: str = typer.Argument(..., help="Name for the migration (e.g., 'add_user_preferences')"),
) -> None:
    """Create a new migration file."""
    from devflow.core.config import load_project_config
    from devflow.migrations.generator import create_migration

    config = load_project_config()
    if not config:
        console.print("[red]No devflow.yml found. Run 'devflow init' first.[/red]")
        raise typer.Exit(1)

    filepath = create_migration(config, name)
    console.print(f"[green]Created migration:[/green] {filepath}")


@app.command()
def rollback(
    env: str = typer.Option("local", "--env", "-e", help="Environment"),
    steps: int = typer.Option(1, "--steps", "-n", help="Number of migrations to rollback"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would be rolled back"),
) -> None:
    """Rollback the last migration(s)."""
    console.print("[yellow]Rollback is not yet implemented.[/yellow]")
    console.print("For now, create a new migration that reverses the changes.")


@app.command()
def connect(
    env: str = typer.Option("local", "--env", "-e", help="Environment to connect to"),
) -> None:
    """Open a psql session to the database."""
    import subprocess

    from devflow.core.config import load_project_config

    config = load_project_config()
    if not config:
        console.print("[red]No devflow.yml found. Run 'devflow init' first.[/red]")
        raise typer.Exit(1)

    db_url = config.get_database_url(env)
    if not db_url:
        console.print(f"[red]No database URL configured for {env}[/red]")
        raise typer.Exit(1)

    console.print(f"[bold]Connecting to {env} database...[/bold]")
    subprocess.run(["psql", db_url])
