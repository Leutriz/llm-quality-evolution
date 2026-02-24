import questionary
from core.config_loader import ConfigLoader
import os

class Launcher:
    def __init__(self):
        self.config = ConfigLoader()

    def run(self):
        """Startet den interaktiven Auswahl-Prozess."""
        print(f"\n--- {self.config.get_app_settings().get('name')} - v{self.config.get_app_settings().get('version')} ---")

        # 1. Modellauswahl aus der Config
        ollama_cfg = self.config.get_ollama_config()
        model_names = [m['name'] for m in ollama_cfg.get('models', [])]
        
        if not model_names:
            print("❌ Keine Modelle in der config.yaml gefunden!")
            return None

        selected_model = questionary.select(
            "Welches Modell möchtest du testen?",
            choices=model_names,
            use_indicator=True
        ).ask()

        # 2. Dataset-Auswahl (Multi-Select)
        dataset_files = [f for f in os.listdir('datasets') if f.endswith('.json')]
        
        if not dataset_files:
            print("❌ Keine Datasets im Ordner /datasets gefunden!")
            return None

        selected_datasets = questionary.checkbox(
            "Welche Datasets sollen in den Testlauf? (Leertaste zum Wählen)",
            choices=dataset_files
        ).ask()

        if not selected_datasets:
            print("⚠️ Kein Dataset ausgewählt. Abbruch.")
            return None

        return {
            "model": selected_model,
            "datasets": selected_datasets
        }