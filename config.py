import json
from typing import Literal, Optional, TypeAlias, Union

from pydantic import BaseModel
from singleton import Singleton

Point: TypeAlias = tuple[int, int]


class ConfigNDI(BaseModel):
    source: str


class ConfigFFmpeg(BaseModel):
    source: str
    loop: bool = True


class ConfigInput(BaseModel):
    source: str
    ndi: Optional[ConfigNDI]
    ffmpeg: Optional[ConfigFFmpeg]


class ConfigPixel(BaseModel):
    sampleType: Literal["pixel"]
    point: Point


class ConfigLine(BaseModel):
    sampleType: Literal["line"]
    start: Point
    end: Point
    count: int


class ConfigDummy(BaseModel):
    sampleType: Literal["dummy"]
    count: int


class ConfigOutputMapping(BaseModel):
    strict: Optional[bool] = True
    fillEnd: Optional[bool] = True


class ConfigOutput(BaseModel):
    sampler: list[Union[ConfigPixel, ConfigLine, ConfigDummy]]
    fps: float
    canvas: tuple[int, int] = (192, 108)
    address: str
    mapping: Optional[ConfigOutputMapping] = ConfigOutputMapping()


class ConfigBody(BaseModel):
    input: ConfigInput
    output: ConfigOutput


class Config(Singleton):
    _loaded = False
    config: ConfigBody

    def __init__(self) -> None:
        if not self._loaded:
            self.load_config()

    def get(self) -> ConfigBody:
        if not self._loaded:
            self.load_config()
        return self.config

    def save(self):
        if not self._loaded:
            return
        with open("./config.json", "w", encoding="utf-8") as f:
            json.dump(self.config, f)

    def load_config(self):
        with open("./config.json", "r", encoding="utf-8") as f:
            self.config = ConfigBody.model_validate(json.load(f))
        self._loaded = True
