from __future__ import annotations

import datetime
from typing import Dict

import core
import pyperclip
from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import DataTable
from textual.widgets.data_table import ColumnKey



class CredentialDetail(Widget):
    """Shows live details of a single Credential in a key/value table."""

    _selected_credential_uuid: str | None = None
    _col_keys: Dict[str, ColumnKey]

    def __init__(self, refresh_hz: float = 5.0) -> None:
        """
        :param task: The Task instance to display.
        :param refresh_hz: How often to refresh per second (default 5 Hz).
        """
        super().__init__()
        self.id="top-right"
        self.border_title = "Credential Details (click to copy)"
        self._refresh_interval = 1.0 / max(refresh_hz, 0.1)

    def compose(self) -> ComposeResult:
        table = DataTable(zebra_stripes=True, classes="row")
        table.cursor_type = "cell"
        table.show_header = False
        yield table

    def on_mount(self) -> None:
        table = self._table
        # columns: Field | Value
        self._col_keys = {
            "field": table.add_column("Field", width=18),
            "value": table.add_column("Value"),
        }

        # periodic refresh
        self.set_interval(self._refresh_interval, self._tick)

    # ---------- helpers ----------

    def on_data_table_cell_selected(self, event: DataTable.CellSelected) -> None:
        pyperclip.copy(event.value)
        self.notify(f"Copied to clipboard: {event.value}")

    @property
    def _table(self) -> DataTable:
        return self.query_one(DataTable)

    def _tick(self) -> None:
        if not core.Backbone().context.selected_credential:
            return
        if self._selected_credential_uuid != core.Backbone().context.selected_credential.uuid:
            credential = core.Backbone().context.selected_credential
            self._selected_credential_uuid = credential.uuid
            self.update()

    def update(self) -> None:
        """Periodic updater; keeps values in sync without reallocating rows."""
        credential = core.Backbone().context.selected_credential

        table = self._table
        table.clear()

        table.add_row("name", credential.name)
        for key, value in credential.fields.items():
            table.add_row(key, value)


    @staticmethod
    def _fmt_dt(dt: datetime.datetime | None) -> str:
        if not dt:
            return "—"
        # show local time HH:MM:SS, and date if not today
        now = datetime.datetime.now(dt.tzinfo) if dt.tzinfo else datetime.datetime.now()
        same_day = (dt.date() == now.date())
        return dt.strftime("%H:%M:%S") if same_day else dt.strftime("%Y-%m-%d %H:%M:%S")

