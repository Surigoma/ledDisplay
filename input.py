from fractions import Fraction
from threading import Thread
import time
from datetime import datetime, timedelta
from typing import Callable, Optional, TypeAlias
from io import BytesIO

import numpy as np
from singleton import Singleton

class ImageArgs:
    image: Optional[np.ndarray]
    shape: Optional[tuple[int, int]]
    def __init__(self, image: Optional[np.ndarray] = None, shape: Optional[tuple[int, int]] = None) -> None:
        self.image = image
        self.shape = shape
        pass

# ImageArgs: TypeAlias = tuple[np.ndarray | None, tuple[int, int] | None]
ImageCallback: TypeAlias = Callable[[ImageArgs], None]
DecodeResult: TypeAlias = tuple[ImageArgs, bool, bool] # Image, isEnd, skipWait


class Input(Singleton):
    _thread: Thread | None = None
    _fps: Fraction = Fraction(30, 1)
    _is_running: bool = True

    def start(self, callback: ImageCallback) -> bool:
        self._callback = callback
        self._thread = Thread(target=self._decode)
        self._thread.start()
        return True

    def decode(self) -> DecodeResult:
        return (ImageArgs(), False, False)

    def _decode(self):
        priv = datetime.now()
        while self._is_running:
            image, isEnd, isSkip = self.decode()
            if isEnd:
                break
            if not isSkip:
                if self._callback is not None:
                    if image is not None:
                        self._callback(image)
                if float(self._fps) != 0:
                    nextTime = (
                        priv + timedelta(seconds=float(1.0 / self._fps))
                    ) - datetime.now()
                    time.sleep(nextTime.total_seconds())
                    priv = datetime.now()
            else:
                print("Skip")
                time.sleep(0.01)

    def stop(self):
        print("Stop input")
        if self._thread is None:
            return
        self._is_running = False
        if not self._thread.is_alive():
            return
        try:
            self._thread.join(timeout=3.0)
        except TimeoutError:
            pass
