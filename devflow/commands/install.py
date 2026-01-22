"""First-time devflow installation and Claude Code plugin setup."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table

from devflow.core.config import (
    DEVFLOW_HOME,
    GlobalConfig,
    is_devflow_initialized,
    load_global_config,
    save_global_config,
)

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


def check_prerequisites() -> dict[str, dict[str, bool]]:
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


def get_current_git_config() -> tuple[str | None, str | None]:
    """Get current git user.name and user.email from global config."""
    name = None
    email = None

    try:
        result = subprocess.run(
            ["git", "config", "--global", "user.name"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            name = result.stdout.strip() or None
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    try:
        result = subprocess.run(
            ["git", "config", "--global", "user.email"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            email = result.stdout.strip() or None
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    return name, email


def create_devflow_directories() -> None:
    """Create the ~/.devflow directory structure."""
    directories = [
        DEVFLOW_HOME,
        DEVFLOW_HOME / "certs",
        DEVFLOW_HOME / "infrastructure",
        DEVFLOW_HOME / "infrastructure" / "dynamic",
    ]

    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)

    console.print(f"[green]✓[/green] Created {DEVFLOW_HOME}")


def setup_git_config(config: GlobalConfig, interactive: bool = True) -> GlobalConfig:
    """Configure git settings interactively or from existing git config."""
    console.print("\n[bold]Git Configuration[/bold]")

    # Get existing git config
    current_name, current_email = get_current_git_config()

    if interactive:
        # Prompt for name
        if current_name:
            console.print(f"  Current git user.name: [cyan]{current_name}[/cyan]")
            use_existing = Confirm.ask("  Use this name for devflow?", default=True)
            if use_existing:
                config.git.user_name = current_name
            else:
                config.git.user_name = Prompt.ask("  Enter your name")
        else:
            config.git.user_name = Prompt.ask("  Enter your name (for git commits)")

        # Prompt for email
        if current_email:
            console.print(f"  Current git user.email: [cyan]{current_email}[/cyan]")
            use_existing = Confirm.ask("  Use this email for devflow?", default=True)
            if use_existing:
                config.git.user_email = current_email
            else:
                config.git.user_email = Prompt.ask("  Enter your email")
        else:
            config.git.user_email = Prompt.ask("  Enter your email (for git commits)")

        # Co-author configuration
        console.print("\n  [dim]AI co-author adds 'Co-Authored-By: Claude' to commits made with AI assistance[/dim]")
        config.git.co_author_enabled = Confirm.ask("  Enable AI co-author in commits?", default=True)
    else:
        # Non-interactive: use existing git config if available
        config.git.user_name = current_name
        config.git.user_email = current_email

    if config.git.user_name:
        console.print(f"[green]✓[/green] Git name: {config.git.user_name}")
    if config.git.user_email:
        console.print(f"[green]✓[/green] Git email: {config.git.user_email}")

    return config


def setup_defaults(config: GlobalConfig, interactive: bool = True) -> GlobalConfig:
    """Configure default settings."""
    console.print("\n[bold]Default Settings[/bold]")

    if interactive:
        # Secrets provider
        console.print("\n  [dim]Secrets provider is used to manage environment secrets[/dim]")
        provider_choice = Prompt.ask(
            "  Default secrets provider",
            choices=["1password", "env", "none"],
            default="none",
        )
        config.defaults.secrets_provider = None if provider_choice == "none" else provider_choice

        # Container registry
        registry = Prompt.ask(
            "  Default container registry (leave empty if none)",
            default="",
        )
        config.defaults.registry = registry if registry else None

    if config.defaults.secrets_provider:
        console.print(f"[green]✓[/green] Secrets provider: {config.defaults.secrets_provider}")
    else:
        console.print("[dim]○ Secrets provider: none (configure per-project)[/dim]")

    if config.defaults.registry:
        console.print(f"[green]✓[/green] Container registry: {config.defaults.registry}")
    else:
        console.print("[dim]○ Container registry: none (configure per-project)[/dim]")

    return config


def setup_infrastructure(prereqs: dict[str, dict[str, bool]], interactive: bool = True) -> bool:
    """Optionally set up shared infrastructure (Traefik, certificates)."""
    console.print("\n[bold]Shared Infrastructure[/bold]")
    console.print("  [dim]Shared infrastructure provides a local Traefik proxy and TLS certificates[/dim]")
    console.print("  [dim]for developing multiple projects that need HTTPS.[/dim]")

    # Check if mkcert and docker are available
    has_mkcert = prereqs["optional"].get("mkcert", False)
    has_docker = prereqs["required"].get("docker", False)

    if not has_docker:
        console.print("\n[yellow]○ Skipping infrastructure setup:[/yellow] Docker not installed")
        return False

    if not has_mkcert:
        console.print("\n[yellow]○ Skipping infrastructure setup:[/yellow] mkcert not installed")
        console.print("  Install mkcert for local TLS certificates: https://github.com/FiloSottile/mkcert")
        return False

    if interactive:
        setup_infra = Confirm.ask("\n  Set up shared infrastructure now?", default=False)
        if not setup_infra:
            console.print("[dim]○ Skipping infrastructure setup (run 'devflow infra up' later)[/dim]")
            return False

    # Run devflow infra up
    console.print("\n[bold]Setting up shared infrastructure...[/bold]")
    try:
        # Import and run the infra up command
        from devflow.providers.infrastructure import InfrastructureProvider

        provider = InfrastructureProvider()

        # Create network
        result = provider.create_network()
        if result.success:
            console.print(f"[green]✓[/green] {result.message}")
        else:
            console.print(f"[yellow]○[/yellow] {result.message}")

        # Generate certificates
        from devflow.providers.mkcert import MkcertProvider

        mkcert = MkcertProvider()
        if mkcert.is_available():
            if not mkcert.is_ca_installed():
                console.print("  Installing mkcert CA...")
                mkcert.install_ca()

            certs_dir = DEVFLOW_HOME / "certs"
            cert_success, cert_message = mkcert.generate_cert(
                ["localhost", "*.localhost", "traefik.localhost"],
                str(certs_dir),
            )
            if cert_success:
                console.print("[green]✓[/green] Generated TLS certificates")
            else:
                console.print(f"[yellow]○[/yellow] Certificate generation: {cert_message}")

        console.print("\n[green]✓[/green] Infrastructure setup complete")
        console.print("  Run [bold]devflow infra up[/bold] to start Traefik when needed")
        return True

    except Exception as e:
        console.print(f"[yellow]○[/yellow] Infrastructure setup failed: {e}")
        console.print("  You can run [bold]devflow infra up[/bold] later to try again")
        return False


@app.command()
def install(
    skip_plugin: bool = typer.Option(False, "--skip-plugin", help="Skip Claude Code plugin installation"),
    skip_git: bool = typer.Option(False, "--skip-git", help="Skip git configuration"),
    skip_infra: bool = typer.Option(False, "--skip-infra", help="Skip infrastructure setup prompt"),
    non_interactive: bool = typer.Option(False, "--non-interactive", "-y", help="Run without prompts"),
    force: bool = typer.Option(False, "--force", "-f", help="Force reinstall even if already installed"),
) -> None:
    """
    First-time devflow setup.

    This wizard will:
    - Create ~/.devflow directory structure
    - Configure git settings (name, email, co-author)
    - Set up default preferences
    - Optionally set up shared infrastructure (Traefik, certificates)
    - Install the Claude Code plugin

    Run this once after installing devflow.
    """
    # Check if already initialized
    already_initialized = is_devflow_initialized()
    if already_initialized and not force:
        console.print("[green]✓[/green] Devflow is already set up!")
        console.print("  Use [bold]--force[/bold] to run setup again")
        console.print("\n[bold]Quick commands:[/bold]")
        console.print("  devflow status     - Check installation status")
        console.print("  devflow doctor     - Run diagnostics")
        console.print("  devflow init       - Initialize a new project")
        return

    console.print(
        Panel.fit(
            "[bold blue]Devflow Setup Wizard[/bold blue]\n" "Configure devflow for first-time use",
            border_style="blue",
        )
    )

    devflow_root = get_devflow_root()
    console.print(f"\nDevflow installation: [dim]{devflow_root}[/dim]")

    # Load or create global config
    config = load_global_config()

    # Step 1: Create directory structure
    console.print("\n[bold]Step 1: Directory Setup[/bold]")
    create_devflow_directories()

    # Step 2: Check prerequisites
    console.print("\n[bold]Step 2: Checking Prerequisites[/bold]")
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

    # Step 3: Git configuration
    if not skip_git and prereqs["required"]["git"]:
        console.print("\n[bold]Step 3: Git Configuration[/bold]")
        config = setup_git_config(config, interactive=not non_interactive)
    else:
        console.print("\n[bold]Step 3: Git Configuration[/bold]")
        if skip_git:
            console.print("[dim]○ Skipped (--skip-git)[/dim]")
        else:
            console.print("[yellow]○ Skipped (git not installed)[/yellow]")

    # Step 4: Default settings
    console.print("\n[bold]Step 4: Default Settings[/bold]")
    config = setup_defaults(config, interactive=not non_interactive)

    # Step 5: Infrastructure setup
    if not skip_infra:
        console.print("\n[bold]Step 5: Shared Infrastructure[/bold]")
        setup_infrastructure(prereqs, interactive=not non_interactive)
    else:
        console.print("\n[bold]Step 5: Shared Infrastructure[/bold]")
        console.print("[dim]○ Skipped (--skip-infra)[/dim]")

    # Step 6: Claude Code plugin
    console.print("\n[bold]Step 6: Claude Code Integration[/bold]")
    if not skip_plugin:
        if not prereqs["required"]["claude"]:
            console.print("[yellow]○ Skipping plugin install:[/yellow] Claude Code CLI not found")
            console.print("  Install Claude Code first: [link]https://claude.ai/code[/link]")
        else:
            if is_plugin_installed() and not force:
                console.print("[green]✓[/green] Claude Code plugin already installed")
            else:
                success = install_claude_plugin(devflow_root)
                if not success:
                    console.print("\n[yellow]You can install the plugin manually:[/yellow]")
                    console.print(f"  claude plugin install {devflow_root}")
    else:
        console.print("[dim]○ Skipped (--skip-plugin)[/dim]")

    # Save configuration
    config.setup_completed = True
    if save_global_config(config):
        console.print(f"\n[green]✓[/green] Saved configuration to {DEVFLOW_HOME / 'config.yml'}")
    else:
        console.print(f"\n[yellow]○[/yellow] Could not save configuration to {DEVFLOW_HOME / 'config.yml'}")

    # Summary and next steps
    console.print("\n" + "─" * 50)
    console.print("\n[bold green]Setup complete![/bold green]\n")

    console.print("[bold]Next steps:[/bold]")
    console.print("  1. Navigate to your project directory")
    console.print("  2. Run [bold]devflow init[/bold] to create project config")
    console.print("  3. Run [bold]devflow doctor[/bold] to verify setup")
    if not skip_infra:
        console.print("  4. Run [bold]devflow infra up[/bold] to start shared infrastructure")

    if prereqs["required"]["claude"]:
        console.print("\n[bold]Claude Code skills available:[/bold]")
        console.print("  /devflow:setup        - Initialize local environment")
        console.print("  /devflow:migrate      - Run database migrations")
        console.print("  /devflow:status       - Check project health")
        console.print("  /devflow:doctor       - Troubleshoot issues")


@app.command()
def uninstall(
    keep_config: bool = typer.Option(False, "--keep-config", help="Keep configuration files"),
) -> None:
    """
    Remove devflow Claude Code plugin.

    This only removes the Claude Code integration, not the CLI itself.
    """
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

    # Check global setup
    config = load_global_config()
    console.print("\n[bold]Setup completed:[/bold] ", end="")
    if config.setup_completed:
        console.print("[green]✓ Yes[/green]")
    else:
        console.print("[yellow]○ No[/yellow] - Run 'devflow install' to set up")

    console.print(f"\n[bold]Installation path:[/bold] {devflow_root}")
    console.print(f"[bold]Config directory:[/bold]  {DEVFLOW_HOME}")

    # Check global config
    config_path = DEVFLOW_HOME / "config.yml"
    console.print("\n[bold]Global config:[/bold] ", end="")
    if config_path.exists():
        console.print(f"[green]✓[/green] {config_path}")
        if config.git.user_name:
            console.print(f"  Git name:  {config.git.user_name}")
        if config.git.user_email:
            console.print(f"  Git email: {config.git.user_email}")
        if config.defaults.secrets_provider:
            console.print(f"  Secrets:   {config.defaults.secrets_provider}")
    else:
        console.print("[yellow]○ Not found[/yellow]")

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

    # Check infrastructure
    console.print("\n[bold]Infrastructure:[/bold]")
    certs_dir = DEVFLOW_HOME / "certs"
    cert_exists = (certs_dir / "cert.pem").exists() and (certs_dir / "key.pem").exists()
    console.print("  Certificates: ", end="")
    if cert_exists:
        console.print("[green]✓ Generated[/green]")
    else:
        console.print("[dim]○ Not generated[/dim]")

    # Check Docker network
    try:
        result = subprocess.run(
            ["docker", "network", "ls", "--filter", "name=devflow-proxy", "--format", "{{.Name}}"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        network_exists = "devflow-proxy" in result.stdout
        console.print("  Docker network: ", end="")
        if network_exists:
            console.print("[green]✓ devflow-proxy[/green]")
        else:
            console.print("[dim]○ Not created[/dim]")
    except (subprocess.TimeoutExpired, FileNotFoundError):
        console.print("  Docker network: [dim]○ Could not check[/dim]")
