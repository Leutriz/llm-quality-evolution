import asyncio
import json
import os
import yaml
from textual.app import App, ComposeResult
from textual.screen import Screen, ModalScreen
from textual.widgets import Header, Footer, Static, Label, DataTable, TextArea, Button, SelectionList
from textual.containers import Grid, Container, Horizontal
from textual.widgets.selection_list import Selection
from textual import work
import subprocess
import requests

from adapters.ollama import OllamaAdapter
from core.scoring import score_response

# --- 1. DETAIL MODAL (Antwort-Volltext) ---
class DetailModal(ModalScreen):
    def __init__(self, data):
        super().__init__()
        self.data = data

    def compose(self) -> ComposeResult:
        with Container(id="modal-container", classes="main-container"):
            yield Label(f"DETAILS: {self.data['id']}", classes="panel-title-text")
            yield Label("PROMPT:", classes="stat-line")
            yield Static(self.data['prompt'], classes="modal-text-box")
            yield Label("\nRESPONSE:", classes="stat-line")
            yield TextArea(self.data['response'], read_only=True, classes="modal-text-area")
            with Horizontal(classes="button-bar"):
                yield Button("Schließen", variant="primary", id="close-btn")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.app.pop_screen()

# --- 2. LAUNCHER SCREEN (Die Auswahl-Maske) ---
class LauncherScreen(Screen):
    BINDINGS = [("escape", "app.pop_screen", "Abbrechen")]

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(classes="main-container"):
            yield Label("TEST KONFIGURIEREN", classes="panel-title-text")
            yield Label("1. Modell auswählen (Ollama):", classes="stat-line")
            yield SelectionList(id="select-model")
            yield Label("\n2. Datasets auswählen:", classes="stat-line")
            yield SelectionList(id="select-datasets")
            with Horizontal(classes="button-bar"):
                yield Button("START", variant="success", id="start-btn")
                yield Button("Abbrechen", variant="error", id="cancel-btn")
        yield Footer()

    def on_mount(self) -> None:
        m_list = self.query_one("#select-model")
        try:
            res = subprocess.run(['ollama', 'list'], capture_output=True, text=True)
            for line in res.stdout.strip().split('\n')[1:]:
                if line:
                    name = line.split()[0]
                    m_list.add_option(Selection(name, name))
        except:
            m_list.add_option(Selection("Ollama offline", "none"))

        d_list = self.query_one("#select-datasets")
        if os.path.exists("datasets"):
            for f in os.listdir("datasets"):
                if f.endswith(".json"):
                    d_list.add_option(Selection(f, f))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "start-btn":
            selected_models = self.query_one("#select-model").selected
            selected_datasets = self.query_one("#select-datasets").selected
            
            if selected_models and selected_datasets:
                choices = {"model": selected_models[0], "datasets": selected_datasets}
                
                # Wir suchen den ResultScreen im Stack, um ihm die Daten zu übergeben
                for screen in self.app.screen_stack:
                    if isinstance(screen, ResultScreen):
                        self.app.pop_screen() # Schließe erst den Launcher
                        screen.start_new_run(choices) # Dann starte den Test
                        return
                
                # Falls wir keinen ResultScreen finden (Sicherheitshalber)
                self.app.notify("Konnte Result-Screen nicht finden!", severity="error")
        else:
            self.app.pop_screen()

# --- 3. RESULT SCREEN (Das Labor-Tagebuch) ---
class ResultScreen(Screen):
    BINDINGS = [
        ("r", "launch_test", "Neuer Test"),
        ("escape", "app.pop_screen", "Zurück"),
        ("enter", "show_details", "Details")
    ]

    def __init__(self):
        super().__init__()
        self.results_data = []
        self.eval_in_progress = False

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(classes="main-container"):
            yield Label("TEST ERGEBNISSE", id="run-title", classes="panel-title-text")
            yield DataTable(id="results-table")
            yield Label("", id="run-status-hint")
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.add_columns("ID", "Score", "TPS", "Latency", "Status")
        table.cursor_type = "row"

    def action_launch_test(self):
        if not self.eval_in_progress:
            self.app.push_screen(LauncherScreen())
        else:
            self.app.notify("Laufender Test!", severity="warning")

    def start_new_run(self, choices):
        self.eval_in_progress = True
        self.choices = choices
        self.results_data = [] # Wichtig: Alte Daten löschen
        
        table = self.query_one(DataTable)
        table.clear() # Wichtig: Tabelle leeren
        
        # Titel und Status aktualisieren
        self.query_one("#run-title").update(f"RUNNING: [bold cyan]{choices['model']}[/]")
        self.query_one("#run-status-hint").update("[blink]⚙️ - Test läuft aktiv...[/]")
        
        self.run_evaluation()

    @work(exclusive=True, thread=True)
    def run_evaluation(self):
        table = self.query_one(DataTable)
        adapter = OllamaAdapter(self.choices['model'])
        
        for ds_name in self.choices['datasets']:
            with open(f"datasets/{ds_name}", "r", encoding="utf-8") as f:
                dataset = json.load(f)
            
            for item in dataset:
                res = adapter.send(item['prompt'])
                eval_data = score_response(res.get("response", ""), item.get("expected_keywords", []))
                score = eval_data.get('score', 0)
                metrics = res.get("metrics", {})

                self.results_data.append({
                    "id": item['id'], "prompt": item['prompt'], 
                    "response": res.get("response", ""), "score": score
                })

                row_data = (item['id'], f"{score}%", str(metrics.get("tps", 0)), 
                            f"{metrics.get('duration', 0)}s", "✅" if score >= 80 else "⚠️")
                
                self.app.call_from_thread(lambda d=row_data: table.add_row(*d))
        
        self.app.call_from_thread(self.finalize_ui)

    def finalize_ui(self):
        self.eval_in_progress = False
        self.query_one("#run-title").update(f"COMPLETED: [bold green]{self.choices['model']}[/]")
        self.query_one("#run-status-hint").update("✅ Run beendet. Drücke [b]R[/] für neuen Test.")

    def action_show_details(self):
        idx = self.query_one(DataTable).cursor_row
        if idx is not None and idx < len(self.results_data):
            self.app.push_screen(DetailModal(self.results_data[idx]))

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


class WelcomeScreen(Screen):
    """Das Claude-Style Startmenü."""
    BINDINGS = [
        ("t", "show_tests", "Tests"),
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

    async def action_show_tests(self):
        self.app.push_screen(ResultScreen())

    def action_open_config(self):
        self.app.push_screen(ConfigScreen())

    def action_show_models(self):
        self.app.push_screen(ModelScreen())

    def action_show_datasets(self):
        self.app.push_screen(DatasetScreen())

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

    #modal-container { background: #1e1e1e; border: thick #28d483; padding: 2; margin: 4 10; height: auto; }
    .modal-text { margin-bottom: 1; color: #cccccc; }
    #hint-text { color: #888888; text-align: center; margin-top: 1; }

    #modal-container { background: #1e1e1e; border: thick #28d483; margin: 2 8; padding: 1 2; height: 80%; }
    .modal-text-box { background: #2d2d2d; padding: 1; border: solid #3f3f3f; margin-bottom: 1; color: #cccccc; }
    .modal-text-area { height: 12; border: solid #3f3f3f; background: #1a1a1a; color: #28d483; }
    #run-status-hint { color: #28d483; text-align: right; text-style: italic; }

    SelectionList { height: 5; border: solid #3f3f3f; background: #1e1e1e; margin-bottom: 1; }
    .button-bar { margin-top: 1; height: 3; align: center middle; }

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