"""Remote Docker context management commands."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(no_args_is_help=True, help="Manage Docker remote contexts and tunnels")
console = Console()


def _get_remote_config():
    """Get the remote context configuration from devflow.yml."""
    from devflow.core.config import load_project_config

    config = load_project_config()
    if config and config.remote:
        return config.remote
    return None


@app.command("list")
def list_contexts(
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """List all available Docker contexts.

    Shows both local and DevFlow-managed remote contexts. The current context
    is marked with an indicator.
    """
    from devflow.providers.remote.context import DockerContextManager

    manager = DockerContextManager()
    contexts = manager.list_contexts()

    if json_output:
        print(json.dumps([ctx.to_dict() for ctx in contexts], indent=2))
        return

    console.print("[bold]Docker Contexts[/bold]\n")

    table = Table(show_header=True)
    table.add_column("", width=2)  # Current indicator
    table.add_column("Name")
    table.add_column("Endpoint")
    table.add_column("Type")

    for ctx in contexts:
        current = "[green]●[/green]" if ctx.is_current else ""
        ctx_type = "[cyan]devflow[/cyan]" if ctx.is_devflow_context() else "[dim]system[/dim]"
        table.add_row(current, ctx.name, ctx.docker_endpoint, ctx_type)

    console.print(table)


@app.command("create")
def create_context(
    name: str = typer.Argument(..., help="Name for the context (will be prefixed with 'devflow-')"),
    host: str = typer.Option(..., "--host", "-h", help="Remote hostname or IP address"),
    user: str = typer.Option("root", "--user", "-u", help="SSH username"),
    port: int = typer.Option(22, "--port", "-p", help="SSH port"),
    key: Optional[Path] = typer.Option(None, "--key", "-k", help="Path to SSH private key"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Create a new remote Docker context.

    Creates a Docker context that connects to a remote Docker daemon over SSH.
    The context name will be prefixed with 'devflow-' for easy identification.

    Example:
        devflow context create dev-server --host 192.168.1.100 --user developer
    """
    from devflow.core.config import RemoteContextConfig
    from devflow.providers.remote.context import DockerContextManager

    config = RemoteContextConfig(
        enabled=True,
        name=name,
        host=host,
        user=user,
        ssh_port=port,
        ssh_key=key,
    )

    manager = DockerContextManager(config)
    success, message = manager.create_remote_context(name, config)

    if json_output:
        print(json.dumps({"success": success, "message": message, "context_name": f"devflow-{name}"}))
        return

    if success:
        console.print(f"[green]✓[/green] {message}")
        console.print(f"\nTo use this context: [cyan]devflow context use {name}[/cyan]")
    else:
        console.print(f"[red]✗[/red] {message}")
        raise typer.Exit(1)


