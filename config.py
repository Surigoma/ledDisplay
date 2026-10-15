import json
from typing import Literal, Optional, TypeAlias, Union

from pydantic import BaseModel, model_validator
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


class ConfigSampler(BaseModel):
    universe: Optional[int] = None
    channel: Optional[int] = None

    @model_validator(mode="after")
    def validate_output_position(self):
        if (self.universe is None) != (self.channel is None):
            raise ValueError("universe and channel must be specified together")
        if self.universe is not None and not 0 <= self.universe <= 32767:
            raise ValueError("universe must be between 0 and 32767")
        if self.channel is not None and not 1 <= self.channel <= 512:
            raise ValueError("channel must be between 1 and 512")
        return self


class ConfigPixel(ConfigSampler):
    sampleType: Literal["pixel"]
    point: Point


class ConfigLine(ConfigSampler):
    sampleType: Literal["line"]
    start: Point
    end: Point
    count: int


class ConfigDummy(ConfigSampler):
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
