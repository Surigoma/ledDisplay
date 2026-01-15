import json

import numpy as np
from config import ConfigDummy, ConfigLine, ConfigOutput, ConfigPixel, Point
from input import ImageArgs


class ImageSampler:
    _samplePoint: list[Point] = []

    def _generatePoint(self, config: ConfigPixel) -> list[Point]:
        return [config.point]

    def _generateLine(self, config: ConfigLine) -> list[Point]:
        result: list[Point] = []
        dx = config.end[0] - config.start[0]
        dy = config.end[1] - config.start[1]
        for i in range(config.count):
            percent = float(i / (config.count - 1))
            result.append(
                (
                    round(dx * percent) + config.start[0],
                    round(dy * percent) + config.start[1],
                )
            )
        return result

    def _generateDummy(self, config: ConfigDummy) -> list[Point]:
        return [(-1, -1)] * config.count

    def sampleLen(self):
        return len(self._samplePoint)

    def setup(self, config: ConfigOutput):
        for sample in config.sampler:
            points: list[Point]
            if sample.sampleType == "pixel":
                points = self._generatePoint(sample)
            elif sample.sampleType == "line":
                points = self._generateLine(sample)
            elif sample.sampleType == "dummy":
                points = self._generateDummy(sample)
            else:
                continue
            self._samplePoint.extend(points)
        print(json.dumps(self._samplePoint))

    def sample(self, image: ImageArgs):
        result: list[tuple[int, int, int]] = [(0, 0, 0)] * len(self._samplePoint)
        if image.image is None:
            return result
        for i, point in enumerate(self._samplePoint):
            if point[0] < 0 or point[1] < 0:
                result[i] = (0, 0, 0)
            result[i] = image.image[point[1], point[0]][:3]
        return result
