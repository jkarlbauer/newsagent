import json


class _Config:
    def _load(self):
        with open("config.json") as f:
            return json.load(f)

    def __getitem__(self, key):
        return self._load()[key]

    def __iter__(self):
        return iter(self._load())

    def keys(self):
        return self._load().keys()

    def get(self, key, default=None):
        return self._load().get(key, default)


config = _Config()
