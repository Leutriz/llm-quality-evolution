import json
import os
from datetime import datetime

HISTORY_FILE = "config/history.json"

def load_all_runs():
    if not os.path.exists(HISTORY_FILE):
        return []
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

def save_run(model, datasets, results_data):
    history = load_all_runs()
    
    scores = [r['score'] for r in results_data]
    avg_score = round(sum(scores) / len(scores), 1) if scores else 0
    
    new_run = {
        "id": datetime.now().strftime("%Y%m%d_%H%M%S"),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "model": model,
        "datasets": datasets,
        "avg_score": avg_score,
        "details": results_data
    }
    
    history.insert(0, new_run)
    os.makedirs("config", exist_ok=True)
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=4)
    return new_run