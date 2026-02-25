import os
import subprocess
from textual.screen import Screen
from textual.widgets import Header, Footer, SelectionList, Label, Button
from textual.widgets.selection_list import Selection
from textual.containers import Container, Horizontal

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
        if event.button.id == "cancel-btn":
            self.app.pop_screen()
            return

        if event.button.id != "start-btn":
            return
        
        models = self.query_one("#select-model").selected
        datasets = self.query_one("#select-datasets").selected
        
        if not models or not datasets:
            self.app.notify("Bitte Modell und Dataset auswählen.", severity="warning")
            return
        
        model_name = models[0]
        dataset_names = ", ".join(datasets)

        from ui.results import ResultArchiveScreen
        for screen in self.app.screen_stack:
            if isinstance(screen, ResultArchiveScreen):
                screen.show_loading_state()
                screen.run_benchmark(model_name, datasets)
                break

        self.app.notify(
            f"Test von: {dataset_names}", 
            title=f"Benchmark mit {model_name} gestartet", 
            severity="warning"
        )

        self.app.pop_screen()
