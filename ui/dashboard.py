import asyncio
import json
import os
import yaml  # Neu: für config
from textual.app import App, ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, Static, Label, DataTable, TextArea, Button
from textual.containers import Grid, Container, Vertical, Horizontal
from textual import work
import subprocess
import requests

from core.launcher import Launcher
from adapters.ollama import OllamaAdapter
from core.scoring import score_response


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


# --- NEUER SCREEN: CONFIG EDITOR ---

class ConfigScreen(Screen):
    """Ein einfacher YAML-Editor für die config.yaml."""
    BINDINGS = [("escape", "app.pop_screen", "Abbrechen"), ("ctrl+s", "save_config", "Speichern")]

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(id="config-container", classes="main-container"):
            yield Label("KONFIGURATION EDITIEREN", id="config-title", classes="panel-title-text")
            yield TextArea(id="config-editor", language="yaml")
            with Horizontal(classes="button-bar"):
                yield Button("Speichern", variant="success", id="save-btn")
                yield Button("Abbrechen", variant="error", id="cancel-btn")
        yield Footer()

    def on_mount(self) -> None:
        # Lade die config.yaml in den Editor
        try:
            with open("config/config.yaml", "r", encoding="utf-8") as f:
                content = f.read()
            self.query_one(TextArea).text = content
        except Exception as e:
            self.query_one(TextArea).text = f"# Fehler beim Laden: {e}"

    def action_save_config(self):
        text = self.query_one(TextArea).text
        try:
            # Validierung: Ist es gültiges YAML?
            yaml.safe_load(text)
            with open("config/config.yaml", "w", encoding="utf-8") as f:
                f.write(text)
            self.app.notify("Konfiguration erfolgreich gespeichert!", title="Erfolg")
            self.app.pop_screen()
        except Exception as e:
            self.app.notify(f"Ungültiges YAML: {e}", title="Fehler", severity="error")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save-btn":
            self.action_save_config()
        else:
            self.app.pop_screen()

# --- UPDATE WELCOME SCREEN ---

class WelcomeScreen(Screen):
    """Das Claude-Style Startmenü."""
    BINDINGS = [
        ("r", "new_test", "Run Test"),
        ("m", "show_models", "Models"),
        ("d", "show_datasets", "Datasets"),
        ("c", "open_config", "Config"),
        ("q", "quit", "Quit")
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        yield Grid(
            Container(
                Label("LLM QUALITY EVOLUTION", id="app-title"),
                Label("Model Benchmarking", id="app-subtitle"),
                Label("Ollama: [#e89f46]checking...[/]\nOpenAI: [#e89f46]checking...[/]", id="status-label"),
                id="left-panel"
            ),
            Container(
                Label("RECENT ACTIVITY", classes="panel-title"),
                Label("• Llama3: [#14baba]85% Score[/]", classes="stat-line"),
                Label("• Mistral: [#14baba]91% Score[/]", classes="stat-line"),
                id="right-panel"
            ),
            id="main-grid"
        )
        yield Footer()

    def on_mount(self) -> None:
        self.check_provider_status()

    @work(exclusive=True, thread=True)
    def check_provider_status(self):
        """Prüft im Hintergrund, ob Ollama läuft."""
        status_lines = []

        # 1. Check Ollama
        try:
            requests.get("http://localhost:11434/api/tags", timeout=1)
            status_lines.append("Ollama: [#14baba]online[/]")
            self.ollama_online = True
        except:
            status_lines.append("Ollama: [#ff4b4b]offline[/]")
            self.ollama_online = False

        # 2. Check OpenAI (Beispielhaft - checkt nur ob API Key da ist oder pingt API)
        # Hier könnte man später einen echten Ping zu api.openai.com machen
        status_lines.append("OpenAI: [#e89f46]configured[/]") 

        # Update das Label mit allen Stati
        status_label = self.query_one("#status-label")
        status_label.update("\n".join(status_lines))

    async def action_new_test(self):
        launcher = Launcher()
        with self.app.suspend():
            choices = await asyncio.to_thread(launcher.run)
        if choices:
            self.app.push_screen(ResultScreen(choices))

    def action_open_config(self):
        self.app.push_screen(ConfigScreen())

    def action_show_models(self):
        self.app.push_screen(ModelScreen())

    def action_show_datasets(self):
        self.app.push_screen(DatasetScreen())

class ResultScreen(Screen):
    """Die Seite mit der Live-Tabelle."""
    BINDINGS = [("escape", "app.pop_screen", "Zurück zum Dashboard")]

    def __init__(self, choices):
        super().__init__()
        self.choices = choices

    def compose(self) -> ComposeResult:
        yield Header()
        yield Container(
            Static(f"RUNNING: [bold cyan]{self.choices['model']}[/]", id="run-info"),
            DataTable(id="results-table"),
        )
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.add_columns("ID", "Score", "TPS", "Latency", "Status")
        table.cursor_type = "row"
        self.run_evaluation()

    @work(exclusive=True, thread=True)
    def run_evaluation(self):
        table = self.query_one(DataTable)
        adapter = OllamaAdapter(self.choices['model'])
        
        for ds_name in self.choices['datasets']:
            with open(f"datasets/{ds_name}", "r", encoding="utf-8") as f:
                dataset = json.load(f)
            
            for item in dataset:
                row_key = table.add_row(item['id'], "...", "...", "...", "⏳")
                result = adapter.send(item['prompt'])
                eval_data = score_response(result.get("response", ""), item.get("expected_keywords", []))
                metrics = result.get("metrics", {})

                table.update_cell(row_key, "Score", f"{eval_data['score']}%")
                table.update_cell(row_key, "TPS", str(metrics.get("tps", 0)))
                table.update_cell(row_key, "Latency", f"{metrics.get('duration', 0)}s")
                table.update_cell(row_key, "Status", "✅" if eval_data['score'] >= 80 else "⚠️")

# --- MAIN APP ---

class EvaluationApp(App):
    TITLE = "LLM Quality Evolution"
    BINDINGS = [("q", "quit", "Quit")]

    CSS = """
    Screen { background: #1e1e1e; }
    #main-grid { grid-size: 2; grid-columns: 1fr 1fr; padding: 2; grid-gutter: 2; }
    #left-panel, #right-panel { background: #2d2d2d; border: tall #3f3f3f; padding: 2; }
    
    #app-title { color: #28d483; text-style: bold; margin-bottom: 1; }
    #app-subtitle { color: #888888; margin-bottom: 2; }
    .panel-title { color: #28d483; text-style: bold; margin-bottom: 1; }
    .stat-line { color: #cccccc; }

    .main-container { padding: 2; background: #2d2d2d; margin: 2; border: tall #3f3f3f; height: 1fr; }
    .panel-title-text { color: #28d483; text-style: bold; margin-bottom: 1; }
    TextArea { height: 1fr; border: solid #3f3f3f; margin-bottom: 1; }
    .button-bar { height: 3; align: center middle; column-span: 2; }
    #model-container, #dataset-container, #config-container { padding: 2; background: #2d2d2d; margin: 2; border: tall #3f3f3f; }
    #model-title, #dataset-title, #config-title { color: #28d483; text-style: bold; margin-bottom: 1; }

    #run-info { background: $accent; color: white; padding: 1; margin-bottom: 1; }
    DataTable { height: 1fr; border: solid #3f3f3f; }
    """

    def on_mount(self) -> None:
        self.push_screen(WelcomeScreen())
    
    def action_quit(self):
        self.exit()

if __name__ == "__main__":
    app = EvaluationApp()
    app.run()