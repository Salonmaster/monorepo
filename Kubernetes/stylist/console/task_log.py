import core
import logging
import datetime
from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import DataTable
from textual.widgets.data_table import RowKey, ColumnKey

class TaskLog(Widget):
    column_keys: dict[str, ColumnKey] = {}
    task_rows: dict[str, RowKey] = {}
    _sort_reverse: dict[ColumnKey, bool] = {}
    _sort_key: ColumnKey | None = None

    LOG_COLORS = {
        1: "red",
        2: "yellow",
        3: "green",
    }

    def __init__(self):
        super().__init__()
        self.id="bottom-right"
        self.border_title = "Task log"

    def compose(self) -> ComposeResult:
        yield DataTable()

    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.cursor_type = "none"
        self.column_keys = {
            "Time": table.add_column("Time"),
            "Level": table.add_column("Level"),
            "Message": table.add_column("Message"),
        }
        self.set_interval(0.5, self.update_table)


    def update_table(self) -> None:
        table = self.query_one(DataTable)
        table.clear()
        t = core.Backbone().context.selected_task
        if not t:
            return

        for log_message in t.log_recorder.get_all(reverse=True):
            log_message: logging.LogRecord = log_message

            table.add_row(datetime.datetime.fromtimestamp(log_message.created).strftime("%H:%M:%S.%f")[:-4], log_message.levelname, log_message.msg)

    def format_elapsed(self, delta: datetime.timedelta | None) -> str:
        """Format a timedelta as HH:MM:SS.d (tenths of a second)."""
        if not delta:
            return "N/A"

        total_seconds = delta.total_seconds()
        hours, rem = divmod(total_seconds, 3600)
        minutes, seconds = divmod(rem, 60)

        # Seconds with tenths (1 decimal place)
        return f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"
