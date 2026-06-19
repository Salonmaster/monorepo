import core
import enums
import datetime
from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import DataTable
from textual.widgets.data_table import RowKey, ColumnKey
from rich.text import Text

class TaskList(Widget):
    column_keys: dict[str, ColumnKey] = {}
    task_rows: dict[str, RowKey] = {}
    _sort_reverse: dict[ColumnKey, bool] = {}
    _sort_key: ColumnKey | None = None

    def __init__(self, orchestrator: core.TaskOrchestrator):
        super().__init__()
        self.id = "left-pane"
        self.orchestrator = orchestrator
        self.border_title = "Task List"

    def compose(self) -> ComposeResult:
        yield DataTable()

    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.cursor_type = "row"
        self.column_keys = {
            "Task name": table.add_column("Task name"),
            "Status": table.add_column("Status"),
            "Elapsed": table.add_column("Elapsed"),
            "Message": table.add_column("Message"),
        }
        self.set_interval(0.5, self.update_table)
        for task in self.orchestrator.tasks:
            self.task_rows[task.uuid] = table.add_row(task.name)

    def on_data_table_header_selected(self, event: DataTable.HeaderSelected) -> None:
        self._sort_key = event.column_key

        # Toggle sort direction
        reverse = getattr(self, "_sort_reverse", False)

        self._sort_reverse = not reverse

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        table = event.data_table
        row_key = event.row_key
        if row_key:
            core.Backbone().context.selected_task = self.orchestrator.tasks[table.get_row_index(row_key)]

    def update_table(self) -> None:
        table = self.query_one(DataTable)

        for task in self.orchestrator.tasks:
            row_key = self.task_rows[task.uuid]


            match task.status:
                case enums.TaskStatus.RUNNING:
                    elapsed_time = self.format_elapsed(datetime.datetime.now() - task.started)
                case enums.TaskStatus.SUCCEEDED | enums.TaskStatus.SUCCEEDED_WITH_WARNINGS | enums.TaskStatus.FAILED:
                    elapsed_time = self.format_elapsed(task.finished - task.started)
                case enums.TaskStatus.QUEUED:
                    elapsed_time = f"{self.format_elapsed(datetime.timedelta(seconds=task.delay))}-"
                case enums.TaskStatus.RETRYING:
                    elapsed_time = f"{self.format_elapsed(datetime.timedelta(seconds=task.backoff))}-"
                case _:
                    elapsed_time = "N/A"
            if (last_log := task.log_recorder.get_last(False)) is None:
                formatted_task_message = "No logs"
            else:
                formatted_task_message = last_log.msg
            table.update_cell(row_key, self.column_keys["Status"], Text(task.status, style=enums.TaskStatusStyles.get(task.status, "white")), update_width=True)
            table.update_cell(row_key, self.column_keys["Elapsed"], Text(elapsed_time), update_width=True)
            table.update_cell(row_key, self.column_keys["Message"], Text(formatted_task_message, justify="fill"), update_width=True)
        if self._sort_key:
            table.sort(self._sort_key, reverse=self._sort_reverse, key=lambda row: row if isinstance(row, str) else row.plain)

    def format_elapsed(self, delta: datetime.timedelta | None) -> str:
        """Format a timedelta as HH:MM:SS.d (tenths of a second)."""
        if delta is None:
            return "N/A"

        total_seconds = delta.total_seconds()
        hours, rem = divmod(total_seconds, 3600)
        minutes, seconds = divmod(rem, 60)

        # Seconds with tenths (1 decimal place)
        return f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"
