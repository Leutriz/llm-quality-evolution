import os
import subprocess
import json
from textual.screen import Screen
from textual.widgets import Header, Footer, SelectionList, Label, Button
from textual.widgets.selection_list import Selection
from textual.containers import Container, Horizontal
from textual import work

from adapters.ollama import OllamaAdapter
from core.scoring import score_response
from core.history_manager import save_run

class LauncherScreen(Screen):
    BINDINGS = [("escape", "app.pop_screen", "Abbrechen")]

    def __init__(self, callback=None):
        super().__init__()
        self.callback = callback

    def compose(self):
        yield Header()
        with Container(classes="main-container"):
            yield Label("TEST KONFIGURIEREN", classes="panel-title-text")
            
            yield Label("1. Modell (Ollama):", classes="stat-line")
            yield SelectionList(id="select-model")
            
            yield Label("\n2. Datasets:", classes="stat-line")
            yield SelectionList(id="select-datasets")
            
            with Horizontal(classes="button-bar"):
                yield Button("TEST STARTEN", variant="success", id="start-btn")
                yield Button("Abbrechen", variant="error", id="cancel-btn")
        yield Footer()

    def on_mount(self):
        # Modelle laden
        m_list = self.query_one("#select-model")
        try:
            res = subprocess.run(['ollama', 'list'], capture_output=True, text=True)
            for line in res.stdout.strip().split('\n')[1:]:
                if line:
                    name = line.split()[0]
                    m_list.add_option(Selection(name, name))
        except:
            m_list.add_option(Selection("Ollama offline", "none"))

        # Datasets laden
        d_list = self.query_one("#select-datasets")
        if os.path.exists("datasets"):
            for f in os.listdir("datasets"):
                if f.endswith(".json"):
                    d_list.add_option(Selection(f, f))

    def on_button_pressed(self, event):
        if event.button.id == "start-btn":
            models = self.query_one("#select-model").selected
            datasets = self.query_one("#select-datasets").selected
            
            from ui.results import ResultArchiveScreen
            
            if models and datasets:
                model_name = models[0]
                dataset_names = ", ".join(datasets)
                for screen in self.app.screen_stack:
                    if isinstance(screen, ResultArchiveScreen):
                        screen.show_loading_state()
                        break
                self.run_benchmark(models[0], datasets)
                self.app.notify(
                    f"Test von: {dataset_names}", 
                    title=f"Benchmark mit {model_name} gestartet",
                    timeout=10
                )
                self.app.pop_screen()
        else:
            self.app.pop_screen()

    @work(exclusive=True, thread=True)
    def run_benchmark(self, model, datasets):
        adapter = OllamaAdapter(model)
        all_results = []

        for ds_name in datasets:
            ds_path = os.path.join("datasets", ds_name)
            with open(ds_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            for item in data:
                res = adapter.send(item['prompt'])
                eval_data = score_response(res.get("response", ""), item.get("expected_keywords", []))
                
                all_results.append({
                    "id": item.get('id', 'unknown'),
                    "prompt": item['prompt'],
                    "response": res.get("response", ""),
                    "score": eval_data.get('score', 0),
                    "metrics": res.get("metrics", {})
                })

        save_run(model, datasets, all_results)
        
        self.app.call_from_thread(self.finalize_run)

    def finalize_run(self):
        self.app.notify("Benchmark abgeschlossen und gespeichert!", title="Erfolg")
        if self.callback:
            self.callback()
        try:
            indicator = self.app.query_one("#active-run-indicator")
            indicator.styles.display = "none"
        except:
            pass