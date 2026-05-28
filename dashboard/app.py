import json
import os

from flask import Flask, render_template, abort

from news.plotter import generate_plot

app = Flask(__name__)
LOGS_DIR = "logs"


def _list_runs() -> list[dict]:
    runs = []
    if not os.path.exists(LOGS_DIR):
        return runs
    for chat_id in sorted(os.listdir(LOGS_DIR)):
        user_dir = os.path.join(LOGS_DIR, chat_id)
        for filename in sorted(os.listdir(user_dir), reverse=True):
            if filename.endswith(".json"):
                runs.append({
                    "chat_id": chat_id,
                    "filename": filename,
                    "label": filename[:-5].replace("_", " "),
                })
    return runs


@app.route("/")
def index():
    return render_template("index.html", runs=_list_runs())


@app.route("/plot/<chat_id>/<filename>")
def plot(chat_id, filename):
    path = os.path.join(LOGS_DIR, chat_id, filename)
    if not os.path.exists(path):
        abort(404)
    with open(path) as f:
        articles = json.load(f)
    title = f"User {chat_id} — {filename[:-5].replace('_', ' ')}"
    return generate_plot(articles, title=title)
