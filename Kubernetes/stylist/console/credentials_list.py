import core
from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import DataTable
from textual.widgets.data_table import RowKey, ColumnKey

class CredentialsList(Widget):
    def __init__(self):
        super().__init__()
        self.id = "left-pane"
        self.border_title = "Credentials List"
        self.column_keys: dict[str, ColumnKey] = {}
        self.credential_rows: dict[str, RowKey] = {}
        self._sort_reverse: dict[ColumnKey, bool] = {}
        self._sort_key: ColumnKey | None = None

    def compose(self) -> ComposeResult:
        yield DataTable()

    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.cursor_type = "row"
        self.column_keys = {
            "Name": table.add_column("Name"),
        }
        self.set_interval(5, self.update_table)


    def on_data_table_header_selected(self, event: DataTable.HeaderSelected) -> None:
        self._sort_key = event.column_key

        # Toggle sort direction for this column
        previous = self._sort_reverse.get(event.column_key, False)
        self._sort_reverse[event.column_key] = not previous

        self.update_table()

    def update_table(self) -> None:
        table = self.query_one(DataTable)

        credentials = list(core.Backbone().context.credentials)

        # Determine sort key and direction
        if self._sort_key is not None:
            reverse = self._sort_reverse.get(self._sort_key, False)
            # For now, only "Name" can be sorted. Could add more columns later.
            if self._sort_key == self.column_keys.get("Name"):
                credentials.sort(key=lambda c: c.name, reverse=reverse)
        # else: no sorting

        table.clear(columns=False)
        self.credential_rows.clear()
        for credential in credentials:
            row = table.add_row(credential.name)
            self.credential_rows[credential.uuid] = row
            # Optionally keep current row selection and selected_credential logic
            if table.cursor_row == table.get_cell_coordinate(row, self.column_keys["Name"]).row:
                core.Backbone().context.selected_credential = credential
