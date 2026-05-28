import json
import os
import numpy as np
from datetime import datetime

from news.models import Article

LOGS_DIR = "logs"
_KEEP = 30


def save_embedded(chat_id: int, articles: list) -> str:
    user_dir = os.path.join(LOGS_DIR, str(chat_id))
    os.makedirs(user_dir, exist_ok=True)
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(user_dir, f"{timestamp}_raw.json")
    data = [
        {
            "title": a.title,
            "content": a.content,
            "topic": a.topic,
            "url": a.url,
            "embedding": a.embedding.tolist(),
        }
        for a in articles
    ]
    with open(path, "w") as f:
        json.dump(data, f)
    _prune(user_dir)
    return path


def load_embedded(path: str) -> list:
    with open(path) as f:
        data = json.load(f)
    return [
        Article(
            title=d["title"],
            content=d["content"],
            topic=d["topic"],
            url=d["url"],
            embedding=np.array(d["embedding"], dtype=np.float32),
        )
        for d in data
    ]


def _prune(user_dir: str) -> None:
    files = sorted(f for f in os.listdir(user_dir) if f.endswith("_raw.json"))
    for old in files[:-_KEEP]:
        os.remove(os.path.join(user_dir, old))
