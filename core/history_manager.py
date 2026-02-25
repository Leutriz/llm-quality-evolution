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

    durations = [r['metrics']['duration'] for r in results_data if 'metrics' in r]
    avg_duration = round(sum(durations) / len(durations), 1) if durations else 0

    tps_list = [r['metrics']['tps'] for r in results_data if 'metrics' in r]
    avg_tps = round(sum(tps_list) / len(tps_list), 1) if tps_list else 0

    resp_len = [r['metrics']['response_length'] for r in results_data if 'metrics' in r]
    avg_resp_len = round(sum(resp_len) / len(resp_len), 1) if resp_len else 0

    new_run = {
        "id": datetime.now().strftime("%Y%m%d_%H%M%S"),
        "timestamp": datetime.now().strftime("%H:%M - %d.%m.%y"),
        "model": model,
        "datasets": datasets,
        "avg_score": avg_score,
        "avg_duration": avg_duration,
        "avg_tps": avg_tps,
        "avg_response_length": avg_resp_len,
        "details": results_data
    }
    
    history.insert(0, new_run)
    os.makedirs("config", exist_ok=True)
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=4)
    return new_run