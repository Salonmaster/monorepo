from __future__ import annotations

import datetime
from typing import Dict

import core
from rich.text import Text
from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import DataTable
from textual.widgets.data_table import RowKey, ColumnKey

from enums import TaskStatus, TaskStatusStyles  # assuming Enum-like
from models import Task       # or wherever your Task dataclass lives


class TaskDetail(Widget):
    """Shows live details of a single Task in a key/value table."""


    _col_keys: Dict[str, ColumnKey]
    _row_keys: Dict[str, RowKey]
    orchestrator: core.TaskOrchestrator

    def __init__(self, orchestrator: core.TaskOrchestrator, refresh_hz: float = 5.0) -> None:
        """
        :param task: The Task instance to display.
        :param refresh_hz: How often to refresh per second (default 5 Hz).
        """
        super().__init__()
        self.id="top-right"
        self.border_title = "Task Details"
        self.orchestrator = orchestrator
        self._refresh_interval = 1.0 / max(refresh_hz, 0.1)

    def compose(self) -> ComposeResult:
        table = DataTable(zebra_stripes=True, classes="row")
        table.cursor_type = "none"
        table.show_header = False
        yield table

    def on_mount(self) -> None:
        table = self._table
        # columns: Field | Value
        self._col_keys = {
            "field": table.add_column("Field", width=18),
            "value": table.add_column("Value"),
        }

        # Pre-create rows we will update in-place
        self._row_keys = {
            "name":        table.add_row(Text("Name", style="bold"), ""),
            "status":      table.add_row(Text("Status", style="bold"), ""),
            "uuid":        table.add_row(Text("UUID", style="bold"), ""),
            "delay":       table.add_row(Text("Delay", style="bold"), ""),
            "backoff":     table.add_row(Text("Backoff", style="bold"), ""),
            "started":     table.add_row(Text("Started", style="bold"), ""),
            "attempts":    table.add_row(Text("Attempts", style="bold"), ""),
            "finished":    table.add_row(Text("Finished", style="bold"), ""),
            "elapsed":     table.add_row(Text("Elapsed", style="bold"), ""),
            "depends_on":  table.add_row(Text("Dependencies", style="bold"), ""),
        }

        self._push_all()
        # periodic refresh
        self.set_interval(self._refresh_interval, self._tick)

    # ---------- helpers ----------

    @property
    def _table(self) -> DataTable:
        return self.query_one(DataTable)



    def _tick(self) -> None:
        """Periodic updater; keeps values in sync without reallocating rows."""
        t = core.Backbone().context.selected_task
        if not t:
            return
        table = self._table

        # status with style
        status_text = self._styled_status(t.status)

        # elapsed depends on started/finished
        elapsed_text = self._format_elapsed(t.started, t.finished)

        # dependencies string
        orchestrator = self.orchestrator
        depending_tasks = [task for task in orchestrator.tasks if next((dep for dep in t.dependencies if isinstance(task, dep)), None)]

        if len(depending_tasks) > 0:
            deps = ", ".join([f"{task.name}([{TaskStatusStyles.get(task.status, 'white')}]{task.status.value}[/])" for task in depending_tasks])
        else:
            deps = "—"

        def set_row(key: str, value) -> None:
            table.update_cell(self._row_keys[key], self._col_keys["value"], value, update_width=True)

        set_row("name", t.name)
        set_row("status", status_text)
        set_row("uuid", t.uuid)
        set_row("delay", f"{t.delay}s")
        set_row("backoff", f"{t.backoff}s")
        set_row("started", self._fmt_dt(t.started))
        set_row("attempts", f"{t.current_attempt}/{t.retries}")
        set_row("finished", self._fmt_dt(t.finished))
        set_row("elapsed", elapsed_text)
        set_row("depends_on", deps)

    def _push_all(self) -> None:
        """Initial fill (same as tick but does all fields once)."""
        self._tick()

    @staticmethod
    def _fmt_dt(dt: datetime.datetime | None) -> str:
        if not dt:
            return "—"
        # show local time HH:MM:SS, and date if not today
        now = datetime.datetime.now(dt.tzinfo) if dt.tzinfo else datetime.datetime.now()
        same_day = (dt.date() == now.date())
        return dt.strftime("%H:%M:%S") if same_day else dt.strftime("%Y-%m-%d %H:%M:%S")

    @staticmethod
    def _format_elapsed(started: datetime.datetime | None,
                        finished: datetime.datetime | None) -> str:
        if not started:
            return "—"
        end = finished or datetime.datetime.now(started.tzinfo) if started and started.tzinfo else (
            finished or datetime.datetime.now()
        )
        delta = end - started
        # Compact pretty duration (H:MM:SS.mmm when < 1 day, else Dd HH:MM:SS)
        total_ms = int(delta.total_seconds() * 1000)
        if total_ms < 0:
            return "—"
        seconds, ms = divmod(total_ms, 1000)
        mins, sec = divmod(seconds, 60)
        hrs, min_ = divmod(mins, 60)
        days, hr_ = divmod(hrs, 24)
        if days:
            return f"{days}d {hr_:02}:{min_:02}:{sec:02}"
        if hrs:
            return f"{hr_:d}:{min_:02}:{sec:02}"
        # show milliseconds only when < 1 minute for extra feedback
        if mins == 0:
            return f"{sec}.{ms:03}s"
        return f"{min_:02}:{sec:02}"

    def _styled_status(self, status: TaskStatus | str) -> Text:
        style = TaskStatusStyles.get(status, "white")
        return Text(status.value, style=style)

    # ---------- public API ----------

    def set_task(self, task: Task) -> None:
        """Swap the displayed task at runtime."""
        self.task = task
        self._push_all()