@app.command("delete")
def delete_context(
    name: str = typer.Argument(..., help="Context name to delete"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Delete a DevFlow-managed Docker context.

    Only DevFlow-managed contexts (prefixed with 'devflow-') can be deleted.
    System contexts like 'default' are protected.
    """
    from devflow.providers.remote.context import DockerContextManager

    manager = DockerContextManager()
    success, message = manager.delete_context(name)

    if json_output:
        print(json.dumps({"success": success, "message": message}))
        return

    if success:
        console.print(f"[green]✓[/green] {message}")
    else:
        console.print(f"[red]✗[/red] {message}")
        raise typer.Exit(1)


@app.command("use")
def use_context(
    name: str = typer.Argument(..., help="Context name, or 'local' to switch to default"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Switch to a Docker context.

    Use 'local' to switch back to the default local Docker daemon.

    Examples:
        devflow context use dev-server  # Use remote context
        devflow context use local       # Switch back to local Docker
    """
    from devflow.providers.remote.context import DockerContextManager

    manager = DockerContextManager()

    if name == "local":
        success, message = manager.use_local()
    else:
        success, message = manager.use_context(name)

    if json_output:
        print(json.dumps({"success": success, "message": message}))
        return

    if success:
        console.print(f"[green]✓[/green] {message}")
    else:
        console.print(f"[red]✗[/red] {message}")
        raise typer.Exit(1)


@app.command("test")
def test_context(
    name: Optional[str] = typer.Argument(None, help="Context name to test (defaults to current)"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Test connection to a Docker context.

    Verifies that the Docker daemon is accessible through the specified context.
    If no context name is given, tests the current context.
    """
    from devflow.providers.remote.context import DockerContextManager

    manager = DockerContextManager()
    success, message = manager.test_connection(name)

    if json_output:
        print(json.dumps({"success": success, "message": message, "context": name or "current"}))
        return

    if success:
        console.print(f"[green]✓[/green] {message}")
    else:
        console.print(f"[red]✗[/red] {message}")
        raise typer.Exit(1)


# Tunnel subcommands
tunnel_app = typer.Typer(no_args_is_help=True, help="Manage SSH tunnels for remote contexts")
app.add_typer(tunnel_app, name="tunnel")


@tunnel_app.command("start")
def tunnel_start(
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Start SSH tunnel for the configured remote context.

    Uses the remote context configuration from devflow.yml to establish
    SSH port forwarding for the configured ports (HTTP, HTTPS, PostgreSQL, etc.).

    Uses autossh for automatic reconnection if available.
    """
    from devflow.providers.remote.ssh_tunnel import SSHTunnelProvider

    config = _get_remote_config()

    if not config or not config.enabled:
        msg = "No remote context configured in devflow.yml"
        if json_output:
            print(json.dumps({"success": False, "message": msg}))
        else:
            console.print(f"[red]✗[/red] {msg}")
            console.print("\n[dim]Add a 'remote' section to your devflow.yml:[/dim]")
            console.print("""
remote:
  enabled: true
  host: your-server.example.com
  user: developer
  ssh_key: ~/.ssh/id_ed25519
""")
        raise typer.Exit(1)

    tunnel = SSHTunnelProvider(config)

    if not tunnel.is_available():
        msg = "SSH is not available on this system"
        if json_output:
            print(json.dumps({"success": False, "message": msg}))
        else:
            console.print(f"[red]✗[/red] {msg}")
        raise typer.Exit(1)

    if not json_output:
        console.print(f"[bold]Starting tunnel to {config.host}...[/bold]\n")

    try:
        tunnel.start()
        health = tunnel.health()

        if json_output:
            print(json.dumps({"success": True, "message": "Tunnel started", **health.to_dict()}))
            return

        console.print(f"[green]✓[/green] Tunnel started (PID: {health.pid})")
        console.print("\n[bold]Forwarded ports:[/bold]")
        for t in config.tunnels:
            desc = f" ({t.description})" if t.description else ""
            console.print(f"  localhost:{t.local} → remote:{t.remote}{desc}")

    except RuntimeError as e:
        if json_output:
            print(json.dumps({"success": False, "message": str(e)}))
        else:
            console.print(f"[red]✗[/red] {e}")
        raise typer.Exit(1)


@tunnel_app.command("stop")
def tunnel_stop(
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Stop the SSH tunnel."""
    from devflow.providers.remote.ssh_tunnel import SSHTunnelProvider

    config = _get_remote_config()

    if not config:
        msg = "No remote context configured in devflow.yml"
        if json_output:
            print(json.dumps({"success": False, "message": msg}))
        else:
            console.print(f"[yellow]⚠[/yellow] {msg}")
        raise typer.Exit(1)

    tunnel = SSHTunnelProvider(config)
    tunnel.stop()

    if json_output:
        print(json.dumps({"success": True, "message": "Tunnel stopped"}))
    else:
        console.print("[green]✓[/green] Tunnel stopped")


@tunnel_app.command("status")
def tunnel_status(
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Check the status of the SSH tunnel."""
    from devflow.providers.remote.ssh_tunnel import SSHTunnelProvider
    from devflow.providers.remote.tunnel import TunnelStatus

    config = _get_remote_config()

    if not config:
        msg = "No remote context configured in devflow.yml"
        if json_output:
            print(json.dumps({"configured": False, "message": msg}))
        else:
            console.print(f"[dim]○ {msg}[/dim]")
        return

    tunnel = SSHTunnelProvider(config)
    health = tunnel.health()

    if json_output:
        print(json.dumps({"configured": True, **health.to_dict()}))
        return

    console.print("[bold]Tunnel Status[/bold]\n")
    console.print(f"Remote Host: [cyan]{config.host}[/cyan]")
    console.print(f"User: [dim]{config.user}[/dim]")

    if health.status == TunnelStatus.RUNNING:
        console.print(f"\nStatus: [green]● Running[/green]")
        console.print(f"  PID: {health.pid}")
        if health.latency_ms is not None:
            console.print(f"  Latency: {health.latency_ms:.1f}ms")
        if health.uptime_seconds is not None:
            uptime_min = health.uptime_seconds // 60
            uptime_sec = health.uptime_seconds % 60
            console.print(f"  Uptime: {uptime_min}m {uptime_sec}s")
    elif health.status == TunnelStatus.STOPPED:
        console.print(f"\nStatus: [dim]○ Stopped[/dim]")
    elif health.status == TunnelStatus.RECONNECTING:
        console.print(f"\nStatus: [yellow]◐ Reconnecting[/yellow]")
        if health.error:
            console.print(f"  {health.error}")
    else:
        console.print(f"\nStatus: [red]✗ {health.status.value}[/red]")
        if health.error:
            console.print(f"  [red]{health.error}[/red]")

    console.print("\n[bold]Configured Tunnels:[/bold]")
    for t in config.tunnels:
        desc = f" ({t.description})" if t.description else ""
        console.print(f"  localhost:{t.local} → remote:{t.remote}{desc}")


@tunnel_app.command("restart")
def tunnel_restart(
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Restart the SSH tunnel."""
    from devflow.providers.remote.ssh_tunnel import SSHTunnelProvider

    config = _get_remote_config()

    if not config:
        msg = "No remote context configured in devflow.yml"
        if json_output:
            print(json.dumps({"success": False, "message": msg}))
        else:
            console.print(f"[red]✗[/red] {msg}")
        raise typer.Exit(1)

    tunnel = SSHTunnelProvider(config)

    if not json_output:
        console.print("[bold]Restarting tunnel...[/bold]\n")

    tunnel.stop()

    try:
        tunnel.start()
        health = tunnel.health()

        if json_output:
            print(json.dumps({"success": True, "message": "Tunnel restarted", **health.to_dict()}))
        else:
            console.print(f"[green]✓[/green] Tunnel restarted (PID: {health.pid})")

    except RuntimeError as e:
        if json_output:
            print(json.dumps({"success": False, "message": str(e)}))
        else:
            console.print(f"[red]✗[/red] {e}")
        raise typer.Exit(1)
