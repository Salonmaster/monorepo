import typer
def print_boxed(message: str, color = typer.colors.GREEN) -> None:
    """
    Print a success message to the console.
    """
    lines = message.splitlines()
    width = max(len(line) for line in lines)
    border = "+" + "-" * (width + 2) + "+"

    typer.secho(border, fg=color)
    for line in lines:
        typer.secho(f"| {line.ljust(width)} |", fg=color)
    typer.secho(border, fg=color)

def print_separator(message: str, color = typer.colors.BLUE) -> None:
    """
    Print a separator line to the console.
    """
    typer.secho(f"\n{message}", fg=color, bold=True)
