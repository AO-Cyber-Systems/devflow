"""Local development commands."""

from typing import Optional

import typer
from rich.console import Console

app = typer.Typer(no_args_is_help=True)
console = Console()


@app.command()
def setup() -> None:
    """Set up local development environment."""
    console.print("[bold]Setting up local development environment...[/bold]\n")

    from devflow.core.config import load_project_config

    config = load_project_config()
    if not config:
        console.print("[red]No devflow.yml found. Run 'devflow init' first.[/red]")
        raise typer.Exit(1)

    # Steps:
    # 1. Check Docker is running
    # 2. Pull required images
    # 3. Create necessary directories
    # 4. Set up environment files
    # 5. Start services

    console.print("[yellow]Setup not yet implemented.[/yellow]")


@app.command()
def start(
    service: Optional[str] = typer.Option(None, "--service", "-s", help="Specific service to start"),
    detach: bool = typer.Option(True, "--detach/--no-detach", "-d", help="Run in background"),
) -> None:
    """Start local development services."""
    import subprocess

    from devflow.core.config import load_project_config

    config = load_project_config()
    if not config:
        console.print("[red]No devflow.yml found. Run 'devflow init' first.[/red]")
        raise typer.Exit(1)

    compose_file = config.development.get("compose_file", "docker-compose.yml")

    cmd = ["docker", "compose", "-f", compose_file, "up"]
    if detach:
        cmd.append("-d")
    if service:
        cmd.append(service)

    console.print(f"[bold]Starting services...[/bold]")
    subprocess.run(cmd)


@app.command()
def stop(
    service: Optional[str] = typer.Option(None, "--service", "-s", help="Specific service to stop"),
) -> None:
    """Stop local development services."""
    import subprocess

    from devflow.core.config import load_project_config

    config = load_project_config()
    if not config:
        console.print("[red]No devflow.yml found. Run 'devflow init' first.[/red]")
        raise typer.Exit(1)

    compose_file = config.development.get("compose_file", "docker-compose.yml")

    cmd = ["docker", "compose", "-f", compose_file, "stop"]
    if service:
        cmd.append(service)

    console.print(f"[bold]Stopping services...[/bold]")
    subprocess.run(cmd)


@app.command()
def logs(
    service: str = typer.Argument(..., help="Service name"),
    follow: bool = typer.Option(False, "--follow", "-f", help="Follow log output"),
    tail: int = typer.Option(100, "--tail", "-n", help="Number of lines to show"),
) -> None:
    """View local service logs."""
    import subprocess

    from devflow.core.config import load_project_config

    config = load_project_config()
    if not config:
        console.print("[red]No devflow.yml found. Run 'devflow init' first.[/red]")
        raise typer.Exit(1)

    compose_file = config.development.get("compose_file", "docker-compose.yml")

    cmd = ["docker", "compose", "-f", compose_file, "logs", f"--tail={tail}"]
    if follow:
        cmd.append("-f")
    cmd.append(service)

    subprocess.run(cmd)


@app.command()
def shell(
    service: str = typer.Argument(..., help="Service name"),
    shell_cmd: str = typer.Option("/bin/sh", "--shell", help="Shell to use"),
) -> None:
    """Open a shell in a running container."""
    import subprocess

    from devflow.core.config import load_project_config

    config = load_project_config()
    if not config:
        console.print("[red]No devflow.yml found. Run 'devflow init' first.[/red]")
        raise typer.Exit(1)

    compose_file = config.development.get("compose_file", "docker-compose.yml")

    cmd = ["docker", "compose", "-f", compose_file, "exec", service, shell_cmd]
    subprocess.run(cmd)


@app.command()
def reset(
    volumes: bool = typer.Option(False, "--volumes", "-v", help="Also remove volumes (database data)"),
) -> None:
    """Reset local development environment."""
    import subprocess

    console.print("[bold yellow]This will remove all containers and optionally volumes.[/bold yellow]")

    if volumes:
        confirm = typer.confirm(
            "[red]This will DELETE all local database data. Are you sure?[/red]",
            default=False,
        )
        if not confirm:
            console.print("Aborted.")
            raise typer.Exit(0)

    from devflow.core.config import load_project_config

    config = load_project_config()
    if not config:
        console.print("[red]No devflow.yml found. Run 'devflow init' first.[/red]")
        raise typer.Exit(1)

    compose_file = config.development.get("compose_file", "docker-compose.yml")

    cmd = ["docker", "compose", "-f", compose_file, "down"]
    if volumes:
        cmd.append("-v")

    console.print("[bold]Resetting environment...[/bold]")
    subprocess.run(cmd)
    console.print("[green]Done.[/green]")
