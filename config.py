import json
from typing import TypedDict


class ConfigBody(TypedDict):
    source: str


class Config:
    _instance = None
    _loaded = False
    config: ConfigBody

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if not self._loaded:
            self.load_config()

    def load_config(self):
        with open("./config.json", "r", encoding="utf-8") as f:
            self.config = json.load(f)
        self._loaded = True
