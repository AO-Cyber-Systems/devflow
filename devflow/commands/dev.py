"""Local development commands."""

import typer
from rich.console import Console

app = typer.Typer(no_args_is_help=True)
console = Console()


@app.command()
def setup(
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Set up local development environment."""
    import json
    import subprocess
    from pathlib import Path

    from devflow.core.config import load_project_config
    from devflow.core.git import configure_git_user
    from devflow.providers.docker import DockerProvider
    from devflow.providers.onepassword import OnePasswordProvider

    if not json_output:
        console.print("[bold]Setting up local development environment...[/bold]\n")

    steps = []
    errors = []

    # Step 1: Check Docker
    docker = DockerProvider()
    if not docker.is_authenticated():
        step = {"name": "docker", "status": "error", "message": "Docker daemon not running"}
        steps.append(step)
        errors.append("Docker daemon not running. Please start Docker first.")

        if json_output:
            print(json.dumps({"success": False, "steps": steps, "errors": errors}))
        else:
            console.print("[red]Error:[/red] Docker daemon not running.")
            console.print("Please start Docker Desktop or the Docker daemon first.")
        raise typer.Exit(1)

    steps.append({"name": "docker", "status": "ok", "message": "Docker is running"})
    if not json_output:
        console.print("[green]1. Docker[/green] - running")

    # Step 2: Load config
    config = load_project_config()
    if not config:
        step = {"name": "config", "status": "error", "message": "No devflow.yml found"}
        steps.append(step)
        errors.append("No devflow.yml found. Run 'devflow init' first.")

        if json_output:
            print(json.dumps({"success": False, "steps": steps, "errors": errors}))
        else:
            console.print("[red]Error:[/red] No devflow.yml found.")
            console.print("Run 'devflow init' first.")
        raise typer.Exit(1)

    steps.append({"name": "config", "status": "ok", "message": "Configuration loaded"})
    if not json_output:
        console.print("[green]2. Config[/green] - loaded")

    # Step 3: Configure git
    git_result = configure_git_user(config)
    if git_result["status"] == "ok":
        steps.append({"name": "git_config", "status": "ok", "message": git_result["message"]})
        if not json_output:
            console.print(f"[green]3. Git[/green] - {git_result['message']}")
    else:
        steps.append({"name": "git_config", "status": "skipped", "message": git_result["message"]})
        if not json_output:
            console.print(f"[dim]3. Git[/dim] - {git_result['message']}")

    # Step 4: Pull Docker images
    compose_file = config.development.compose_file
    compose_path = Path(compose_file)

    if compose_path.exists():
        if not json_output:
            console.print("[dim]4. Pulling images...[/dim]")

        try:
            result = subprocess.run(
                ["docker", "compose", "-f", str(compose_path), "pull"],
                capture_output=True,
                text=True,
                timeout=300,
            )
            if result.returncode == 0:
                steps.append({"name": "pull_images", "status": "ok", "message": "Images pulled"})
                if not json_output:
                    console.print("[green]4. Images[/green] - pulled")
            else:
                steps.append({"name": "pull_images", "status": "warning", "message": "Some images may not have pulled"})
                if not json_output:
                    console.print("[yellow]4. Images[/yellow] - some warnings (non-fatal)")
        except subprocess.TimeoutExpired:
            steps.append({"name": "pull_images", "status": "warning", "message": "Pull timed out"})
            if not json_output:
                console.print("[yellow]4. Images[/yellow] - timed out (continuing)")
        except Exception as e:
            steps.append({"name": "pull_images", "status": "warning", "message": str(e)})
            if not json_output:
                console.print(f"[yellow]4. Images[/yellow] - {e}")
    else:
        steps.append({"name": "pull_images", "status": "skipped", "message": f"No {compose_file} found"})
        if not json_output:
            console.print(f"[dim]4. Images[/dim] - skipped (no {compose_file})")

    # Step 5: Set up .env from template
    env_template = Path(".env.template")
    env_local = Path(".env.local")
    env_file = Path(".env")

    if env_template.exists():
        if not json_output:
            console.print("[dim]5. Setting up environment...[/dim]")

        template_content = env_template.read_text()

        # Check if template has 1Password references and provider is configured
        use_1password = (
            "op://" in template_content and config.secrets is not None and config.secrets.provider == "1password"
        )

        if use_1password:
            op = OnePasswordProvider()
            if op.is_authenticated():
                try:
                    resolved_content = op.inject(template_content)
                    env_local.write_text(resolved_content)
                    steps.append(
                        {"name": "env_setup", "status": "ok", "message": "Environment resolved from 1Password"}
                    )
                    if not json_output:
                        console.print("[green]5. Environment[/green] - resolved from 1Password")
                except Exception as e:
                    # Fall back to copying template as-is
                    env_local.write_text(template_content)
                    steps.append(
                        {"name": "env_setup", "status": "warning", "message": f"Could not resolve secrets: {e}"}
                    )
                    if not json_output:
                        console.print(f"[yellow]5. Environment[/yellow] - copied template (could not resolve: {e})")
            else:
                # Copy template as-is if not authenticated
                env_local.write_text(template_content)
                steps.append({"name": "env_setup", "status": "warning", "message": "1Password not authenticated"})
                if not json_output:
                    console.print("[yellow]5. Environment[/yellow] - copied template (1Password not authenticated)")
        else:
            # No secrets provider or no 1Password references, just copy
            env_local.write_text(template_content)
            steps.append({"name": "env_setup", "status": "ok", "message": "Environment file created"})
            if not json_output:
                console.print("[green]5. Environment[/green] - created .env.local")
    elif not env_file.exists() and not env_local.exists():
        steps.append({"name": "env_setup", "status": "skipped", "message": "No .env.template found"})
        if not json_output:
            console.print("[dim]5. Environment[/dim] - skipped (no template)")
    else:
        steps.append({"name": "env_setup", "status": "ok", "message": "Environment file exists"})
        if not json_output:
            console.print("[green]5. Environment[/green] - already exists")

    # Step 6: Start infrastructure if configured
    if config.infrastructure.enabled:
        if not json_output:
            console.print("[dim]6. Starting infrastructure...[/dim]")

        try:
            from devflow.providers.infrastructure import InfrastructureProvider

            infra = InfrastructureProvider(config.infrastructure)
            infra_result = infra.start()

            if infra_result.success:
                steps.append({"name": "infrastructure", "status": "ok", "message": "Infrastructure started"})
                if not json_output:
                    console.print("[green]6. Infrastructure[/green] - started (Traefik)")
            else:
                steps.append({"name": "infrastructure", "status": "warning", "message": infra_result.message})
                if not json_output:
                    console.print(f"[yellow]6. Infrastructure[/yellow] - {infra_result.message}")
        except Exception as e:
            steps.append({"name": "infrastructure", "status": "warning", "message": str(e)})
            if not json_output:
                console.print(f"[yellow]6. Infrastructure[/yellow] - {e}")
    else:
        steps.append({"name": "infrastructure", "status": "skipped", "message": "Not enabled in config"})
        if not json_output:
            console.print("[dim]6. Infrastructure[/dim] - skipped (not enabled)")

    # Summary
    success = all(s["status"] in ("ok", "skipped", "warning") for s in steps)

    if json_output:
        print(
            json.dumps(
                {
                    "success": success,
                    "steps": steps,
                    "errors": errors,
                }
            )
        )
    else:
        console.print()
        if success:
            console.print("[green]Setup complete![/green]")
            console.print("\nNext steps:")
            console.print("  1. Run 'devflow dev start' to start services")
            console.print("  2. Run 'devflow db migrate' to run migrations")
        else:
            console.print("[red]Setup completed with errors.[/red]")
            for error in errors:
                console.print(f"  - {error}")


@app.command()
def start(
    service: str | None = typer.Option(None, "--service", "-s", help="Specific service to start"),
    detach: bool = typer.Option(True, "--detach/--no-detach", "-d", help="Run in background"),
) -> None:
    """Start local development services."""
    import subprocess

    from devflow.core.config import load_project_config

    config = load_project_config()
    if not config:
        console.print("[red]No devflow.yml found. Run 'devflow init' first.[/red]")
        raise typer.Exit(1)

    compose_file = config.development.compose_file

    cmd = ["docker", "compose", "-f", compose_file, "up"]
    if detach:
        cmd.append("-d")
    if service:
        cmd.append(service)

    console.print("[bold]Starting services...[/bold]")
    subprocess.run(cmd)


@app.command()
def stop(
    service: str | None = typer.Option(None, "--service", "-s", help="Specific service to stop"),
) -> None:
    """Stop local development services."""
    import subprocess

    from devflow.core.config import load_project_config

    config = load_project_config()
    if not config:
        console.print("[red]No devflow.yml found. Run 'devflow init' first.[/red]")
        raise typer.Exit(1)

    compose_file = config.development.compose_file

    cmd = ["docker", "compose", "-f", compose_file, "stop"]
    if service:
        cmd.append(service)

    console.print("[bold]Stopping services...[/bold]")
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

    compose_file = config.development.compose_file

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

    compose_file = config.development.compose_file

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

    compose_file = config.development.compose_file

    cmd = ["docker", "compose", "-f", compose_file, "down"]
    if volumes:
        cmd.append("-v")

    console.print("[bold]Resetting environment...[/bold]")
    subprocess.run(cmd)
    console.print("[green]Done.[/green]")
