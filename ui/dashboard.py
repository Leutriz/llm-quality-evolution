from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, DataTable, Static
from textual.containers import Container

class EvaluationDashboard(App):
    """Eine interaktive TUI-App zur Darstellung der LLM-Evaluierung."""
    
    TITLE = "LLM Quality Evolution"
    BINDINGS = [("q", "quit", "Beenden"), ("r", "run", "Start Test")]

    def __init__(self, selected_model, selected_datasets):
        super().__init__()
        self.selected_model = selected_model
        self.selected_datasets = selected_datasets

    def compose(self) -> ComposeResult:
        """Erstellt das Layout der App."""
        yield Header()
        yield Container(
            Static(f"Modell: [bold cyan]{self.selected_model}[/] | Datasets: [bold magenta]{', '.join(self.selected_datasets)}[/]", id="info-bar"),
            DataTable(id="results-table"),
            id="main-container"
        )
        yield Footer()

    def on_mount(self) -> None:
        """Wird aufgerufen, wenn die App startet."""
        table = self.query_one(DataTable)
        table.add_columns("ID", "Status", "Score", "TPS", "Latency (s)", "Tokens")
        table.cursor_type = "row"
        table.zebra_stripes = True

    def action_run(self):
        """Hier wird später die Test-Logik getriggert."""
        table = self.query_one(DataTable)
        table.add_row("Loading...", "⏳", "---", "---", "---", "---")

if __name__ == "__main__":
    # Nur zum Testen der UI-Optik
    app = EvaluationDashboard("Llama3", ["core_tests.json"])
    app.run()