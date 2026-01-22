"""Configuration management commands."""

import typer
from rich.console import Console
from rich.syntax import Syntax

app = typer.Typer(no_args_is_help=True)
console = Console()


@app.command()
def show(
    format: str = typer.Option("yaml", "--format", "-f", help="Output format (yaml, json)"),
) -> None:
    """Show current configuration."""
    from pathlib import Path

    from devflow.core.config import load_project_config

    config = load_project_config()
    if not config:
        console.print("[red]No devflow.yml found. Run 'devflow init' first.[/red]")
        raise typer.Exit(1)

    config_path = Path.cwd() / "devflow.yml"
    content = config_path.read_text()

    syntax = Syntax(content, "yaml", theme="monokai", line_numbers=True)
    console.print(syntax)


@app.command()
def validate() -> None:
    """Validate current configuration."""
    from pathlib import Path

    from devflow.core.config import validate_config

    config_path = Path.cwd() / "devflow.yml"
    if not config_path.exists():
        console.print("[red]No devflow.yml found. Run 'devflow init' first.[/red]")
        raise typer.Exit(1)

    errors = validate_config(config_path)

    if errors:
        console.print("[red]Configuration errors found:[/red]\n")
        for error in errors:
            console.print(f"  [red]{error}[/red]")
        raise typer.Exit(1)
    else:
        console.print("[green]Configuration is valid.[/green]")


@app.command()
def env(
    environment: str | None = typer.Argument(None, help="Environment to switch to"),
) -> None:
    """Show or switch the current environment."""
    from devflow.core.config import get_current_env, set_current_env

    if environment:
        set_current_env(environment)
        console.print(f"Switched to [bold]{environment}[/bold] environment.")
    else:
        current = get_current_env()
        console.print(f"Current environment: [bold]{current}[/bold]")


def _parse_value(value: str):
    """Parse a string value to the appropriate Python type."""
    import json as json_lib

    # Boolean
    if value.lower() == "true":
        return True
    if value.lower() == "false":
        return False

    # Integer
    try:
        return int(value)
    except ValueError:
        pass

    # Float
    try:
        return float(value)
    except ValueError:
        pass

    # JSON array or object
    if value.startswith("[") or value.startswith("{"):
        try:
            return json_lib.loads(value)
        except json_lib.JSONDecodeError:
            pass

    # String (default)
    return value


def _set_nested_value(data: dict, keys: list[str], value) -> None:
    """Set a value in a nested dictionary using a list of keys."""
    for key in keys[:-1]:
        if key not in data:
            data[key] = {}
        data = data[key]
    data[keys[-1]] = value


def _get_nested_value(data: dict, keys: list[str]):
    """Get a value from a nested dictionary using a list of keys."""
    for key in keys:
        if not isinstance(data, dict) or key not in data:
            return None
        data = data[key]
    return data


@app.command("set")
def set_value(
    key: str = typer.Argument(..., help="Configuration key (e.g., 'database.migrations.directory')"),
    value: str = typer.Argument(..., help="Value to set"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Set a configuration value."""
    import json as json_lib
    from pathlib import Path

    import yaml

    from devflow.core.config import validate_config

    config_path = Path.cwd() / "devflow.yml"
    if not config_path.exists():
        if json_output:
            print(json_lib.dumps({"success": False, "error": "No devflow.yml found"}))
        else:
            console.print("[red]No devflow.yml found. Run 'devflow init' first.[/red]")
        raise typer.Exit(1)

    # Load raw YAML to preserve structure/comments
    with open(config_path) as f:
        raw_config = yaml.safe_load(f)

    # Parse the key path
    keys = key.split(".")
    if not keys:
        if json_output:
            print(json_lib.dumps({"success": False, "error": "Invalid key"}))
        else:
            console.print("[red]Invalid key.[/red]")
        raise typer.Exit(1)

    # Get the old value for reporting
    old_value = _get_nested_value(raw_config, keys)

    # Parse the new value
    parsed_value = _parse_value(value)

    # Set the new value
    _set_nested_value(raw_config, keys, parsed_value)

    # Write back to file
    with open(config_path, "w") as f:
        yaml.dump(raw_config, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

    # Validate the updated config
    errors = validate_config(config_path)
    if errors:
        if json_output:
            print(
                json_lib.dumps(
                    {
                        "success": False,
                        "error": "Configuration validation failed",
                        "validation_errors": errors,
                    }
                )
            )
        else:
            console.print("[red]Configuration validation failed:[/red]")
            for error in errors:
                console.print(f"  {error}")
            console.print("\n[yellow]The configuration was saved but may be invalid.[/yellow]")
        raise typer.Exit(1)

    if json_output:
        print(
            json_lib.dumps(
                {
                    "success": True,
                    "key": key,
                    "old_value": old_value,
                    "new_value": parsed_value,
                }
            )
        )
    else:
        console.print(f"[green]Updated:[/green] {key}")
        console.print(f"  Old: {old_value}")
        console.print(f"  New: {parsed_value}")
