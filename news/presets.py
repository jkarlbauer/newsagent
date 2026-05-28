import json

with open("presets.json") as f:
    TOPIC_PRESETS: dict = json.load(f)
