from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, Label, DataTable
from textual.containers import Container
from textual import work
import subprocess


class ModelScreen(Screen):
    """Zeigt alle lokal installierten Ollama-Modelle an."""
    BINDINGS = [("escape", "app.pop_screen", "Zurück")]

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(id="model-container"):
            yield Label("INSTALLIERTE MODELLE (Ollama)", id="model-title")
            yield DataTable(id="model-table")
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.add_columns("NAME", "ID", "GRÖSSE", "STATUS")
        table.cursor_type = "row"
        self.load_models()

    @work(exclusive=True, thread=True)
    def load_models(self):
        table = self.query_one(DataTable)
        try:
            # Wir rufen 'ollama list' ab
            result = subprocess.run(['ollama', 'list'], capture_output=True, text=True)
            lines = result.stdout.strip().split('\n')[1:] # Header überspringen
            
            for line in lines:
                parts = line.split()
                if len(parts) >= 3:
                    name = parts[0]
                    model_id = parts[1]
                    size = parts[2]
                    table.add_row(name, model_id, size, "✅ Ready")
        except Exception as e:
            self.app.notify(f"Fehler beim Laden der Modelle: {e}", severity="error")
