"""Console output utilities using Rich."""

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

# Global console instance
console = Console()


def create_table(title: str, columns: list[tuple[str, str]]) -> Table:
    """
    Create a Rich table with common styling.

    Args:
        title: Table title
        columns: List of (name, style) tuples

    Returns:
        Configured Table instance
    """
    table = Table(title=title)
    for name, style in columns:
        table.add_column(name, style=style)
    return table


def create_spinner(text: str = "Working...") -> Progress:
    """Create a spinner progress indicator."""
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    )


def print_success(message: str) -> None:
    """Print a success message."""
    console.print(f"[green]{message}[/green]")


def print_error(message: str) -> None:
    """Print an error message."""
    console.print(f"[red]Error: {message}[/red]")


def print_warning(message: str) -> None:
    """Print a warning message."""
    console.print(f"[yellow]Warning: {message}[/yellow]")


def print_info(message: str) -> None:
    """Print an info message."""
    console.print(f"[blue]{message}[/blue]")
