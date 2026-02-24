import yaml
import os

class ConfigLoader:
    def __init__(self, config_path="config/config.yaml"):
        self.config_path = config_path
        self.config = self._load_yaml()

    def _load_yaml(self):
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Konfigurationsdatei nicht gefunden: {self.config_path}")
        
        with open(self.config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def get_ollama_config(self):
        return self.config.get('providers', {}).get('ollama', {})

    def get_model_metadata(self, model_name):
        """Sucht technische Eckdaten für ein spezifisches Modell."""
        models = self.get_ollama_config().get('models', [])
        for m in models:
            if m['name'] == model_name:
                return m
        return {}

    def get_app_settings(self):
        return self.config.get('app', {})