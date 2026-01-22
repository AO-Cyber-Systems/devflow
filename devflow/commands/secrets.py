"""Secrets management commands."""

import json
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(no_args_is_help=True)
console = Console()


def _get_repo_name() -> str | None:
    """Get the GitHub repository name from git remote."""
    import subprocess

    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            url = result.stdout.strip()
            # Parse git@github.com:org/repo.git or https://github.com/org/repo.git
            if url.startswith("git@"):
                # git@github.com:org/repo.git
                return url.split(":")[-1].replace(".git", "")
            elif "github.com" in url:
                # https://github.com/org/repo.git
                parts = url.split("github.com/")[-1].replace(".git", "")
                return parts
    except Exception:
        pass
    return None


@app.command("list")
def list_secrets(
    env: str = typer.Option("staging", "--env", "-e", help="Environment (staging, production)"),
    source: str = typer.Option("1password", "--source", "-s", help="Secret source (1password, github, docker)"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """List secrets for the specified environment."""
    from devflow.core.config import load_project_config
    from devflow.providers.docker import DockerProvider
    from devflow.providers.github import GitHubProvider
    from devflow.providers.onepassword import OnePasswordProvider

    config = load_project_config()
    if not config:
        if json_output:
            print(json.dumps({"success": False, "error": "No devflow.yml found"}))
        else:
            console.print("[red]No devflow.yml found. Run 'devflow init' first.[/red]")
        raise typer.Exit(1)

    secrets_list = []

    if source == "1password":
        op = OnePasswordProvider()
        if not op.is_authenticated():
            if json_output:
                print(json.dumps({"success": False, "error": "1Password not authenticated"}))
            else:
                console.print("[red]1Password not authenticated. Run 'op signin' first.[/red]")
            raise typer.Exit(1)

        vault = config.secrets.vault
        items = op.list_items(vault)

        for item in items:
            secrets_list.append(
                {
                    "name": item.get("title", ""),
                    "id": item.get("id", ""),
                    "category": item.get("category", ""),
                    "vault": vault,
                }
            )

    elif source == "github":
        gh = GitHubProvider()
        if not gh.is_authenticated():
            if json_output:
                print(json.dumps({"success": False, "error": "GitHub not authenticated"}))
            else:
                console.print("[red]GitHub not authenticated. Run 'gh auth login' first.[/red]")
            raise typer.Exit(1)

        repo = _get_repo_name()
        if not repo:
            if json_output:
                print(json.dumps({"success": False, "error": "Could not determine repository"}))
            else:
                console.print("[red]Could not determine repository from git remote.[/red]")
            raise typer.Exit(1)

        secret_names = gh.list_secrets(repo)
        for name in secret_names:
            secrets_list.append(
                {
                    "name": name,
                    "repo": repo,
                }
            )

    elif source == "docker":
        docker = DockerProvider()
        if not docker.is_authenticated():
            if json_output:
                print(json.dumps({"success": False, "error": "Docker not running"}))
            else:
                console.print("[red]Docker daemon not running.[/red]")
            raise typer.Exit(1)

        docker_secrets = docker.list_secrets()
        for secret in docker_secrets:
            secrets_list.append(
                {
                    "name": secret.get("Name", ""),
                    "id": secret.get("ID", ""),
                    "created": secret.get("CreatedAt", ""),
                }
            )

    else:
        if json_output:
            print(json.dumps({"success": False, "error": f"Unknown source: {source}"}))
        else:
            console.print(f"[red]Unknown source: {source}[/red]")
        raise typer.Exit(1)

    # Cross-reference with config mappings if available
    mappings = {m.name: m for m in config.secrets.mappings}

    if json_output:
        print(
            json.dumps(
                {
                    "success": True,
                    "environment": env,
                    "source": source,
                    "secrets": secrets_list,
                    "mapped_count": len([s for s in secrets_list if s["name"] in mappings]),
                }
            )
        )
    else:
        console.print(f"[bold]Secrets for {env}[/bold] (source: {source})\n")

        if not secrets_list:
            console.print("[yellow]No secrets found.[/yellow]")
            return

        table = Table(show_header=True)
        table.add_column("Name")
        if source == "1password":
            table.add_column("Category")
            table.add_column("Mapped")
        elif source == "github":
            table.add_column("Mapped")
        elif source == "docker":
            table.add_column("ID")
            table.add_column("Mapped")

        for secret in secrets_list:
            name = secret.get("name", "")
            is_mapped = "[green]Yes[/green]" if name in mappings else "[dim]No[/dim]"

            if source == "1password":
                table.add_row(name, secret.get("category", ""), is_mapped)
            elif source == "github":
                table.add_row(name, is_mapped)
            elif source == "docker":
                table.add_row(name, secret.get("id", "")[:12], is_mapped)

        console.print(table)
        console.print(f"\n[dim]Total: {len(secrets_list)} secrets[/dim]")


@app.command()
def sync(
    from_source: str = typer.Option("1password", "--from", help="Source (1password, env)"),
    to_target: str = typer.Option("github", "--to", help="Target (github, docker)"),
    env: str = typer.Option("staging", "--env", "-e", help="Environment"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would be synced"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Sync secrets from source to target."""
    from devflow.core.config import load_project_config
    from devflow.providers.docker import DockerProvider
    from devflow.providers.github import GitHubProvider
    from devflow.providers.onepassword import OnePasswordProvider

    config = load_project_config()
    if not config:
        if json_output:
            print(json.dumps({"success": False, "error": "No devflow.yml found"}))
        else:
            console.print("[red]No devflow.yml found. Run 'devflow init' first.[/red]")
        raise typer.Exit(1)

    if not json_output:
        console.print(f"[bold]Syncing secrets: {from_source} -> {to_target}[/bold] ({env})\n")
        if dry_run:
            console.print("[dim]Dry run - no changes will be made[/dim]\n")

    mappings = config.secrets.mappings
    if not mappings:
        if json_output:
            print(json.dumps({"success": True, "synced": 0, "message": "No mappings configured"}))
        else:
            console.print("[yellow]No secret mappings configured in devflow.yml[/yellow]")
        return

    # Initialize providers
    op = None
    gh = None
    docker = None
    repo: str | None = None

    if from_source == "1password":
        op = OnePasswordProvider()
        if not op.is_authenticated():
            if json_output:
                print(json.dumps({"success": False, "error": "1Password not authenticated"}))
            else:
                console.print("[red]1Password not authenticated. Run 'op signin' first.[/red]")
            raise typer.Exit(1)

    if to_target == "github":
        gh = GitHubProvider()
        if not gh.is_authenticated():
            if json_output:
                print(json.dumps({"success": False, "error": "GitHub not authenticated"}))
            else:
                console.print("[red]GitHub not authenticated. Run 'gh auth login' first.[/red]")
            raise typer.Exit(1)
        repo = _get_repo_name()
        if not repo:
            if json_output:
                print(json.dumps({"success": False, "error": "Could not determine repository"}))
            else:
                console.print("[red]Could not determine repository from git remote.[/red]")
            raise typer.Exit(1)
    elif to_target == "docker":
        docker = DockerProvider()
        if not docker.is_authenticated():
            if json_output:
                print(json.dumps({"success": False, "error": "Docker not running"}))
            else:
                console.print("[red]Docker daemon not running.[/red]")
            raise typer.Exit(1)

    vault = config.secrets.vault
    synced = 0
    failed = 0
    results = []

    for mapping in mappings:
        result = {"name": mapping.name, "status": "skipped"}

        # Read from source
        value = None
        if from_source == "1password" and mapping.op_item and mapping.op_field:
            assert op is not None  # Validated above
            value = op.read_field(mapping.op_item, mapping.op_field, vault)
            if not value:
                result["status"] = "error"
                result["error"] = "Could not read from 1Password"
                failed += 1
                results.append(result)
                continue

        if not value:
            result["status"] = "skipped"
            result["reason"] = "No source configured"
            results.append(result)
            continue

        # Write to target
        if to_target == "github" and mapping.github_secret:
            assert gh is not None  # Validated above
            assert repo is not None  # Validated above
            if dry_run:
                result["status"] = "would_sync"
                result["target"] = mapping.github_secret
            else:
                success = gh.set_secret(repo, mapping.github_secret, value)
                if success:
                    result["status"] = "synced"
                    result["target"] = mapping.github_secret
                    synced += 1
                else:
                    result["status"] = "error"
                    result["error"] = "Failed to set GitHub secret"
                    failed += 1

        elif to_target == "docker" and mapping.docker_secret:
            assert docker is not None  # Validated above
            if dry_run:
                result["status"] = "would_sync"
                result["target"] = mapping.docker_secret
            else:
                # Remove existing secret first (Docker secrets are immutable)
                docker.remove_secret(mapping.docker_secret)
                success = docker.create_secret(mapping.docker_secret, value)
                if success:
                    result["status"] = "synced"
                    result["target"] = mapping.docker_secret
                    synced += 1
                else:
                    result["status"] = "error"
                    result["error"] = "Failed to create Docker secret"
                    failed += 1
        else:
            result["status"] = "skipped"
            result["reason"] = f"No {to_target} target configured"

        results.append(result)

    if json_output:
        print(
            json.dumps(
                {
                    "success": failed == 0,
                    "dry_run": dry_run,
                    "synced": synced,
                    "failed": failed,
                    "results": results,
                }
            )
        )
    else:
        table = Table(show_header=True)
        table.add_column("Secret")
        table.add_column("Status")
        table.add_column("Target")

        for r in results:
            status_color = {
                "synced": "green",
                "would_sync": "cyan",
                "error": "red",
                "skipped": "dim",
            }.get(r["status"], "white")

            status_display = f"[{status_color}]{r['status']}[/{status_color}]"
            target = r.get("target", r.get("reason", r.get("error", "-")))
            table.add_row(r["name"], status_display, target)

        console.print(table)
        console.print(f"\n[dim]Synced: {synced}, Failed: {failed}[/dim]")


@app.command()
def verify(
    env: str = typer.Option("staging", "--env", "-e", help="Environment to verify"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Verify secrets are in sync across all systems."""
    from devflow.core.config import load_project_config
    from devflow.providers.docker import DockerProvider
    from devflow.providers.github import GitHubProvider
    from devflow.providers.onepassword import OnePasswordProvider

    config = load_project_config()
    if not config:
        if json_output:
            print(json.dumps({"success": False, "error": "No devflow.yml found"}))
        else:
            console.print("[red]No devflow.yml found. Run 'devflow init' first.[/red]")
        raise typer.Exit(1)

    if not json_output:
        console.print(f"[bold]Verifying secrets for {env}[/bold]\n")

    mappings = config.secrets.mappings
    if not mappings:
        if json_output:
            print(json.dumps({"success": True, "verified": 0, "message": "No mappings configured"}))
        else:
            console.print("[yellow]No secret mappings configured in devflow.yml[/yellow]")
        return

    # Initialize providers
    op = OnePasswordProvider()
    gh = GitHubProvider()
    docker = DockerProvider()

    vault = config.secrets.vault
    repo = _get_repo_name()

    # Get existing secrets from each source
    github_secrets = set(gh.list_secrets(repo)) if gh.is_authenticated() and repo else set()
    docker_secrets = {s.get("Name") for s in docker.list_secrets()} if docker.is_authenticated() else set()

    results = []
    in_sync = 0
    out_of_sync = 0

    for mapping in mappings:
        result = {
            "name": mapping.name,
            "op": False,
            "github": None,
            "docker": None,
        }

        # Check 1Password
        if mapping.op_item and mapping.op_field and op.is_authenticated():
            value = op.read_field(mapping.op_item, mapping.op_field, vault)
            result["op"] = value is not None

        # Check GitHub
        if mapping.github_secret:
            result["github"] = mapping.github_secret in github_secrets

        # Check Docker
        if mapping.docker_secret:
            result["docker"] = mapping.docker_secret in docker_secrets

        # Determine sync status
        checks = [v for v in [result["op"], result["github"], result["docker"]] if v is not None]
        if checks and all(checks):
            result["status"] = "in_sync"
            in_sync += 1
        elif any(checks):
            result["status"] = "partial"
            out_of_sync += 1
        else:
            result["status"] = "missing"
            out_of_sync += 1

        results.append(result)

    if json_output:
        print(
            json.dumps(
                {
                    "success": out_of_sync == 0,
                    "environment": env,
                    "in_sync": in_sync,
                    "out_of_sync": out_of_sync,
                    "results": results,
                }
            )
        )
    else:
        table = Table(show_header=True)
        table.add_column("Secret")
        table.add_column("1Password")
        table.add_column("GitHub")
        table.add_column("Docker")
        table.add_column("Status")

        def _status_icon(val: bool | None) -> str:
            if val is None:
                return "[dim]-[/dim]"
            return "[green]Yes[/green]" if val else "[red]No[/red]"

        for r in results:
            status = str(r.get("status", ""))
            status_color = {
                "in_sync": "green",
                "partial": "yellow",
                "missing": "red",
            }.get(status, "white")

            table.add_row(
                str(r.get("name", "")),
                _status_icon(r.get("op")),  # type: ignore[arg-type]
                _status_icon(r.get("github")),  # type: ignore[arg-type]
                _status_icon(r.get("docker")),  # type: ignore[arg-type]
                f"[{status_color}]{status}[/{status_color}]",
            )

        console.print(table)

        if out_of_sync > 0:
            console.print(f"\n[yellow]Warning: {out_of_sync} secret(s) out of sync[/yellow]")
            console.print("Run 'devflow secrets sync' to synchronize.")
        else:
            console.print(f"\n[green]All {in_sync} secrets are in sync.[/green]")


@app.command()
def export(
    env: str = typer.Option("local", "--env", "-e", help="Environment"),
    output: str = typer.Option("-", "--output", "-o", help="Output file (- for stdout)"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Export secrets to .env format (development only)."""
    if env not in ("local", "development"):
        if json_output:
            print(json.dumps({"success": False, "error": "Export only allowed for local/development"}))
        else:
            console.print("[red]Export is only allowed for local/development environments.[/red]")
            console.print("Use 'devflow secrets sync' for staging/production.")
        raise typer.Exit(1)

    from devflow.core.config import load_project_config
    from devflow.providers.onepassword import OnePasswordProvider

    config = load_project_config()
    if not config:
        if json_output:
            print(json.dumps({"success": False, "error": "No devflow.yml found"}))
        else:
            console.print("[red]No devflow.yml found. Run 'devflow init' first.[/red]")
        raise typer.Exit(1)

    if not json_output and output != "-":
        console.print(f"[bold]Exporting secrets for {env}[/bold]\n")

    mappings = config.secrets.mappings
    if not mappings:
        if json_output:
            print(json.dumps({"success": True, "exported": 0, "message": "No mappings configured"}))
        else:
            console.print("[yellow]No secret mappings configured in devflow.yml[/yellow]")
        return

    op = OnePasswordProvider()
    if not op.is_authenticated():
        if json_output:
            print(json.dumps({"success": False, "error": "1Password not authenticated"}))
        else:
            console.print("[red]1Password not authenticated. Run 'op signin' first.[/red]")
        raise typer.Exit(1)

    vault = config.secrets.vault
    env_lines = []
    exported = 0
    failed = 0

    for mapping in mappings:
        if not mapping.op_item or not mapping.op_field:
            continue

        value = op.read_field(mapping.op_item, mapping.op_field, vault)
        if value:
            # Use uppercase name for env var
            env_name = mapping.name.upper().replace("-", "_").replace(".", "_")
            # Escape quotes in value
            escaped_value = value.replace('"', '\\"')
            env_lines.append(f'{env_name}="{escaped_value}"')
            exported += 1
        else:
            failed += 1
            if not json_output and output != "-":
                console.print(f"[yellow]Warning: Could not read {mapping.name}[/yellow]")

    env_content = "\n".join(env_lines) + "\n" if env_lines else ""

    if json_output:
        print(
            json.dumps(
                {
                    "success": failed == 0,
                    "exported": exported,
                    "failed": failed,
                    "content": env_content if output == "-" else None,
                    "file": output if output != "-" else None,
                }
            )
        )
    elif output == "-":
        # Output to stdout
        console.print(env_content, end="")
    else:
        # Write to file
        output_path = Path(output)
        output_path.write_text(env_content)
        console.print(f"[green]Exported {exported} secrets to {output}[/green]")

        if failed > 0:
            console.print(f"[yellow]Warning: {failed} secret(s) could not be read[/yellow]")
