"""Doctor command - system health checks and diagnostics."""

import shutil
import subprocess
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from devflow.core.config import DEVFLOW_HOME, is_devflow_initialized, load_global_config

console = Console()


def check_tool(name: str, binary: str, version_flag: str = "--version") -> dict:
    """Check if a tool is installed and get its version."""
    path = shutil.which(binary)
    if not path:
        return {"name": name, "binary": binary, "installed": False, "version": None, "path": None}

    try:
        result = subprocess.run([binary, version_flag], capture_output=True, text=True, timeout=10)
        version = result.stdout.strip() or result.stderr.strip()
        # Extract just the version number from the output
        version_line = version.split("\n")[0] if version else "unknown"
    except (subprocess.TimeoutExpired, subprocess.SubprocessError):
        version_line = "unknown"

    return {"name": name, "binary": binary, "installed": True, "version": version_line, "path": path}


def check_authentication(tool: str) -> tuple[bool, str]:
    """Check if a tool is authenticated."""
    try:
        if tool == "gh":
            result = subprocess.run(["gh", "auth", "status"], capture_output=True, text=True, timeout=10)
            return result.returncode == 0, "Authenticated" if result.returncode == 0 else "Not authenticated"

        elif tool == "op":
            result = subprocess.run(["op", "account", "list"], capture_output=True, text=True, timeout=10)
            return result.returncode == 0, "Signed in" if result.returncode == 0 else "Not signed in"

        elif tool == "docker":
            result = subprocess.run(["docker", "info"], capture_output=True, text=True, timeout=10)
            return result.returncode == 0, "Running" if result.returncode == 0 else "Not running"

        elif tool == "supabase":
            # For self-hosted, no auth is needed - just check if CLI works
            result = subprocess.run(["supabase", "--version"], capture_output=True, text=True, timeout=10)
            return result.returncode == 0, "Ready (self-hosted)" if result.returncode == 0 else "Not working"

    except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError):
        pass

    return False, "Check failed"


def doctor(
    fix: bool = typer.Option(False, "--fix", help="Attempt to fix issues automatically"),
) -> None:
    """Check system health and verify all required tools are installed."""
    console.print("\n[bold]Devflow System Health Check[/bold]\n")

    # Required tools
    required_tools = [
        ("GitHub CLI", "gh"),
        ("1Password CLI", "op"),
        ("Docker", "docker"),
        ("Supabase CLI", "supabase"),
        ("PostgreSQL Client", "psql"),
        ("Git", "git"),
    ]

    # Check tool installation
    table = Table(title="Tool Installation")
    table.add_column("Tool", style="cyan")
    table.add_column("Binary", style="dim")
    table.add_column("Status", style="bold")
    table.add_column("Version")

    all_installed = True
    tool_statuses = {}

    for name, binary in required_tools:
        status = check_tool(name, binary)
        tool_statuses[binary] = status

        if status["installed"]:
            status_str = "[green]Installed[/green]"
            version_str = status["version"][:50] if status["version"] else "unknown"
        else:
            status_str = "[red]Missing[/red]"
            version_str = "-"
            all_installed = False

        table.add_row(name, binary, status_str, version_str)

    console.print(table)

    # Check authentication for installed tools
    auth_tools = ["gh", "op", "docker", "supabase"]
    auth_table = Table(title="\nAuthentication Status")
    auth_table.add_column("Tool", style="cyan")
    auth_table.add_column("Status", style="bold")
    auth_table.add_column("Details")

    for tool in auth_tools:
        if tool_statuses.get(tool, {}).get("installed"):
            is_auth, details = check_authentication(tool)
            status_str = "[green]OK[/green]" if is_auth else "[yellow]Action needed[/yellow]"
            auth_table.add_row(tool, status_str, details)
        else:
            auth_table.add_row(tool, "[dim]Skipped[/dim]", "Tool not installed")

    console.print(auth_table)

    # Check for devflow configuration
    console.print("\n[bold]Configuration Status[/bold]")

    # Check global setup
    global_config_path = DEVFLOW_HOME / "config.yml"
    if is_devflow_initialized():
        global_config = load_global_config()
        console.print("  [green]Global setup:[/green] Completed")
        console.print(f"  [green]Global config:[/green] {global_config_path}")
        if global_config.git.user_name:
            console.print(f"    Git name: {global_config.git.user_name}")
        if global_config.git.user_email:
            console.print(f"    Git email: {global_config.git.user_email}")
    else:
        console.print("  [yellow]Global setup:[/yellow] Not completed (run 'devflow install' first)")
        if global_config_path.exists():
            console.print(f"  [dim]Global config:[/dim] {global_config_path} (setup incomplete)")
        else:
            console.print("  [dim]Global config:[/dim] Not found")

    # Check project config
    config_path = Path.cwd() / "devflow.yml"
    if config_path.exists():
        console.print(f"  [green]Project config:[/green] {config_path}")
    else:
        console.print("  [yellow]Project config:[/yellow] Not found (run 'devflow init' to create)")

    # Summary
    console.print("\n[bold]Summary[/bold]")

    # Check global setup first
    if not is_devflow_initialized():
        console.print("  [yellow]⚠ Devflow not set up.[/yellow]")
        console.print("    Run: [bold]devflow install[/bold]")
        console.print()

    if all_installed:
        console.print("  [green]All required tools are installed.[/green]")
    else:
        console.print("  [red]Some required tools are missing.[/red]")
        console.print("\n  Install missing tools:")
        if not tool_statuses.get("gh", {}).get("installed"):
            console.print("    gh:       https://cli.github.com/")
        if not tool_statuses.get("op", {}).get("installed"):
            console.print("    op:       https://1password.com/downloads/command-line/")
        if not tool_statuses.get("docker", {}).get("installed"):
            console.print("    docker:   https://docs.docker.com/get-docker/")
        if not tool_statuses.get("supabase", {}).get("installed"):
            console.print("    supabase: https://supabase.com/docs/guides/cli")
        if not tool_statuses.get("psql", {}).get("installed"):
            console.print("    psql:     apt install postgresql-client (or brew install postgresql)")

    console.print()
