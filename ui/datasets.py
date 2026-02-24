import json
import os
from textual.app import ComposeResult
from textual.screen import Screen 
from textual.widgets import Header, Footer, Label, DataTable
from textual.containers import Container 
from textual import work


class DatasetScreen(Screen):
    """Zeigt alle verfügbaren Test-Datasets an."""
    BINDINGS = [("escape", "app.pop_screen", "Zurück")]

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(id="dataset-container", classes="main-container"):
            yield Label("VERFÜGBARE DATASETS", id="dataset-title", classes="panel-title-text")
            yield DataTable(id="dataset-table")
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one("#dataset-table")
        table.add_columns("DATEI", "PROMPTS", "VORSCHAU")
        table.cursor_type = "row"
        self.load_datasets()

    @work(exclusive=True, thread=True)
    def load_datasets(self):
        table = self.query_one(DataTable)
        dataset_dir = "datasets"
        
        if not os.path.exists(dataset_dir):
            self.app.notify("Ordner /datasets nicht gefunden!", severity="error")
            return

        for file in os.listdir(dataset_dir):
            if file.endswith(".json"):
                try:
                    with open(os.path.join(dataset_dir, file), "r", encoding="utf-8") as f:
                        data = json.load(f)
                        count = len(data)
                        preview = data[0].get("prompt", "")[:40] + "..." if data else "Leer"
                        table.add_row(file, str(count), preview)
                except Exception:
                    table.add_row(file, "Fehler", "Datei konnte nicht gelesen werden")
