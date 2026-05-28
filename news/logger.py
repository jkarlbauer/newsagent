import json
import os
from datetime import datetime

LOGS_DIR = "logs"


def save_run(chat_id: int, articles: list, selected_urls: set) -> None:
    user_dir = os.path.join(LOGS_DIR, str(chat_id))
    os.makedirs(user_dir, exist_ok=True)
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(user_dir, f"{timestamp}.json")
    data = [
        {
            "title": a.title,
            "topic": a.topic,
            "url": a.url,
            "score": round(float(a.score), 4),
            "coverage": round(float(a.coverage), 4),
            "embedding": a.embedding.tolist(),
            "selected": a.url in selected_urls,
        }
        for a in articles
    ]
    with open(path, "w") as f:
        json.dump(data, f)
    _prune(user_dir)


def _prune(user_dir: str, keep: int = 30) -> None:
    files = sorted(f for f in os.listdir(user_dir) if f.endswith(".json") and not f.endswith("_raw.json"))
    for old in files[:-keep]:
        os.remove(os.path.join(user_dir, old))
