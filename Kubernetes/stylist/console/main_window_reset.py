from textual.app import App, ComposeResult

from textual.widgets import Footer, Header, TabbedContent, TabPane
from .task_list import TaskList
from .task_details import TaskDetail
from .task_log import TaskLog
from .credentials_list import CredentialsList
from .credential_details import CredentialDetail
from textual.binding import Binding

from textual.containers import Container
import core
import datetime

class MainWindowReset(App):
    """A Textual app to manage stopwatches."""
    CSS_PATH = "horizontal_layout.tcss"
    TITLE = "Stylist"
    BINDINGS = [
        Binding(key="q", action="quit", description="Quit the app"),
        Binding(key="d", action="toggle_dark", description="Toggle dark mode")
    ]


    def __init__(self,
                 reset_orchestrator,
                 bootstrap_orchestrator,
                 quit_on_completion: bool = False):
        super().__init__()
        self.reset_complete = False
        self.reset_orchestrator = reset_orchestrator
        self.bootstrap_orchestrator = bootstrap_orchestrator

        self._orch_worker = None
        self.quit_on_completion = quit_on_completion


    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        with TabbedContent():
            with TabPane("Tasks (reset)", id="reset-tasks"):
                with Container(id="app-grid"):
                    yield TaskList(self.reset_orchestrator)
                    yield TaskDetail(self.reset_orchestrator)
                    yield TaskLog()
            with TabPane("Tasks (bootstrap)", id="bootstrap-tasks"):
                with Container(id="app-grid"):
                    yield TaskList(self.bootstrap_orchestrator)
                    yield TaskDetail(self.bootstrap_orchestrator)
                    yield TaskLog()
            with TabPane("Credentials"):
                with Container(id="app-grid"):
                    yield CredentialsList()
                    yield CredentialDetail()

        yield Footer()

    def _tick(self) -> None:
        """Update the UI elements periodically."""

        if self.reset_orchestrator.process_tasks() and not self.reset_complete:
            self.sub_title = f"Runtime: {str(datetime.datetime.now() - core.Backbone().context.program_start)[:-5]} "
        elif not self.reset_complete:
            self.notify("Cluster was reset")
            self.reset_complete = True
            titles = self.query_one(TabbedContent)
            titles.get_tab("bootstrap-tasks").title = "Tasks (bootstrap)"
            titles.active = "bootstrap-tasks"
        elif self.bootstrap_orchestrator.process_tasks():
            self.sub_title = f"Runtime: {str(datetime.datetime.now() - core.Backbone().context.program_start)[:-5]} "
        elif not core.Backbone().context.program_finished:
            core.Backbone().context.program_finished = datetime.datetime.now()
        elif core.Backbone().context.program_finished:
            self.sub_title = f"DONE (Runtime: {str(core.Backbone().context.program_finished - core.Backbone().context.program_start)[:-4]})"
            if self.quit_on_completion:
                self.exit()

    def action_toggle_dark(self) -> None:
        """An action to toggle dark mode."""
        self.theme = (
            "textual-dark" if self.theme == "textual-light" else "textual-light"
        )
    async def _run_orchestrator(self):
        await self.reset_orchestrator.run()
        await self.bootstrap_orchestrator.run()

    async def on_mount(self) -> None:
        """Called when the app is mounted."""
                # Kick off your orchestrator as a managed background worker.
        # This handles cancellation on app exit for you.
        self._orch_worker = self.run_worker(
            self._run_orchestrator(),
            name="orchestrator",
            group="bg",
            exclusive=True,
            exit_on_error=False,
        )
        self.set_interval(0.1, self._tick)

