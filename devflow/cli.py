"""Main CLI application using Typer."""

import typer
from rich.console import Console

from devflow import __version__
from devflow.commands import config, db, deploy, dev, doctor, secrets

app = typer.Typer(
    name="devflow",
    help="Developer workflow CLI for AOCyber ecosystem",
    no_args_is_help=True,
    rich_markup_mode="rich",
)

console = Console()

# Register command groups
app.add_typer(db.app, name="db", help="Database and migration operations")
app.add_typer(secrets.app, name="secrets", help="Secrets management")
app.add_typer(deploy.app, name="deploy", help="Deployment operations")
app.add_typer(dev.app, name="dev", help="Local development commands")
app.add_typer(config.app, name="config", help="Configuration management")


@app.command()
def init(
    preset: str = typer.Option(None, "--preset", "-p", help="Use a built-in preset (aocodex, aosentry)"),
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite existing configuration"),
) -> None:
    """Initialize devflow in the current project."""
    from devflow.core.config import initialize_project

    initialize_project(preset=preset, force=force)


@app.command()
def version() -> None:
    """Show devflow version."""
    console.print(f"devflow version {__version__}")


# Register doctor command at root level
app.command(name="doctor")(doctor.doctor)


@app.callback()
def main(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output"),
) -> None:
    """Devflow - Developer workflow CLI for AOCyber ecosystem."""
    if verbose:
        import logging

        logging.basicConfig(level=logging.DEBUG)


if __name__ == "__main__":
    app()
