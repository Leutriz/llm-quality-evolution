import requests
import time
from .base import BaseAdapter

class OllamaAdapter(BaseAdapter):
    def __init__(self, model_name, host="http://localhost:11434"):
        self.model_name = model_name
        self.url = f"{host}/api/chat"

    def send(self, prompt: str) -> dict:
        payload = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False
        }

        start_time = time.time()
        try:
            response = requests.post(self.url, json=payload, timeout=60)
            response.raise_for_status()
            end_time = time.time()
            
            data = response.json()
            
            duration_total = end_time - start_time
            eval_count = data.get("eval_count", 0) 
            tps = eval_count / (data.get("eval_duration", 1) / 1e9) if eval_count > 0 else 0

            return {
                "response": data["message"]["content"],
                "metrics": {
                    "duration": round(duration_total, 2),
                    "tps": round(tps, 2),
                    "token_count": eval_count
                }
            }
        except Exception as e:
            return {"error": str(e)}