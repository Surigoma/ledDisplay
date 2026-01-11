import json
from typing import Optional, TypedDict
from singleton import Singleton


class ConfigNDI(TypedDict):
    source: str


class ConfigFFmpeg(TypedDict):
    source: str


class ConfigBody(TypedDict):
    source: str
    ndi: Optional[ConfigNDI]
    ffmpeg: Optional[ConfigFFmpeg]


class Config(Singleton):
    _loaded = False
    config: ConfigBody

    def __init__(self) -> None:
        if not self._loaded:
            self.load_config()

    def load_config(self):
        with open("./config.json", "r", encoding="utf-8") as f:
            self.config = json.load(f)
        self._loaded = True
