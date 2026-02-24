from ui.dashboard import EvaluationApp

def main():
    """
    Haupteinstiegspunkt für LLM Quality Evolution v2.1.
    Initialisiert die TUI-Anwendung und startet den Event-Loop.
    """
    app = EvaluationApp()
    
    try:
        app.run()
    except Exception as e:
        print(f"💥 Die App musste aufgrund eines Fehlers beendet werden: {e}")

if __name__ == "__main__":
    main()