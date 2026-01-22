"""Deployment commands."""

import json

import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(no_args_is_help=True)
console = Console()


def _get_env_config(config, env: str):
    """Get deployment environment configuration."""
    return config.deployment.environments.get(env)


def _build_image_tag(config, service_name: str, service_config) -> str:
    """Build the full image tag for a service."""
    registry = config.deployment.registry
    org = config.deployment.organization
    image = service_config.image
    return f"{registry}/{org}/{image}"


@app.command()
def status(
    env: str = typer.Option("staging", "--env", "-e", help="Environment (staging, production)"),
    service: str | None = typer.Option(None, "--service", "-s", help="Specific service to check"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Show deployment status for the specified environment."""
    from devflow.core.config import load_project_config
    from devflow.providers.docker import DockerProvider
    from devflow.providers.ssh import SSHProvider

    config = load_project_config()
    if not config:
        if json_output:
            print(json.dumps({"success": False, "error": "No devflow.yml found"}))
        else:
            console.print("[red]No devflow.yml found. Run 'devflow init' first.[/red]")
        raise typer.Exit(1)

    env_config = _get_env_config(config, env)
    if not env_config:
        if json_output:
            print(json.dumps({"success": False, "error": f"No environment config for: {env}"}))
        else:
            console.print(f"[red]No deployment environment configured for: {env}[/red]")
        raise typer.Exit(1)

    if not json_output:
        console.print(f"[bold]Deployment Status[/bold] ({env})\n")

    services_status = []

    # Check if remote or local
    if env_config.host:
        # Remote environment - use SSH
        ssh = SSHProvider()
        if not ssh.is_available():
            if json_output:
                print(json.dumps({"success": False, "error": "SSH not available"}))
            else:
                console.print("[red]SSH is not available.[/red]")
            raise typer.Exit(1)

        # Build command to list services
        cmd = 'docker service ls --format "{{json .}}"'
        if service:
            cmd = f'docker service ls --filter name={service} --format "{{{{json .}}}}"'

        result = ssh.execute(
            host=env_config.host,
            user=env_config.ssh_user,
            command=cmd,
        )

        if not result.success:
            if json_output:
                print(json.dumps({"success": False, "error": f"SSH command failed: {result.stderr}"}))
            else:
                console.print(f"[red]Failed to get status: {result.stderr}[/red]")
            raise typer.Exit(1)

        for line in result.stdout.strip().split("\n"):
            if line:
                try:
                    svc = json.loads(line)
                    services_status.append(
                        {
                            "name": svc.get("Name", ""),
                            "mode": svc.get("Mode", ""),
                            "replicas": svc.get("Replicas", ""),
                            "image": svc.get("Image", ""),
                        }
                    )
                except json.JSONDecodeError:
                    pass
    else:
        # Local environment - use Docker directly
        docker = DockerProvider()
        if not docker.is_authenticated():
            if json_output:
                print(json.dumps({"success": False, "error": "Docker not running"}))
            else:
                console.print("[red]Docker daemon not running.[/red]")
            raise typer.Exit(1)

        docker_services = docker.list_services(filter_name=service)
        for svc in docker_services:
            services_status.append(
                {
                    "name": svc.get("Name", ""),
                    "mode": svc.get("Mode", ""),
                    "replicas": svc.get("Replicas", ""),
                    "image": svc.get("Image", ""),
                }
            )

    if json_output:
        print(
            json.dumps(
                {
                    "success": True,
                    "environment": env,
                    "host": env_config.host,
                    "services": services_status,
                }
            )
        )
    else:
        if not services_status:
            console.print("[yellow]No services found.[/yellow]")
            return

        table = Table(show_header=True)
        table.add_column("Service")
        table.add_column("Mode")
        table.add_column("Replicas")
        table.add_column("Image")

        for svc in services_status:
            table.add_row(
                svc["name"],
                svc["mode"],
                svc["replicas"],
                svc["image"],
            )

        console.print(table)
        if env_config.host:
            console.print(f"\n[dim]Host: {env_config.host}[/dim]")


@app.command()
def staging(
    service: str | None = typer.Option(None, "--service", "-s", help="Specific service to deploy"),
    migrate: bool = typer.Option(False, "--migrate", "-m", help="Run migrations before deploying"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would be deployed"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Deploy to staging environment."""
    _deploy_to_env("staging", service, migrate, dry_run, json_output, require_confirm=False)


@app.command()
def production(
    service: str | None = typer.Option(None, "--service", "-s", help="Specific service to deploy"),
    migrate: bool = typer.Option(False, "--migrate", "-m", help="Run migrations before deploying"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would be deployed"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Deploy to production environment (requires confirmation)."""
    _deploy_to_env("production", service, migrate, dry_run, json_output, require_confirm=not yes)


def _deploy_to_env(
    env: str,
    service: str | None,
    migrate: bool,
    dry_run: bool,
    json_output: bool,
    require_confirm: bool,
) -> None:
    """Deploy to specified environment."""
    from devflow.core.config import load_project_config
    from devflow.providers.ssh import SSHProvider

    config = load_project_config()
    if not config:
        if json_output:
            print(json.dumps({"success": False, "error": "No devflow.yml found"}))
        else:
            console.print("[red]No devflow.yml found. Run 'devflow init' first.[/red]")
        raise typer.Exit(1)

    env_config = _get_env_config(config, env)
    if not env_config:
        if json_output:
            print(json.dumps({"success": False, "error": f"No environment config for: {env}"}))
        else:
            console.print(f"[red]No deployment environment configured for: {env}[/red]")
        raise typer.Exit(1)

    if require_confirm and not dry_run:
        confirm = typer.confirm(
            f"[yellow]You are about to deploy to {env.upper()}. Are you sure?[/yellow]",
            default=False,
        )
        if not confirm:
            if json_output:
                print(json.dumps({"success": False, "error": "Aborted by user"}))
            else:
                console.print("Aborted.")
            raise typer.Exit(0)

    # Check for require_approval config
    if env_config.require_approval and not dry_run:
        if not json_output:
            console.print("[yellow]This environment requires approval.[/yellow]")
            console.print("Use GitHub Actions or another CI/CD system for approved deployments.")
        if json_output:
            print(json.dumps({"success": False, "error": "Environment requires approval"}))
        raise typer.Exit(1)

    if not json_output:
        console.print(f"[bold]Deploying to {env}...[/bold]\n")
        if dry_run:
            console.print("[dim]Dry run - no changes will be made[/dim]\n")

    # Run migrations if requested
    if migrate and not dry_run:
        if not json_output:
            console.print("Running migrations first...")

        from devflow.migrations.engine import MigrationEngine

        engine = MigrationEngine(config, env)
        result = engine.apply_migrations(ci_mode=True)

        if not result["success"]:
            if json_output:
                print(json.dumps({"success": False, "error": f"Migration failed: {result['error']}"}))
            else:
                console.print(f"[red]Migration failed: {result['error']}[/red]")
            raise typer.Exit(1)

        if not json_output:
            console.print(f"[green]Applied {result['applied']} migration(s).[/green]\n")

    # Get services to deploy
    services_to_deploy = config.deployment.services
    if service:
        if service not in services_to_deploy:
            if json_output:
                print(json.dumps({"success": False, "error": f"Unknown service: {service}"}))
            else:
                console.print(f"[red]Unknown service: {service}[/red]")
            raise typer.Exit(1)
        services_to_deploy = {service: services_to_deploy[service]}

    if not services_to_deploy:
        if json_output:
            print(json.dumps({"success": True, "deployed": 0, "message": "No services configured"}))
        else:
            console.print("[yellow]No services configured in devflow.yml[/yellow]")
        return

    # Initialize SSH if remote
    ssh = None
    if env_config.host:
        ssh = SSHProvider()
        if not ssh.is_available():
            if json_output:
                print(json.dumps({"success": False, "error": "SSH not available"}))
            else:
                console.print("[red]SSH is not available.[/red]")
            raise typer.Exit(1)

    deployed = 0
    failed = 0
    results = []

    for svc_name, svc_config in services_to_deploy.items():
        result = {"service": svc_name, "status": "pending"}
        image_tag = _build_image_tag(config, svc_name, svc_config)

        if dry_run:
            result["status"] = "would_deploy"
            result["image"] = image_tag
            results.append(result)
            if not json_output:
                console.print(f"Would deploy [bold]{svc_name}[/bold] with image: {image_tag}")
            continue

        # Build update command
        service_full_name = f"{svc_config.stack}_{svc_name}"
        cmd = f"docker service update --image {image_tag} --with-registry-auth {service_full_name}"

        if not json_output:
            console.print(f"Deploying [bold]{svc_name}[/bold]...")

        if ssh:
            ssh_result = ssh.execute(
                host=env_config.host,
                user=env_config.ssh_user,
                command=cmd,
                timeout=120,
            )
            success = ssh_result.success
            error = ssh_result.stderr if not success else None
        else:
            # Local deployment
            from devflow.providers.docker import DockerProvider

            docker = DockerProvider()
            success = docker.service_update(service_full_name, image=image_tag)
            error = None if success else "Service update failed"

        if success:
            result["status"] = "deployed"
            result["image"] = image_tag
            deployed += 1
            if not json_output:
                console.print("  [green]Deployed successfully[/green]")
        else:
            result["status"] = "failed"
            result["error"] = error
            failed += 1
            if not json_output:
                console.print(f"  [red]Failed: {error}[/red]")

        results.append(result)

    if json_output:
        print(
            json.dumps(
                {
                    "success": failed == 0,
                    "environment": env,
                    "dry_run": dry_run,
                    "deployed": deployed,
                    "failed": failed,
                    "results": results,
                }
            )
        )
    elif not dry_run:
        console.print(f"\n[dim]Deployed: {deployed}, Failed: {failed}[/dim]")


@app.command()
def rollback(
    env: str = typer.Option("staging", "--env", "-e", help="Environment"),
    service: str | None = typer.Option(None, "--service", "-s", help="Specific service to rollback"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Rollback to the previous deployment."""
    from devflow.core.config import load_project_config
    from devflow.providers.docker import DockerProvider
    from devflow.providers.ssh import SSHProvider

    config = load_project_config()
    if not config:
        if json_output:
            print(json.dumps({"success": False, "error": "No devflow.yml found"}))
        else:
            console.print("[red]No devflow.yml found. Run 'devflow init' first.[/red]")
        raise typer.Exit(1)

    env_config = _get_env_config(config, env)
    if not env_config:
        if json_output:
            print(json.dumps({"success": False, "error": f"No environment config for: {env}"}))
        else:
            console.print(f"[red]No deployment environment configured for: {env}[/red]")
        raise typer.Exit(1)

    if not json_output:
        console.print(f"[bold]Rolling back {env}...[/bold]\n")

    # Get services to rollback
    services_to_rollback = config.deployment.services
    if service:
        if service not in services_to_rollback:
            if json_output:
                print(json.dumps({"success": False, "error": f"Unknown service: {service}"}))
            else:
                console.print(f"[red]Unknown service: {service}[/red]")
            raise typer.Exit(1)
        services_to_rollback = {service: services_to_rollback[service]}

    if not services_to_rollback:
        if json_output:
            print(json.dumps({"success": True, "rolled_back": 0, "message": "No services configured"}))
        else:
            console.print("[yellow]No services configured in devflow.yml[/yellow]")
        return

    ssh = None
    docker = None

    if env_config.host:
        ssh = SSHProvider()
        if not ssh.is_available():
            if json_output:
                print(json.dumps({"success": False, "error": "SSH not available"}))
            else:
                console.print("[red]SSH is not available.[/red]")
            raise typer.Exit(1)
    else:
        docker = DockerProvider()
        if not docker.is_authenticated():
            if json_output:
                print(json.dumps({"success": False, "error": "Docker not running"}))
            else:
                console.print("[red]Docker daemon not running.[/red]")
            raise typer.Exit(1)

    rolled_back = 0
    failed = 0
    results = []

    for svc_name, svc_config in services_to_rollback.items():
        result = {"service": svc_name, "status": "pending"}
        service_full_name = f"{svc_config.stack}_{svc_name}"

        if not json_output:
            console.print(f"Rolling back [bold]{svc_name}[/bold]...")

        if ssh:
            ssh_result = ssh.execute(
                host=env_config.host,
                user=env_config.ssh_user,
                command=f"docker service rollback {service_full_name}",
                timeout=60,
            )
            success = ssh_result.success
            error = ssh_result.stderr if not success else None
        else:
            success = docker.service_rollback(service_full_name)
            error = None if success else "Rollback failed"

        if success:
            result["status"] = "rolled_back"
            rolled_back += 1
            if not json_output:
                console.print("  [green]Rolled back successfully[/green]")
        else:
            result["status"] = "failed"
            result["error"] = error
            failed += 1
            if not json_output:
                console.print(f"  [red]Failed: {error}[/red]")

        results.append(result)

    if json_output:
        print(
            json.dumps(
                {
                    "success": failed == 0,
                    "environment": env,
                    "rolled_back": rolled_back,
                    "failed": failed,
                    "results": results,
                }
            )
        )
    else:
        console.print(f"\n[dim]Rolled back: {rolled_back}, Failed: {failed}[/dim]")


@app.command()
def logs(
    service: str = typer.Argument(..., help="Service name"),
    env: str = typer.Option("staging", "--env", "-e", help="Environment"),
    follow: bool = typer.Option(False, "--follow", "-f", help="Follow log output"),
    tail: int = typer.Option(100, "--tail", "-n", help="Number of lines to show"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """View service logs."""
    from devflow.core.config import load_project_config
    from devflow.providers.docker import DockerProvider
    from devflow.providers.ssh import SSHProvider

    config = load_project_config()
    if not config:
        if json_output:
            print(json.dumps({"success": False, "error": "No devflow.yml found"}))
        else:
            console.print("[red]No devflow.yml found. Run 'devflow init' first.[/red]")
        raise typer.Exit(1)

    env_config = _get_env_config(config, env)
    if not env_config:
        if json_output:
            print(json.dumps({"success": False, "error": f"No environment config for: {env}"}))
        else:
            console.print(f"[red]No deployment environment configured for: {env}[/red]")
        raise typer.Exit(1)

    # Get the full service name
    svc_config = config.deployment.services.get(service)
    if svc_config:
        service_full_name = f"{svc_config.stack}_{service}"
    else:
        # Use the name as-is if not in config
        service_full_name = service

    if not json_output:
        console.print(f"[bold]Logs for {service}[/bold] ({env})\n")

    if env_config.host:
        # Remote logs via SSH
        ssh = SSHProvider()
        if not ssh.is_available():
            if json_output:
                print(json.dumps({"success": False, "error": "SSH not available"}))
            else:
                console.print("[red]SSH is not available.[/red]")
            raise typer.Exit(1)

        follow_flag = "-f" if follow else ""
        cmd = f"docker service logs --tail {tail} {follow_flag} {service_full_name}"

        if follow:
            # For follow mode, use interactive connection
            import subprocess

            args = [
                "ssh",
                "-o",
                "StrictHostKeyChecking=accept-new",
                f"{env_config.ssh_user}@{env_config.host}",
                cmd,
            ]
            try:
                subprocess.run(args)
            except KeyboardInterrupt:
                pass
        else:
            result = ssh.execute(
                host=env_config.host,
                user=env_config.ssh_user,
                command=cmd,
                timeout=30,
            )

            if json_output:
                print(
                    json.dumps(
                        {
                            "success": result.success,
                            "logs": result.stdout,
                            "error": result.stderr if not result.success else None,
                        }
                    )
                )
            else:
                if result.success:
                    console.print(result.stdout)
                else:
                    console.print(f"[red]Failed to get logs: {result.stderr}[/red]")
                    raise typer.Exit(1)
    else:
        # Local logs
        docker = DockerProvider()
        if not docker.is_authenticated():
            if json_output:
                print(json.dumps({"success": False, "error": "Docker not running"}))
            else:
                console.print("[red]Docker daemon not running.[/red]")
            raise typer.Exit(1)

        process = docker.service_logs(service_full_name, tail=tail, follow=follow)

        if json_output and not follow:
            output = process.stdout.read() if process.stdout else ""
            process.wait()
            print(json.dumps({"success": True, "logs": output}))
        else:
            try:
                for line in process.stdout:
                    console.print(line, end="")
            except KeyboardInterrupt:
                pass
            finally:
                process.terminate()


@app.command()
def ssh(
    env: str = typer.Option("staging", "--env", "-e", help="Environment"),
    node: str = typer.Option("manager", help="Node to connect to (manager, worker1, etc.)"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """SSH to a cluster node."""
    from devflow.core.config import load_project_config
    from devflow.providers.onepassword import OnePasswordProvider
    from devflow.providers.ssh import SSHProvider

    config = load_project_config()
    if not config:
        if json_output:
            print(json.dumps({"success": False, "error": "No devflow.yml found"}))
        else:
            console.print("[red]No devflow.yml found. Run 'devflow init' first.[/red]")
        raise typer.Exit(1)

    env_config = _get_env_config(config, env)
    if not env_config:
        if json_output:
            print(json.dumps({"success": False, "error": f"No environment config for: {env}"}))
        else:
            console.print(f"[red]No deployment environment configured for: {env}[/red]")
        raise typer.Exit(1)

    if not env_config.host:
        if json_output:
            print(json.dumps({"success": False, "error": "No host configured for this environment"}))
        else:
            console.print(f"[red]No host configured for {env}. This is a local environment.[/red]")
        raise typer.Exit(1)

    ssh_provider = SSHProvider()
    if not ssh_provider.is_available():
        if json_output:
            print(json.dumps({"success": False, "error": "SSH not available"}))
        else:
            console.print("[red]SSH is not available.[/red]")
        raise typer.Exit(1)

    # Determine host (support for multiple nodes if configured)
    host = env_config.host
    user = env_config.ssh_user

    key_path = None
    cleanup_key = False

    # Check if we need to get SSH key from 1Password
    if env_config.ssh_key_secret:
        op = OnePasswordProvider()
        if not op.is_authenticated():
            if json_output:
                print(json.dumps({"success": False, "error": "1Password not authenticated"}))
            else:
                console.print("[red]1Password not authenticated. Run 'op signin' first.[/red]")
            raise typer.Exit(1)

        vault = config.secrets.vault
        key_content = op.read_field(env_config.ssh_key_secret, "private key", vault)
        if not key_content:
            # Try alternate field name
            key_content = op.read_field(env_config.ssh_key_secret, "password", vault)

        if not key_content:
            if json_output:
                print(json.dumps({"success": False, "error": "Could not read SSH key from 1Password"}))
            else:
                console.print("[red]Could not read SSH key from 1Password.[/red]")
            raise typer.Exit(1)

        # Write key to temp file
        key_path = ssh_provider.write_temp_key(key_content)
        cleanup_key = True

    if not json_output:
        console.print(f"[bold]Connecting to {env} ({node})...[/bold]\n")

    try:
        # Start interactive SSH session
        process = ssh_provider.connect(host, user, key_path)
        process.wait()
    finally:
        if cleanup_key and key_path:
            SSHProvider.cleanup_temp_key(key_path)

    if json_output:
        print(json.dumps({"success": True, "host": host, "user": user}))
