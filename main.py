from textual.app import App
from ui.dashboard import WelcomeScreen

class EvaluationApp(App):
    TITLE = "LLM Quality Evolution"
    BINDINGS = [("q", "quit", "Quit")]
    
    # Zentrales CSS (kann auch in ui/style.css stehen)
    CSS = """
    .main-container { background: #2d2d2d; border: tall #3f3f3f; padding: 1 2; margin: 1; }
    .panel-title-text { color: #28d483; text-style: bold; margin-bottom: 1; }
    #modal-container { background: #1e1e1e; border: thick #28d483; margin: 2 4; height: 90%; }
    DataTable { height: 1fr; border: solid #3f3f3f; }
    .button-bar { height: 3; align: center middle; margin-top: 1; }

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

    #active-run-indicator { color: #ffff00; padding: 0 1; margin-bottom: 1; display: none; border: solid #e89f46; }

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

    def on_mount(self):
        self.push_screen(WelcomeScreen())

if __name__ == "__main__":
    app = EvaluationApp()
    app.run()