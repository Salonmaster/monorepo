from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, DataTable, Footer, Header, Input, Select, Static, TextArea
from textual.widgets.data_table import RowKey

from stylist import helpers
from stylist.helpers.remote_db import SecretsDatabaseHandle

FILTER_ALL = "__all__"
FILTER_SHARED = "__shared__"
DEFAULT_ENVIRONMENTS = ("tst", "acc", "prd")
VALUE_PREVIEW_LIMIT = 60
NEWLINE_SYMBOL = "⏎"


@dataclass(slots=True)
class SecretRecord:
    environment: str | None
    namespace: str
    name: str
    key: str
    value: str | None

    @property
    def identity(self) -> str:
        env = self.environment or ""
        return "|".join((env, self.namespace, self.name, self.key))

    @property
    def env_label(self) -> str:
        return self.environment or "shared"

    @property
    def value_preview(self) -> str:
        if not self.value:
            return ""
        preview = self.value.replace("\r\n", "\n").replace("\r", "\n").replace("\n", NEWLINE_SYMBOL)
        if len(preview) <= VALUE_PREVIEW_LIMIT:
            return preview
        return f"{preview[: VALUE_PREVIEW_LIMIT - 3]}..."


class DatabaseEditorApp(App):
    """Interactive TUI for viewing and editing secrets in the Stylist database."""

    CSS_PATH = "database_editor.tcss"
    TITLE = "Stylist Secrets Editor"
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("ctrl+s", "save_secret", "Save"),
        Binding("n", "new_secret", "New"),
        Binding("r", "refresh_data", "Reload"),
        Binding("delete", "delete_secret", "Delete"),
    ]

    def __init__(
        self,
        db_path: str,
        password: str | None = None,
        environment_filter: str | None = None,
        db_handle: SecretsDatabaseHandle | None = None,
    ) -> None:
        super().__init__()
        self.db_path = db_path
        self.password = password
        self._records: list[SecretRecord] = []
        self._row_lookup: dict[RowKey, SecretRecord] = {}
        self._selected_identity: str | None = None
        self._filter_value: str = FILTER_ALL
        if environment_filter is not None:
            self._filter_value = environment_filter or FILTER_ALL
        self._db_handle = db_handle

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(id="editor-body"):
            with Vertical(id="table-panel"):
                yield Static("Secrets", id="table-title")
                with Horizontal(id="table-toolbar"):
                    yield Select(
                        id="env-filter",
                        prompt="Environment filter",
                        options=self._initial_filter_options(),
                        value=self._filter_value,
                    )
                    yield Button("Reload", id="reload-button", variant="primary")
                    yield Button("New", id="new-button")
                yield DataTable(id="secrets-table")
            with Vertical(id="form-panel"):
                yield Static("Secret Details", id="form-title")
                yield from self._build_form()
        yield Footer()

    def _build_form(self) -> Iterable[Static | Input | Horizontal]:
        yield Static("Environment", classes="field-label")
        yield Input(placeholder="Environment (optional)", id="env-input")
        yield Static("Namespace", classes="field-label")
        yield Input(placeholder="Namespace", id="namespace-input")
        yield Static("Name", classes="field-label")
        yield Input(placeholder="Secret name", id="name-input")
        yield Static("Key", classes="field-label")
        yield Input(placeholder="Key", id="key-input", value="value")
        yield Static("Value", classes="field-label")
        value_area = TextArea(id="value-input")
        yield value_area
        with Horizontal(id="form-buttons"):
            yield Button("Save", id="save-button", variant="success")
            yield Button("Delete", id="delete-button", variant="error")
            yield Button("Reset", id="reset-button")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @property
    def _table(self) -> DataTable:
        return self.query_one("#secrets-table", DataTable)

    def _input(self, input_id: str) -> Input:
        return self.query_one(f"#{input_id}", Input)

    def _value_area(self) -> TextArea:
        return self.query_one("#value-input", TextArea)

    def _filter_select(self) -> Select:
        return self.query_one("#env-filter", Select)

    def _initial_filter_options(self) -> list[tuple[str, str]]:
        return [
            ("All environments", FILTER_ALL),
            ("Shared only", FILTER_SHARED),
            *( (env.upper(), env) for env in DEFAULT_ENVIRONMENTS ),
        ]

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def on_mount(self) -> None:
        table = self._table
        table.add_column("Env", key="env", width=9)
        table.add_column("Namespace", key="namespace")
        table.add_column("Name", key="name")
        table.add_column("Key", key="key")
        table.add_column("Value", key="value")
        table.cursor_type = "row"
        table.zebra_stripes = True
        self.sub_title = self.db_path
        self.reset_form()
        self.refresh_from_db()

    # ------------------------------------------------------------------
    # Data loading & filtering
    # ------------------------------------------------------------------

    def refresh_from_db(self) -> None:
        try:
            rows = helpers.database.fetch_all_secrets(self.db_path, self.password)
        except Exception as exc:  # pragma: no cover - visual feedback only
            self.notify(f"Failed to load secrets: {exc}")
            return
        self._records = [
            SecretRecord(environment=row[0], namespace=row[1], name=row[2], key=row[3], value=row[4])
            for row in rows
        ]
        self._update_filter_options()
        self._refresh_table()

    def _update_filter_options(self) -> None:
        select = self._filter_select()
        environments = sorted({rec.environment for rec in self._records if rec.environment})
        options: list[tuple[str, str]] = [
            ("All environments", FILTER_ALL),
            ("Shared only", FILTER_SHARED),
        ]
        options.extend((env.upper(), env) for env in environments)
        select.set_options(options)
        if self._filter_value not in {value for _, value in options}:
            self._filter_value = FILTER_ALL
        select.value = self._filter_value

    def _filtered_records(self) -> Iterable[SecretRecord]:
        if self._filter_value == FILTER_ALL:
            return list(self._records)
        if self._filter_value == FILTER_SHARED:
            return [rec for rec in self._records if rec.environment is None]
        return [rec for rec in self._records if rec.environment == self._filter_value]

    def _refresh_table(self) -> None:
        table = self._table
        selected_identity = self._selected_identity
        table.clear()
        self._row_lookup.clear()
        for record in self._filtered_records():
            row_key = table.add_row(
                record.env_label,
                record.namespace,
                record.name,
                record.key,
                record.value_preview,
                key=record.identity,
            )
            self._row_lookup[row_key] = record
        if selected_identity:
            self._select_row(selected_identity)

    def _select_row(self, identity: str) -> None:
        table = self._table
        if not table.row_count:
            return
        try:
            row_index = table.get_row_index(identity)
        except KeyError:
            return
        # Position the cursor and ensure the selected row is visible when possible
        table.cursor_coordinate = (row_index, 0)
        if hasattr(table, "scroll_to_coordinate"):
            table.scroll_to_coordinate(row_index, 0)

    # ------------------------------------------------------------------
    # Form helpers
    # ------------------------------------------------------------------

    def reset_form(self) -> None:
        self._selected_identity = None
        self._input("env-input").value = ""
        self._input("namespace-input").value = ""
        self._input("name-input").value = ""
        self._input("key-input").value = "value"
        self._value_area().load_text("")

    def populate_form(self, record: SecretRecord) -> None:
        self._input("env-input").value = record.environment or ""
        self._input("namespace-input").value = record.namespace
        self._input("name-input").value = record.name
        self._input("key-input").value = record.key
        self._value_area().load_text(record.value or "")
        self._selected_identity = record.identity

    def _collect_form_data(self) -> SecretRecord | None:
        namespace = self._input("namespace-input").value.strip()
        name = self._input("name-input").value.strip()
        key = self._input("key-input").value.strip() or "value"
        environment = self._input("env-input").value.strip() or None
        raw_value = self._value_area().text or ""
        value = raw_value if raw_value else None

        required = {
            "namespace": namespace,
            "name": name,
        }
        missing = [label for label, val in required.items() if not val]
        if missing:
            self.notify(f"Missing required field(s): {', '.join(missing)}")
            return None

        return SecretRecord(environment=environment, namespace=namespace, name=name, key=key, value=value)

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def action_refresh_data(self) -> None:
        self.refresh_from_db()
        self.notify("Secrets reloaded")

    def action_new_secret(self) -> None:
        self.reset_form()
        self.notify("Ready to create a new secret")

    def action_save_secret(self) -> None:
        record = self._collect_form_data()
        if not record:
            return
        try:
            helpers.database.upsert_secret(
                db_path=self.db_path,
                namespace=record.namespace,
                name=record.name,
                key=record.key,
                value=record.value,
                environment=record.environment,
                password=self.password,
                silent=True,
            )
            if self._db_handle:
                self._db_handle.mark_dirty()
        except Exception as exc:  # pragma: no cover - interactive feedback
            self.notify(f"Failed to save secret: {exc}")
            return
        self.notify("Secret saved")
        self._selected_identity = record.identity
        self.refresh_from_db()
        self.populate_form(record)

    def action_delete_secret(self) -> None:
        if not self._selected_identity:
            self.notify("Select a secret to delete")
            return
        record = next((r for r in self._records if r.identity == self._selected_identity), None)
        if record is None:
            self.notify("Selected secret is no longer available")
            return
        try:
            helpers.database.remove_secret(
                db_path=self.db_path,
                namespace=record.namespace,
                name=record.name,
                key=record.key,
                environment=record.environment,
                password=self.password,
                silent=True,
            )
            if self._db_handle:
                self._db_handle.mark_dirty()
        except Exception as exc:  # pragma: no cover - interactive feedback
            self.notify(f"Failed to delete secret: {exc}")
            return
        self.notify("Secret removed")
        self.reset_form()
        self.refresh_from_db()

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        record = self._row_lookup.get(event.row_key)
        if record:
            self.populate_form(record)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        match event.button.id:
            case "save-button":
                self.action_save_secret()
            case "delete-button":
                self.action_delete_secret()
            case "reset-button":
                self.reset_form()
            case "reload-button":
                self.action_refresh_data()
            case "new-button":
                self.action_new_secret()

    def on_select_changed(self, event: Select.Changed[str]) -> None:
        if event.select.id == "env-filter":
            self._filter_value = event.value or FILTER_ALL
            self._refresh_table()
