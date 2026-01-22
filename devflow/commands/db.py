"""Database and migration commands."""

import json
import sys
from typing import Optional

import typer
from rich.console import Console

app = typer.Typer(no_args_is_help=True)
console = Console()


@app.command()
def status(
    env: str = typer.Option("local", "--env", "-e", help="Environment (local, staging, production)"),
    json_output: bool = typer.Option(False, "--json", help="Output results as JSON"),
) -> None:
    """Show migration status for the specified environment."""
    from devflow.core.config import load_project_config
    from devflow.migrations.engine import MigrationEngine

    config = load_project_config()
    if not config:
        if json_output:
            print(json.dumps({"success": False, "error": "No devflow.yml found"}))
        else:
            console.print("[red]No devflow.yml found. Run 'devflow init' first.[/red]")
        raise typer.Exit(1)

    engine = MigrationEngine(config, env)
    status_data = engine.get_status()

    if json_output:
        print(json.dumps({
            "success": True,
            "environment": env,
            "executor": status_data.get("executor", "sql"),
            "applied": status_data["applied"],
            "pending": status_data["pending"],
            "total": status_data["total"],
            "pending_files": status_data["pending_files"],
        }))
    else:
        console.print(f"[bold]Migration Status[/bold] ({env})\n")
        console.print(f"  Executor: {status_data.get('executor', 'sql')}")
        console.print(f"  Applied:  {status_data['applied']}")
        console.print(f"  Pending:  {status_data['pending']}")
        console.print(f"  Total:    {status_data['total']}")

        if status_data["pending_files"]:
            console.print("\n[yellow]Pending migrations:[/yellow]")
            for f in status_data["pending_files"]:
                console.print(f"  - {f}")


