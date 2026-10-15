from threading import Event, Lock, Thread
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

    def __init__(self):
        self._callback = None
        self._thread = None
        self._is_running = False
        self._outputFrame = None
        self._reshape = (192, 108)
        self._frame_lock = Lock()
        self._frame_ready = Event()
        self._frame_version = 0
        self._processed_version = -1

    def _frameResample(self):
        print("Start frame Resample")
        while self._is_running:
            if not self._frame_ready.wait(timeout=0.1):
                continue
            self._frame_ready.clear()
            with self._frame_lock:
                if self._frame_version == self._processed_version:
                    frame = None
                else:
                    frame = self._outputFrame
                    self._processed_version = self._frame_version
            if frame is None:
                continue
            if frame.shape is None or min(frame.shape) <= 0:
                continue
            if self._callback is not None:
                self._callback(self.process(frame))

    def setResizeShape(self, shape: tuple[int, int]):
        self._reshape = shape

    def setup(self, config: ConfigOutput):
        self._reshape = config.canvas

    def start(self, callback: ImageCallback, framerate: float = 40.0) -> bool:
        self._is_running = True
        self._processed_version = -1
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
        self._frame_ready.set()
        try:
            self._thread.join(timeout=1.0)
        except TimeoutError:
            pass

    def update(self, image: ImageArgs):
        with self._frame_lock:
            self._outputFrame = image
            self._frame_version += 1
        self._frame_ready.set()

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
