from textual.screen import Screen
from textual.widgets import Header, Footer, DataTable, Label
from textual.containers import Container
from core.history_manager import load_all_runs
from ui.launcher import LauncherScreen
from ui.modals import RunDetailModal

class ResultArchiveScreen(Screen):
    BINDINGS = [
        ("r", "launch_test", "Neuer Run"),
        ("enter", "view_details", "Details öffnen"),
        ("escape", "app.pop_screen", "Zurück")
    ]

    def on_data_table_row_selected(self, event):
        self.action_view_details()

    def compose(self):
        yield Header()
        with Container(classes="main-container"):
            yield Label("TEST ARCHIV", classes="panel-title-text")
            yield Label("", id="active-run-indicator")
            yield DataTable(id="history-table")
            yield Label("Enter: Details | R: Neuer Test | E: Export", id="hint-text")
        yield Footer()

    def on_mount(self):
        table = self.query_one("#history-table")
        table.add_columns("Datum", "Modell", "Datasets", "Ø Score", "Status")
        table.cursor_type = "row"
        self.refresh_history()

    def refresh_history(self):
        table = self.query_one("#history-table")
        table.clear()
        self.runs = load_all_runs()
        for run in self.runs:
            table.add_row(
                run["timestamp"],
                run["model"],
                ", ".join(run["datasets"]),
                f"{run['avg_score']}%",
                "✅" if run["avg_score"] >= 80 else "⚠️"
            )

    def show_loading_state(self):
        indicator = self.query_one("#active-run-indicator")
        indicator.update("[#e89f46]Testlauf aktiv... Bitte warten.[/]")
        indicator.styles.display = "block"

    def action_launch_test(self):
        self.app.push_screen(LauncherScreen(callback=self.refresh_history))

    def action_view_details(self):
        table = self.query_one("#history-table")
        idx = table.cursor_row
        
        if idx is not None and idx < len(self.runs):
            selected_run = self.runs[idx]
            from ui.modals import RunDetailModal
            self.app.push_screen(RunDetailModal(selected_run))
        else:
            self.app.notify("Kein Lauf ausgewählt.", severity="warning")