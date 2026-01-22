"""Infrastructure management commands for shared local development."""

import json
from datetime import datetime
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(no_args_is_help=True, help="Manage shared development infrastructure")
console = Console()


def _get_provider():
    """Get the infrastructure provider with config from devflow.yml or defaults."""
    from devflow.core.config import InfrastructureConfig, load_project_config
    from devflow.providers.infrastructure import InfrastructureProvider

    config = load_project_config()
    if config and config.infrastructure:
        return InfrastructureProvider(config.infrastructure)
    return InfrastructureProvider(InfrastructureConfig())


@app.command()
def up(
    detach: bool = typer.Option(True, "--detach/--no-detach", "-d", help="Run in background"),
    force_recreate: bool = typer.Option(False, "--force-recreate", help="Force recreation of containers"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Start shared infrastructure (Traefik, networks).

    This starts the shared Traefik reverse proxy and creates the devflow-proxy
    network. Projects configured with 'devflow infra configure' will route
    through this shared infrastructure.
    """
    provider = _get_provider()

    if not json_output:
        console.print("[bold]Starting shared infrastructure...[/bold]\n")

    result = provider.start(force_recreate=force_recreate)

    if json_output:
        print(json.dumps({"success": result.success, "message": result.message, "details": result.details}))
        return

    if result.success:
        console.print(f"[green]✓[/green] {result.message}")
        if result.details:
            console.print(f"\n  Network: [cyan]{result.details.get('network', 'devflow-proxy')}[/cyan]")
            console.print(f"  Traefik Dashboard: [cyan]{result.details.get('dashboard_url', '')}[/cyan]")
            console.print(f"  HTTPS: [cyan]{result.details.get('traefik_url', '')}[/cyan]")
    else:
        console.print(f"[red]✗[/red] {result.message}")
        raise typer.Exit(1)


@app.command()
def down(
    remove_volumes: bool = typer.Option(False, "--volumes", "-v", help="Remove volumes when stopping"),
    remove_network: bool = typer.Option(False, "--network", help="Remove the network after stopping"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Stop shared infrastructure.

    Stops the Traefik container. Optionally removes the network (which requires
    all connected containers to be stopped first).
    """
    provider = _get_provider()

    if not json_output:
        console.print("[bold]Stopping shared infrastructure...[/bold]\n")

    result = provider.stop(remove_volumes=remove_volumes, remove_network=remove_network)

    if json_output:
        print(json.dumps({"success": result.success, "message": result.message}))
        return

    if result.success:
        console.print(f"[green]✓[/green] {result.message}")
    else:
        console.print(f"[red]✗[/red] {result.message}")
        raise typer.Exit(1)


@app.command()
def status(
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Show infrastructure status.

    Displays the status of the shared network, Traefik container, certificates,
    and registered projects.
    """
    provider = _get_provider()
    infra_status = provider.status()

    if json_output:
        print(json.dumps(infra_status.to_dict(), indent=2))
        return

    console.print("[bold]Infrastructure Status[/bold]\n")

    # Network status
    network_status = "[green]✓[/green]" if infra_status.network_exists else "[red]✗[/red]"
    console.print(f"Network ({infra_status.network_name}): {network_status}")

    # Traefik status
    traefik_status = "[green]running[/green]" if infra_status.traefik_running else "[red]stopped[/red]"
    console.print(f"Traefik: {traefik_status}")
    if infra_status.traefik_running and infra_status.traefik_url:
        console.print(
            f"  Dashboard: [cyan]{infra_status.traefik_url.replace('https:', 'http:').replace(':443', ':8080')}[/cyan]"
        )

    # Certificates status
    certs_status = "[green]valid[/green]" if infra_status.certificates_valid else "[yellow]not found[/yellow]"
    console.print(f"Certificates: {certs_status}")
    if infra_status.certificates_path:
        console.print(f"  Path: [dim]{infra_status.certificates_path}[/dim]")

    # Registered projects
    if infra_status.registered_projects:
        console.print(f"\n[bold]Registered Projects ({len(infra_status.registered_projects)})[/bold]")
        table = Table(show_header=True)
        table.add_column("Name")
        table.add_column("Path")
        table.add_column("Configured")

        for project in infra_status.registered_projects:
            table.add_row(
                project.get("name", ""),
                project.get("path", ""),
                project.get("configured_at", "")[:10] if project.get("configured_at") else "",
            )
        console.print(table)
    else:
        console.print("\n[dim]No projects registered. Use 'devflow infra configure <path>' to add one.[/dim]")


@app.command()
def configure(
    project_path: Path = typer.Argument(..., help="Path to the project to configure"),
    compose_file: str = typer.Option("docker-compose.yml", "--compose", "-c", help="Compose file to transform"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would be changed without modifying files"),
    no_backup: bool = typer.Option(False, "--no-backup", help="Don't create backup files"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Configure a project to use shared infrastructure.

    Transforms the project's docker-compose.yml to:
    - Use the devflow-proxy network instead of project-specific networks
    - Remove embedded Traefik services (use shared instance instead)
    - Update service network references

    A backup is created before modifying files (unless --no-backup is used).
    """
    from devflow.infrastructure.compose_transformer import ComposeTransformer
    from devflow.providers.infrastructure import RegisteredProject

    provider = _get_provider()
    transformer = ComposeTransformer(provider.config)

    project_path = Path(project_path).resolve()
    compose_path = project_path / compose_file

    if not project_path.exists():
        msg = f"Project path does not exist: {project_path}"
        if json_output:
            print(json.dumps({"success": False, "message": msg}))
        else:
            console.print(f"[red]✗[/red] {msg}")
        raise typer.Exit(1)

    if not compose_path.exists():
        msg = f"Compose file not found: {compose_path}"
        if json_output:
            print(json.dumps({"success": False, "message": msg}))
        else:
            console.print(f"[red]✗[/red] {msg}")
        raise typer.Exit(1)

    if not json_output:
        console.print(f"[bold]Configuring project: {project_path.name}[/bold]\n")

    # Detect domains before transformation
    domains = transformer.detect_domains(compose_path)

    # Transform compose file
    result = transformer.transform(compose_path, dry_run=dry_run)

    if json_output:
        print(
            json.dumps(
                {
                    "success": result.success,
                    "message": result.message,
                    "backup_path": result.backup_path,
                    "changes": result.changes,
                    "warnings": result.warnings,
                    "domains": domains,
                }
            )
        )
        return

    if result.success:
        console.print(f"[green]✓[/green] {result.message}")

        if result.changes:
            console.print("\n[bold]Changes:[/bold]")
            for change in result.changes:
                console.print(f"  • {change}")

        if result.warnings:
            console.print("\n[yellow]Warnings:[/yellow]")
            for warning in result.warnings:
                console.print(f"  ⚠ {warning}")

        if result.backup_path:
            console.print(f"\n[dim]Backup created: {result.backup_path}[/dim]")

        if domains:
            console.print("\n[bold]Detected domains:[/bold]")
            for domain in domains:
                console.print(f"  • {domain}")

        # Register the project (if not dry run)
        if not dry_run:
            project = RegisteredProject(
                name=project_path.name,
                path=str(project_path),
                domains=domains,
                compose_files=[compose_file],
                configured_at=datetime.now().isoformat(),
                backup_path=result.backup_path,
            )
            provider.register_project(project)
            console.print("\n[dim]Project registered in devflow infrastructure.[/dim]")
    else:
        console.print(f"[red]✗[/red] {result.message}")
        raise typer.Exit(1)


@app.command()
def unconfigure(
    project_path: Path = typer.Argument(..., help="Path to the project to unconfigure"),
    compose_file: str = typer.Option("docker-compose.yml", "--compose", "-c", help="Compose file to restore"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Restore project's original docker-compose configuration.

    Restores the docker-compose.yml from the most recent backup created by
    'devflow infra configure'.
    """
    from devflow.infrastructure.compose_transformer import ComposeTransformer

    provider = _get_provider()
    transformer = ComposeTransformer(provider.config)

    project_path = Path(project_path).resolve()
    compose_path = project_path / compose_file

    if not project_path.exists():
        msg = f"Project path does not exist: {project_path}"
        if json_output:
            print(json.dumps({"success": False, "message": msg}))
        else:
            console.print(f"[red]✗[/red] {msg}")
        raise typer.Exit(1)

    # Find backups
    backups = transformer.get_backups(compose_path)
    if not backups:
        msg = f"No backup files found for {compose_file}"
        if json_output:
            print(json.dumps({"success": False, "message": msg}))
        else:
            console.print(f"[yellow]⚠[/yellow] {msg}")
        raise typer.Exit(1)

    if not json_output:
        console.print(f"[bold]Restoring {compose_file} from backup...[/bold]\n")
        console.print(f"[dim]Using: {backups[0]}[/dim]\n")

    # Restore from backup
    success = transformer.restore(compose_path)

    if json_output:
        print(
            json.dumps(
                {
                    "success": success,
                    "message": "Restored from backup" if success else "Failed to restore",
                    "backup_used": str(backups[0]) if success else None,
                }
            )
        )
        return

    if success:
        console.print(f"[green]✓[/green] Restored {compose_file} from backup")

        # Unregister the project
        provider.unregister_project(str(project_path))
        console.print("[dim]Project unregistered from devflow infrastructure.[/dim]")
    else:
        console.print("[red]✗[/red] Failed to restore from backup")
        raise typer.Exit(1)


@app.command()
def certs(
    regenerate: bool = typer.Option(False, "--regenerate", "-r", help="Force regenerate certificates"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Manage TLS certificates.

    Generates locally-trusted TLS certificates using mkcert. Certificates are
    valid for *.localhost and configured project domains.
    """
    provider = _get_provider()

    if not json_output:
        console.print("[bold]TLS Certificates[/bold]\n")

    # Check mkcert availability
    from devflow.providers.mkcert import MkcertProvider

    mkcert = MkcertProvider()

    if not mkcert.is_available():
        msg = "mkcert is not installed. Install from: https://github.com/FiloSottile/mkcert"
        if json_output:
            print(json.dumps({"success": False, "message": msg}))
        else:
            console.print(f"[red]✗[/red] {msg}")
        raise typer.Exit(1)

    # Check if CA is installed
    ca_installed = mkcert.is_ca_installed()
    if not json_output:
        ca_status = "[green]installed[/green]" if ca_installed else "[yellow]not installed[/yellow]"
        console.print(f"CA Status: {ca_status}")
        if mkcert.get_ca_root():
            console.print(f"  Root: [dim]{mkcert.get_ca_root()}[/dim]")

    # Check certificates
    cert_exists = mkcert.cert_exists(str(provider.certs_dir))
    if not json_output:
        cert_status = "[green]valid[/green]" if cert_exists else "[yellow]not found[/yellow]"
        console.print(f"Certificates: {cert_status}")
        console.print(f"  Path: [dim]{provider.certs_dir}[/dim]")

    if regenerate or not cert_exists:
        if not json_output:
            action = "Regenerating" if regenerate else "Generating"
            console.print(f"\n[bold]{action} certificates...[/bold]")

        result = provider.regenerate_certificates()

        if json_output:
            print(
                json.dumps(
                    {
                        "success": result.success,
                        "message": result.message,
                        "ca_installed": ca_installed,
                        "cert_path": str(provider.certs_dir),
                    }
                )
            )
            return

        if result.success:
            console.print(f"[green]✓[/green] {result.message}")
        else:
            console.print(f"[red]✗[/red] {result.message}")
            raise typer.Exit(1)
    else:
        if json_output:
            print(
                json.dumps(
                    {
                        "success": True,
                        "message": "Certificates already exist",
                        "ca_installed": ca_installed,
                        "cert_path": str(provider.certs_dir),
                    }
                )
            )


@app.command()
def hosts(
    action: str = typer.Argument("list", help="Action: add, remove, or list"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Manage /etc/hosts entries.

    Lists, adds, or removes devflow-managed entries in /etc/hosts.

    Note: Adding/removing entries requires sudo/root access.
    """
    provider = _get_provider()

    if action == "list":
        entries = provider.get_hosts_entries()

        if json_output:
            print(json.dumps({"entries": entries}))
            return

        console.print("[bold]/etc/hosts entries (devflow-managed)[/bold]\n")
        if entries:
            for entry in entries:
                console.print(f"  {entry}")
        else:
            console.print("[dim]No devflow-managed entries found.[/dim]")

    elif action == "add":
        # Gather domains from registered projects
        projects = provider.get_registered_projects()
        all_domains = set(provider.config.certificates.domains)

        for project in projects:
            all_domains.update(project.domains)

        # Filter out wildcards (can't be added to /etc/hosts)
        domains = [d for d in all_domains if not d.startswith("*")]

        if not json_output:
            console.print("[bold]Adding hosts entries...[/bold]\n")

        result = provider.add_hosts_entries(domains)

        if json_output:
            print(
                json.dumps(
                    {
                        "success": result.success,
                        "message": result.message,
                        "details": result.details,
                    }
                )
            )
            return

        if result.success:
            console.print(f"[green]✓[/green] {result.message}")
        else:
            console.print(f"[yellow]⚠[/yellow] {result.message}")
            if result.details.get("entries"):
                console.print("\n[bold]Manual addition required:[/bold]")
                for entry in result.details["entries"]:
                    console.print(f"  {entry}")

    elif action == "remove":
        if not json_output:
            console.print("[bold]Removing hosts entries...[/bold]\n")

        result = provider.remove_hosts_entries()

        if json_output:
            print(json.dumps({"success": result.success, "message": result.message}))
            return

        if result.success:
            console.print(f"[green]✓[/green] {result.message}")
        else:
            console.print(f"[red]✗[/red] {result.message}")
            raise typer.Exit(1)

    else:
        msg = f"Unknown action: {action}. Use 'add', 'remove', or 'list'."
        if json_output:
            print(json.dumps({"success": False, "message": msg}))
        else:
            console.print(f"[red]✗[/red] {msg}")
        raise typer.Exit(1)


@app.command()
def network(
    action: str = typer.Argument("status", help="Action: status, create, or remove"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Manage the shared Docker network.

    The devflow-proxy network is used by all projects to communicate with
    the shared Traefik instance.
    """
    provider = _get_provider()

    if action == "status":
        infra_status = provider.status()

        if json_output:
            print(
                json.dumps(
                    {
                        "network_name": infra_status.network_name,
                        "exists": infra_status.network_exists,
                    }
                )
            )
            return

        console.print("[bold]Network Status[/bold]\n")
        status_icon = "[green]✓[/green]" if infra_status.network_exists else "[red]✗[/red]"
        status_text = "exists" if infra_status.network_exists else "does not exist"
        console.print(f"Network '{infra_status.network_name}': {status_icon} {status_text}")

    elif action == "create":
        if not json_output:
            console.print("[bold]Creating network...[/bold]\n")

        result = provider.create_network()

        if json_output:
            print(json.dumps({"success": result.success, "message": result.message}))
            return

        if result.success:
            console.print(f"[green]✓[/green] {result.message}")
        else:
            console.print(f"[red]✗[/red] {result.message}")
            raise typer.Exit(1)

    elif action == "remove":
        if not json_output:
            console.print("[bold]Removing network...[/bold]\n")

        result = provider.remove_network()

        if json_output:
            print(json.dumps({"success": result.success, "message": result.message}))
            return

        if result.success:
            console.print(f"[green]✓[/green] {result.message}")
        else:
            console.print(f"[red]✗[/red] {result.message}")
            raise typer.Exit(1)

    else:
        msg = f"Unknown action: {action}. Use 'status', 'create', or 'remove'."
        if json_output:
            print(json.dumps({"success": False, "message": msg}))
        else:
            console.print(f"[red]✗[/red] {msg}")
        raise typer.Exit(1)


@app.command()
def doctor(
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Check infrastructure health and prerequisites.

    Verifies that all required tools are installed and configured:
    - Docker is running
    - mkcert is installed and CA is trusted
    - Network exists
    - Traefik is running
    - Certificates are valid
    """
    provider = _get_provider()
    diagnostics = provider.doctor()

    if json_output:
        print(json.dumps(diagnostics, indent=2))
        return

    console.print("[bold]Infrastructure Health Check[/bold]\n")

    # Docker
    console.print("[bold]Docker:[/bold]")
    docker = diagnostics["docker"]
    docker_icon = "[green]✓[/green]" if docker["available"] else "[red]✗[/red]"
    console.print(f"  {docker_icon} Installed: {docker['available']}")

    if docker["available"]:
        daemon_icon = "[green]✓[/green]" if docker["daemon_running"] else "[red]✗[/red]"
        console.print(f"  {daemon_icon} Daemon running: {docker['daemon_running']}")
        if docker["version"]:
            console.print(f"  [dim]Version: {docker['version']}[/dim]")

    # mkcert
    console.print("\n[bold]mkcert:[/bold]")
    mkcert = diagnostics["mkcert"]
    mkcert_icon = "[green]✓[/green]" if mkcert["available"] else "[red]✗[/red]"
    console.print(f"  {mkcert_icon} Installed: {mkcert['available']}")

    if mkcert["available"]:
        ca_icon = "[green]✓[/green]" if mkcert["ca_installed"] else "[yellow]⚠[/yellow]"
        console.print(f"  {ca_icon} CA installed: {mkcert['ca_installed']}")
        if mkcert["version"]:
            console.print(f"  [dim]Version: {mkcert['version']}[/dim]")
        if mkcert["ca_root"]:
            console.print(f"  [dim]CA root: {mkcert['ca_root']}[/dim]")

    # Infrastructure
    console.print("\n[bold]Infrastructure:[/bold]")
    infra = diagnostics["infrastructure"]

    network_icon = "[green]✓[/green]" if infra["network_exists"] else "[yellow]⚠[/yellow]"
    console.print(f"  {network_icon} Network exists: {infra['network_exists']}")

    traefik_icon = "[green]✓[/green]" if infra["traefik_running"] else "[yellow]⚠[/yellow]"
    console.print(f"  {traefik_icon} Traefik running: {infra['traefik_running']}")

    certs_icon = "[green]✓[/green]" if infra["certificates_exist"] else "[yellow]⚠[/yellow]"
    console.print(f"  {certs_icon} Certificates exist: {infra['certificates_exist']}")

    console.print(f"  [dim]Home: {infra['devflow_home']}[/dim]")

    # Overall status
    all_ok = (
        docker["available"]
        and docker["daemon_running"]
        and mkcert["available"]
        and mkcert["ca_installed"]
        and infra["network_exists"]
        and infra["traefik_running"]
        and infra["certificates_exist"]
    )

    console.print()
    if all_ok:
        console.print("[green]✓ All checks passed![/green]")
    else:
        console.print("[yellow]⚠ Some checks failed. Run 'devflow infra up' to fix.[/yellow]")
        raise typer.Exit(1)
