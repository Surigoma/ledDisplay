from threading import Thread
import time
from datetime import datetime, timedelta
from typing import Callable, TypeAlias

import numpy as np
from singleton import Singleton

ImageArgs: TypeAlias = tuple[np.ndarray | None, tuple[int, int] | None]
ImageCallback: TypeAlias = Callable[[ImageArgs], None]
DecodeResult: TypeAlias = tuple[ImageArgs, bool]


class Input(Singleton):
    _callback: ImageCallback | None = None
    _thread: Thread | None = None
    _fps: float = 30.0
    _is_running: bool = True

    def start(self, callback: ImageCallback):
        self._callback = callback
        self._thread = Thread(target=self._decode)
        self._thread.run()

    def decode(self) -> DecodeResult:
        pass

    def _decode(self):
        priv = datetime.now()
        while self._is_running:
            image, isEnd = self.decode()
            if isEnd:
                break
            if self._callback is not None:
                if image[0] is not None and image[1] is not None:
                    self._callback(image[0], image[1])
            if float(self._fps) != 0:
                nextTime = (
                    priv + timedelta(seconds=1.0 / float(self._fps))
                ) - datetime.now()
                time.sleep(nextTime.total_seconds())
                priv = datetime.now()
            else:
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
