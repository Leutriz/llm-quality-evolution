from textual.app import App, ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, Label
from textual.containers import Grid, Container
from textual import work
import requests

from core.scoring import score_response
from ui.config_editor import ConfigScreen
from ui.datasets import DatasetScreen
from ui.models import ModelScreen
from ui.results import ResultArchiveScreen

class WelcomeScreen(Screen):
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
                Label("SYSTEM QUICK-LINKS", classes="panel-title-text"),
                Label("• [b]T[/]: Test-Archiv & neue Runs", classes="stat-line"),
                Label("• [b]D[/]: Test-Datasets LiOverviewst", classes="stat-line"),
                Label("• [b]M[/]: Local Ollama Models", classes="stat-line"),
                Label("• [b]C[/]: Config (YAML) bearbeiten", classes="stat-line"),
                Label("• [b]Q[/]: Programm beenden", classes="stat-line"),
                id="right-panel"
            ),
            id="main-grid"
        )
        yield Footer()

    def on_mount(self) -> None:
        self.check_provider_status()

    @work(exclusive=True, thread=True)
    def check_provider_status(self):
        status_lines = []
        try:
            requests.get("http://localhost:11434/api/tags", timeout=1)
            status_lines.append("Ollama: [#14baba]online[/]")
            self.ollama_online = True
        except:
            status_lines.append("Ollama: [#ff4b4b]offline[/]")
            self.ollama_online = False

        status_lines.append("OpenAI: [#e89f46]configured[/]") 

        status_label = self.query_one("#status-label")
        status_label.update("\n".join(status_lines))

    async def action_show_tests(self):
        self.app.push_screen(ResultArchiveScreen())

    def action_open_config(self):
        self.app.push_screen(ConfigScreen())

    def action_show_models(self):
        self.app.push_screen(ModelScreen())

    def action_show_datasets(self):
        self.app.push_screen(DatasetScreen())



class EvaluationApp(App):
    TITLE = "LLM Quality Evolution"
    BINDINGS = [("q", "quit", "Quit")]

    def on_mount(self) -> None:
        self.push_screen(WelcomeScreen())
    
    def action_quit(self):
        self.exit()

if __name__ == "__main__":
    app = EvaluationApp()
    app.run()