@app.command()
def migrate(
    env: str = typer.Option("local", "--env", "-e", help="Environment (local, staging, production)"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would be applied without executing"),
    ci: bool = typer.Option(False, "--ci", help="Running in CI mode (non-interactive)"),
    json_output: bool = typer.Option(False, "--json", help="Output results as JSON (for CI parsing)"),
) -> None:
    """Apply pending migrations to the specified environment."""
    from devflow.core.config import load_project_config
    from devflow.migrations.engine import MigrationEngine

    config = load_project_config()
    if not config:
        if json_output:
            print(json.dumps({"success": False, "error": "No devflow.yml found"}))
        else:
            console.print("[red]No devflow.yml found. Run 'devflow init' first.[/red]")
        raise typer.Exit(1)

    # Production requires confirmation (skip in CI mode)
    if env == "production" and not ci and not dry_run:
        confirm = typer.confirm(
            "[yellow]You are about to run migrations on PRODUCTION. Are you sure?[/yellow]",
            default=False,
        )
        if not confirm:
            if json_output:
                print(json.dumps({"success": False, "error": "Aborted by user"}))
            else:
                console.print("Aborted.")
            raise typer.Exit(0)

    engine = MigrationEngine(config, env)

    if dry_run:
        pending = engine.get_pending_migrations()

        if json_output:
            print(json.dumps({
                "success": True,
                "dry_run": True,
                "environment": env,
                "pending_count": len(pending),
                "pending_migrations": pending,
            }))
        else:
            console.print(f"[bold]Dry Run - Migrations for {env}[/bold]\n")
            if not pending:
                console.print("[green]No pending migrations.[/green]")
                return

            console.print(f"Would apply {len(pending)} migration(s):")
            for m in pending:
                console.print(f"  - {m}")
    else:
        if not json_output:
            console.print(f"[bold]Applying migrations to {env}...[/bold]\n")

        result = engine.apply_migrations(ci_mode=ci)

        if json_output:
            print(json.dumps({
                "success": result["success"],
                "environment": env,
                "applied": result["applied"],
                "skipped": result["skipped"],
                "error": result["error"],
            }))
        else:
            if result["success"]:
                console.print(f"[green]Applied {result['applied']} migration(s).[/green]")
            else:
                console.print(f"[red]Migration failed: {result['error']}[/red]")

        if not result["success"]:
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
    force: bool = typer.Option(False, "--force", help="Force rollback on production"),
    json_output: bool = typer.Option(False, "--json", help="Output results as JSON"),
) -> None:
    """Rollback the last migration(s)."""
    from pathlib import Path

    from devflow.core.config import load_project_config
    from devflow.migrations.executors.sql import SQLExecutor

    config = load_project_config()
    if not config:
        if json_output:
            print(json.dumps({"success": False, "error": "No devflow.yml found"}))
        else:
            console.print("[red]No devflow.yml found. Run 'devflow init' first.[/red]")
        raise typer.Exit(1)

    # Production requires --force
    if env == "production" and not force and not dry_run:
        if json_output:
            print(json.dumps({"success": False, "error": "Production rollback requires --force flag"}))
        else:
            console.print("[red]Production rollback requires --force flag.[/red]")
            console.print("Use: devflow db rollback --env production --force")
        raise typer.Exit(1)

    executor = SQLExecutor(config, env)
    db_url = executor.get_db_url()

    if not db_url:
        if json_output:
            print(json.dumps({"success": False, "error": f"No database URL configured for {env}"}))
        else:
            console.print(f"[red]No database URL configured for {env}[/red]")
        raise typer.Exit(1)

    # Get applied migrations
    applied = executor.get_applied_with_connection(db_url)
    if not applied:
        if json_output:
            print(json.dumps({"success": True, "rolled_back": 0, "message": "No applied migrations to rollback"}))
        else:
            console.print("[yellow]No applied migrations to rollback.[/yellow]")
        return

    # Get the last N migrations
    migrations_to_rollback = applied[-steps:][::-1]  # Reverse to rollback in correct order

    if not json_output:
        console.print(f"[bold]Rollback {len(migrations_to_rollback)} migration(s)[/bold] ({env})\n")
        if dry_run:
            console.print("[dim]Dry run - no changes will be made[/dim]\n")

    migrations_dir = Path(config.database.migrations.directory)
    results = []
    rolled_back = 0
    failed = 0

    for migration_name in migrations_to_rollback:
        result = {"migration": migration_name, "status": "pending"}

        # Look for down migration file
        down_file = migrations_dir / migration_name.replace(".sql", ".down.sql")

        if not down_file.exists():
            result["status"] = "error"
            result["error"] = f"No .down.sql file found"

            if not json_output:
                console.print(f"[red]Error:[/red] No rollback file for {migration_name}")
                console.print(f"  Expected: {down_file}")

            failed += 1
            results.append(result)
            break  # Stop on first error to prevent inconsistent state

        if dry_run:
            result["status"] = "would_rollback"
            result["down_file"] = str(down_file)
            results.append(result)

            if not json_output:
                console.print(f"Would rollback: [bold]{migration_name}[/bold]")
                console.print(f"  Using: {down_file.name}")

            continue

        # Execute rollback
        rollback_result = executor.rollback_migration(migration_name, down_file.read_text())

        if rollback_result.success:
            result["status"] = "rolled_back"
            rolled_back += 1
            if not json_output:
                console.print(f"[green]Rolled back:[/green] {migration_name}")
        else:
            result["status"] = "error"
            result["error"] = rollback_result.error
            failed += 1
            if not json_output:
                console.print(f"[red]Failed:[/red] {migration_name}")
                console.print(f"  Error: {rollback_result.error}")
            break  # Stop on first error

        results.append(result)

    if json_output:
        print(json.dumps({
            "success": failed == 0,
            "environment": env,
            "dry_run": dry_run,
            "rolled_back": rolled_back,
            "failed": failed,
            "results": results,
        }))
    elif not dry_run:
        console.print(f"\n[dim]Rolled back: {rolled_back}, Failed: {failed}[/dim]")


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
