from textual.screen import ModalScreen
from textual.widgets import DataTable, Label, Button
from textual.containers import Container, Horizontal

class RunDetailModal(ModalScreen):
    def __init__(self, run_data):
        super().__init__()
        self.run_data = run_data

    def compose(self):
        with Container(classes="main-container", id="modal-container"):
            yield Label(f"DETAILS: {self.run_data['model']} ({self.run_data['timestamp']})", classes="panel-title-text")
            yield DataTable(id="detail-table")
            with Horizontal(classes="button-bar"):
                yield Button("Schließen", variant="primary", id="close-btn")

    def on_mount(self):
        table = self.query_one("#detail-table")
        table.add_columns("ID", "Score", "Prompt-Vorschau")
        for d in self.run_data["details"]:
            table.add_row(d["id"], f"{d['score']}%", d["prompt"][:50] + "...")

    def on_button_pressed(self):
        self.app.pop_screen()