import json
from config import ConfigLine, ConfigOutput, ConfigPixel, Point


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
            result.append((round(dx * percent), round(dy * percent)))
        return result

    def setup(self, config: ConfigOutput):
        for sample in config.sampler:
            points: list[Point]
            if sample.sampleType == "pixel":
                points = self._generatePoint(sample)
            elif sample.sampleType == "line":
                points = self._generateLine(sample)
            else:
                continue
            self._samplePoint.extend(points)
        print(json.dumps(self._samplePoint))
