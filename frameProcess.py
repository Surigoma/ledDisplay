from threading import Thread
import time
from typing import Optional
import numpy as np
from PIL import Image

from config import ConfigOutput
from input import ImageArgs, ImageCallback


class FrameProcessor:
    _callback: Optional[ImageCallback] = None
    _thread: Optional[Thread] = None
    _is_running: bool = True
    _outputFrame: Optional[ImageArgs] = None
    _framerate: float
    _reshape: tuple[int, int] = (192, 108)

    def _frameResample(self):
        print("Start frame Resample")
        while self._is_running:
            if self._outputFrame is None:
                time.sleep(0.01)
                continue
            if self._outputFrame.shape is None or min(self._outputFrame.shape) <= 0:
                time.sleep(1.0 / self._framerate)
                continue
            if self._callback is not None:
                self._callback(self.process(self._outputFrame))
            time.sleep(1.0 / self._framerate)

    def setResizeShape(self, shape: tuple[int, int]):
        self._reshape = shape

    def setup(self, config: ConfigOutput):
        self._reshape = config.canvas

    def start(self, callback: ImageCallback, framerate: float = 40.0) -> bool:
        self._framerate = framerate
        self._callback = callback
        self._thread = Thread(
            target=self._frameResample, name="FrameProcessor", daemon=True
        )
        self._thread.start()
        return True

    def stop(self):
        if not self._is_running or self._thread is None:
            return
        self._is_running = False
        try:
            self._thread.join(timeout=1.0)
        except TimeoutError:
            pass

    def update(self, image: ImageArgs):
        self._outputFrame = image

    def process(self, image: ImageArgs) -> ImageArgs:
        tmp = image
        tmp = self._resize(tmp, self._reshape)
        return tmp

    def _resize(self, image: ImageArgs, shape: tuple[int, int]) -> ImageArgs:
        if image.image is None:
            return ImageArgs()
        source = Image.fromarray(image.image)
        resized = source.resize(shape)
        return ImageArgs(np.array(resized), resized.size)
