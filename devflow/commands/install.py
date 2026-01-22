"""First-time devflow installation and Claude Code plugin setup."""

import shutil
import subprocess
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

app = typer.Typer()
console = Console()


def get_devflow_root() -> Path:
    """Get the root directory of the devflow installation."""
    # This file is at devflow/commands/install.py
    # Root is two levels up
    return Path(__file__).parent.parent.parent


def is_claude_code_installed() -> bool:
    """Check if Claude Code CLI is available."""
    return shutil.which("claude") is not None


def is_plugin_installed() -> bool:
    """Check if devflow plugin is installed in Claude Code settings."""
    import json

    settings_path = Path.home() / ".claude" / "settings.json"
    if not settings_path.exists():
        return False

    try:
        with open(settings_path) as f:
            settings = json.load(f)
        plugins = settings.get("plugins", [])
        devflow_root = str(get_devflow_root())
        return devflow_root in plugins or any("devflow" in p for p in plugins)
    except (json.JSONDecodeError, OSError):
        return False


def get_claude_settings_path() -> Path:
    """Get the path to Claude Code user settings."""
    return Path.home() / ".claude" / "settings.json"


def install_claude_plugin(devflow_root: Path) -> bool:
    """Install devflow as a Claude Code plugin by adding to settings."""
    import json

    console.print("\n[bold]Installing Claude Code plugin...[/bold]")

    # First validate the plugin
    try:
        result = subprocess.run(
            ["claude", "plugin", "validate", str(devflow_root)],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            console.print(f"[red]✗[/red] Plugin validation failed: {result.stderr}")
            return False
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        console.print(f"[red]✗[/red] Could not validate plugin: {e}")
        return False

    console.print("[green]✓[/green] Plugin validated")

    # Add to user settings
    settings_path = get_claude_settings_path()
    settings_path.parent.mkdir(parents=True, exist_ok=True)

    # Load existing settings or create new
    if settings_path.exists():
        try:
            with open(settings_path) as f:
                settings = json.load(f)
        except json.JSONDecodeError:
            settings = {}
    else:
        settings = {}

    # Add plugin to plugins list
    plugins = settings.get("plugins", [])
    plugin_path = str(devflow_root)

    if plugin_path in plugins:
        console.print("[green]✓[/green] Plugin already in settings")
        return True

    plugins.append(plugin_path)
    settings["plugins"] = plugins

    # Write settings
    try:
        with open(settings_path, "w") as f:
            json.dump(settings, f, indent=2)
        console.print(f"[green]✓[/green] Added plugin to {settings_path}")
        console.print("\n[yellow]Note:[/yellow] Restart Claude Code for changes to take effect")
        return True
    except OSError as e:
        console.print(f"[red]✗[/red] Could not write settings: {e}")
        return False


def check_prerequisites() -> dict[str, bool]:
    """Check all prerequisite tools."""
    tools = {
        "git": shutil.which("git") is not None,
        "docker": shutil.which("docker") is not None,
        "gh": shutil.which("gh") is not None,
        "psql": shutil.which("psql") is not None,
        "claude": shutil.which("claude") is not None,
    }

    # Optional tools
    optional = {
        "op": shutil.which("op") is not None,
        "supabase": shutil.which("supabase") is not None,
        "mkcert": shutil.which("mkcert") is not None,
    }

    return {"required": tools, "optional": optional}


@app.command()
def install(
    skip_plugin: bool = typer.Option(False, "--skip-plugin", help="Skip Claude Code plugin installation"),
    force: bool = typer.Option(False, "--force", "-f", help="Force reinstall even if already installed"),
) -> None:
    """
    First-time devflow setup.

    Installs the Claude Code plugin and verifies prerequisites.
    Run this once after cloning the devflow repository.
    """
    console.print(
        Panel.fit(
            "[bold blue]Devflow Installation[/bold blue]\n" "Setting up devflow CLI and Claude Code integration",
            border_style="blue",
        )
    )

    devflow_root = get_devflow_root()
    console.print(f"\nDevflow root: [dim]{devflow_root}[/dim]")

    # Check prerequisites
    console.print("\n[bold]Checking prerequisites...[/bold]")
    prereqs = check_prerequisites()

    # Required tools table
    table = Table(title="Required Tools")
    table.add_column("Tool", style="cyan")
    table.add_column("Status")
    table.add_column("Purpose", style="dim")

    tool_purposes = {
        "git": "Version control",
        "docker": "Container runtime",
        "gh": "GitHub CLI",
        "psql": "PostgreSQL client",
        "claude": "Claude Code CLI",
    }

    all_required_ok = True
    for tool, installed in prereqs["required"].items():
        status = "[green]✓ Installed[/green]" if installed else "[red]✗ Missing[/red]"
        table.add_row(tool, status, tool_purposes.get(tool, ""))
        if not installed:
            all_required_ok = False

    console.print(table)

    # Optional tools table
    opt_table = Table(title="Optional Tools")
    opt_table.add_column("Tool", style="cyan")
    opt_table.add_column("Status")
    opt_table.add_column("Purpose", style="dim")

    opt_purposes = {
        "op": "1Password CLI (secrets)",
        "supabase": "Supabase CLI (migrations)",
        "mkcert": "Local TLS certificates",
    }

    for tool, installed in prereqs["optional"].items():
        status = "[green]✓ Installed[/green]" if installed else "[yellow]○ Not installed[/yellow]"
        opt_table.add_row(tool, status, opt_purposes.get(tool, ""))

    console.print(opt_table)

    if not all_required_ok:
        console.print("\n[yellow]Warning:[/yellow] Some required tools are missing.")
        console.print("Install them before using devflow features that depend on them.")

    # Claude Code plugin installation
    if not skip_plugin:
        if not prereqs["required"]["claude"]:
            console.print("\n[yellow]Skipping plugin install:[/yellow] Claude Code CLI not found")
            console.print("Install Claude Code first: [link]https://claude.ai/code[/link]")
        else:
            if is_plugin_installed() and not force:
                console.print("\n[green]✓[/green] Claude Code plugin already installed")
                console.print("  Use [bold]--force[/bold] to reinstall")
            else:
                success = install_claude_plugin(devflow_root)
                if not success:
                    console.print("\n[yellow]You can install the plugin manually:[/yellow]")
                    console.print(f"  claude plugin install {devflow_root}")
    else:
        console.print("\n[dim]Skipping Claude Code plugin installation (--skip-plugin)[/dim]")

    # Summary and next steps
    console.print("\n" + "─" * 50)
    console.print("\n[bold green]Installation complete![/bold green]\n")

    console.print("[bold]Next steps:[/bold]")
    console.print("  1. Navigate to your project directory")
    console.print("  2. Run [bold]devflow init --preset aocodex[/bold] to create config")
    console.print("  3. Run [bold]devflow doctor[/bold] to verify setup")
    console.print("  4. Run [bold]devflow infra up[/bold] to start shared infrastructure")

    if prereqs["required"]["claude"]:
        console.print("\n[bold]Claude Code skills available:[/bold]")
        console.print("  /devflow:setup        - Initialize local environment")
        console.print("  /devflow:migrate      - Run database migrations")
        console.print("  /devflow:status       - Check project health")
        console.print("  /devflow:doctor       - Troubleshoot issues")
        console.print("  /devflow:multi-project - Manage multiple projects")


@app.command()
def uninstall(
    keep_config: bool = typer.Option(False, "--keep-config", help="Keep configuration files"),
) -> None:
    """
    Remove devflow Claude Code plugin.

    This only removes the Claude Code integration, not the CLI itself.
    """
    import json

    if not is_plugin_installed():
        console.print("[yellow]Devflow plugin not installed[/yellow]")
        return

    console.print("Removing Claude Code plugin...")

    settings_path = Path.home() / ".claude" / "settings.json"

    try:
        with open(settings_path) as f:
            settings = json.load(f)

        plugins = settings.get("plugins", [])
        devflow_root = str(get_devflow_root())

        # Remove devflow from plugins list
        plugins = [p for p in plugins if devflow_root not in p and "devflow" not in p]
        settings["plugins"] = plugins

        with open(settings_path, "w") as f:
            json.dump(settings, f, indent=2)

        console.print("[green]✓[/green] Plugin removed from settings")
        console.print("\n[yellow]Note:[/yellow] Restart Claude Code for changes to take effect")

    except (json.JSONDecodeError, OSError) as e:
        console.print(f"[red]✗[/red] Error: {e}")


@app.command()
def status() -> None:
    """Show devflow installation status."""
    devflow_root = get_devflow_root()

    console.print(
        Panel.fit(
            "[bold]Devflow Installation Status[/bold]",
            border_style="blue",
        )
    )

    console.print(f"\n[bold]Installation path:[/bold] {devflow_root}")

    # Check plugin status
    claude_installed = is_claude_code_installed()
    plugin_installed = is_plugin_installed() if claude_installed else False

    console.print("\n[bold]Claude Code CLI:[/bold] ", end="")
    if claude_installed:
        console.print("[green]✓ Installed[/green]")
    else:
        console.print("[red]✗ Not found[/red]")

    console.print("[bold]Devflow plugin:[/bold]  ", end="")
    if plugin_installed:
        console.print("[green]✓ Installed[/green]")
    elif not claude_installed:
        console.print("[dim]N/A (Claude Code not installed)[/dim]")
    else:
        console.print("[yellow]○ Not installed[/yellow]")
        console.print("\n  Run: [bold]devflow install[/bold]")

    # Check for plugin files
    plugin_json = devflow_root / ".claude-plugin" / "plugin.json"
    skills_dir = devflow_root / "skills"

    console.print("\n[bold]Plugin manifest:[/bold] ", end="")
    if plugin_json.exists():
        console.print(f"[green]✓[/green] {plugin_json}")
    else:
        console.print("[red]✗ Missing[/red]")

    console.print("[bold]Skills directory:[/bold] ", end="")
    if skills_dir.exists():
        skill_count = len(list(skills_dir.iterdir()))
        console.print(f"[green]✓[/green] {skill_count} skills")
    else:
        console.print("[red]✗ Missing[/red]")
