import datetime
import logging
import typer

import enums

LOG_COLORS = {
    logging.DEBUG: typer.colors.BRIGHT_BLACK,
    logging.INFO: typer.colors.WHITE,
    logging.WARNING: typer.colors.YELLOW,
    logging.ERROR: typer.colors.RED,
    logging.CRITICAL: typer.colors.RED,
}

STATUS_COLORS = {
    enums.TaskStatus.SUCCEEDED: typer.colors.GREEN,
    enums.TaskStatus.SUCCEEDED_WITH_WARNINGS: typer.colors.YELLOW,
    enums.TaskStatus.RUNNING: typer.colors.CYAN,
    enums.TaskStatus.FAILED: typer.colors.RED,
    enums.TaskStatus.RETRYING: typer.colors.BRIGHT_MAGENTA,
    enums.TaskStatus.QUEUED: typer.colors.BRIGHT_BLACK,
    enums.TaskStatus.INITIALIZING: typer.colors.BRIGHT_BLACK,
    enums.TaskStatus.WAITING: typer.colors.BRIGHT_BLACK,
    enums.TaskStatus.UP_NEXT: typer.colors.BRIGHT_BLACK,
}

STATUS_ICONS = {
    enums.TaskStatus.SUCCEEDED: "✔",
    enums.TaskStatus.SUCCEEDED_WITH_WARNINGS: "⚠",
    enums.TaskStatus.FAILED: "✖",
    enums.TaskStatus.RUNNING: "▶",
    enums.TaskStatus.RETRYING: "↻",
}


def _log_handler(task, record, _formatted):
    timestamp = datetime.datetime.fromtimestamp(record.created).strftime("%H:%M:%S")
    color = LOG_COLORS.get(record.levelno, typer.colors.WHITE)
    message = record.getMessage()
    typer.secho(f"{timestamp} [{record.levelname:<8}] {task.name}: {message}", fg=color)


def _print_summary(orchestrator) -> None:
    typer.secho("\nTask summary:", fg=typer.colors.BRIGHT_BLACK, bold=True)
    for task in orchestrator.tasks:
        status = task.status.name.replace("_", " ").title()
        color = STATUS_COLORS.get(task.status, typer.colors.WHITE)
        icon = STATUS_ICONS.get(task.status, "•")
        typer.secho(f"  {icon} {task.name} — {status}", fg=color)
    typer.echo()


def run_orchestrator_console(orchestrator, label: str) -> None:
    success = orchestrator.run_cli(log_handler=_log_handler)
    _print_summary(orchestrator)
    if not success:
        typer.secho(f"✖ {label} failed", fg=typer.colors.RED, bold=True)
        raise typer.Exit(code=1)
    typer.secho(f"✔ {label} completed", fg=typer.colors.GREEN, bold=True)
