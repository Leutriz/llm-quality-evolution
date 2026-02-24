import yaml
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, TextArea, Label, Button
from textual.containers import Container, Horizontal

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