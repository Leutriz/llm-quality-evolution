import json
import os
import traceback

from textual import work
from textual.screen import Screen
from textual.widgets import Header, Footer, DataTable, Label
from textual.containers import Container
from adapters.ollama import OllamaAdapter
from core.history_manager import load_all_runs, save_run
from core.scoring import score_response
from ui.launcher import LauncherScreen
from ui.events import BenchmarkFinished

class ResultArchiveScreen(Screen):
    BINDINGS = [
        ("r", "launch_test", "Neuer Run"),
        ("enter", "view_details", "Details öffnen"),
        ("escape", "app.pop_screen", "Zurück")
    ]

    def on_data_table_row_selected(self, event):
        self.action_view_details()

    def on_benchmark_finished(self, message: BenchmarkFinished):
        self.refresh_history()
        indicator = self.query_one("#active-run-indicator")
        indicator.styles.display = "none"

    def compose(self):
        yield Header()
        with Container(classes="main-container"):
            yield Label("TEST ARCHIV", classes="panel-title-text")
            yield Label("", id="active-run-indicator")
            yield DataTable(id="history-table")
            yield Label("Enter: Details | R: Neuer Test | E: Export", id="hint-text")
        yield Footer()

    def on_mount(self):
        table = self.query_one("#history-table")
        table.add_columns("Datum", "Modell", "Ø Score", "Status", "Datasets")
        table.cursor_type = "row"
        self.refresh_history()
        self._run_active = False

    def refresh_history(self):
        table = self.query_one("#history-table")
        table.clear()
        self.runs = load_all_runs()
        for run in self.runs:
            table.add_row(
                run["timestamp"],
                run["model"],
                f"{run['avg_score']}%",
                "✅" if run["avg_score"] >= 80 else "⚠️",
                ", ".join(run["datasets"])
            )

    def show_loading_state(self):
        indicator = self.query_one("#active-run-indicator")
        indicator.update("[#e89f46]Testlauf aktiv... Bitte warten.[/]")
        indicator.styles.display = "block"

    def action_launch_test(self):
        if self._run_active:
            self.app.notify("Ein Testlauf läuft bereits. Bitte warten.", severity="warning")
            return
    
        self.app.push_screen(LauncherScreen(callback=self.refresh_history))

    def action_view_details(self):
        table = self.query_one("#history-table")
        idx = table.cursor_row
        
        if idx is not None and idx < len(self.runs):
            selected_run = self.runs[idx]
            from ui.modals import RunDetailModal
            self.app.push_screen(RunDetailModal(selected_run))
        else:
            self.app.notify("Kein Lauf ausgewählt.", severity="warning")
    
    @work(exclusive=True, thread=True)
    def run_benchmark(self, model, datasets):
        try:
            adapter = OllamaAdapter(model)
            all_results = []

            for ds_name in datasets:
                ds_path = os.path.join("datasets", ds_name)
                with open(ds_path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                for item in data:
                    res = adapter.send(item["prompt"])
                    eval_data = score_response(
                        res.get("response", ""),
                        item.get("expected_keywords", [])
                    )

                    all_results.append({
                        "id": item.get("id", "unknown"),
                        "prompt": item["prompt"],
                        "response": res.get("response", ""),
                        "score": eval_data.get("score", 0),
                        "metrics": res.get("metrics", {})
                    })
            save_run(model, datasets, all_results)
            self.app.call_from_thread(self._finalize_global)
        except Exception:
            traceback.print_exc()
        
    def _finalize_global(self):
        self.app.notify("Benchmark done!")

        from ui.results import ResultArchiveScreen
        for screen in self.app.screen_stack:
            if isinstance(screen, ResultArchiveScreen):
                screen.refresh_history()
                try:
                    indicator = screen.query_one("#active-run-indicator")
                    indicator.styles.display = "none"
                except:
                    pass