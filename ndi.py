import time
from typing import Callable
from cyndilib import (
    Finder,
    Source,
    Receiver,
    RecvColorFormat,
    RecvBandwidth,
    VideoFrameSync
)
import numpy as np
from PIL import Image
from threading import Thread

class NDI:
    _instance = None
    _finder: Finder
    _source: Source | None = None
    _receiver: Receiver | None = None
    _frameSync: VideoFrameSync | None = None
    _decode: Thread | None = None
    _is_running: bool = True
    _callback: Callable[[np.ndarray, tuple[int, int]], None] | None = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __del__(self):
        print("Stop NDI")
        self.stop()
        if self._finder.is_open:
            print("Stop Finder")
            self._finder.close()
        print("Stopped Finder")

    def __init__(self) -> None:
        print("Start NDI")
        self._finder = Finder()
        self._finder.open()
        self.waitNDISourcesUpdate()
        self._finder.get_source_names()

    def waitNDISourcesUpdate(self):
        r = True
        while r:
            r = self._finder.wait_for_sources(timeout=1)

    def getNDISources(self) -> list[str]:
        result: list[str] = []
        self.waitNDISourcesUpdate()
        for name in self._finder.get_source_names():
            result.append(name)
        return result

    def setSource(self, name: str) -> bool:
        if not self._finder.is_open:
            self.waitNDISourcesUpdate()
        print(self._finder.num_sources)
        self._source = self._finder.get_source(name)
        print(self._source)
        return self._source != None

    def start(self, callback: Callable[[np.ndarray, tuple[int, int]], None]) -> bool:
        if self._source == None:
            return False
        if self._receiver != None and self._receiver.is_connected():
            self._receiver.disconnect()
        self._receiver = Receiver(
            color_format=RecvColorFormat.RGBX_RGBA,
            bandwidth=RecvBandwidth.highest,
        )
        self._frameSync = VideoFrameSync()
        self._receiver.frame_sync.set_video_frame(self._frameSync)
        self._receiver.set_source(self._source)
        i = 0
        while not self._receiver.is_connected():
            if i > 30:
                raise Exception("timeout waiting for connection")
            time.sleep(0.5)
            i += 1
        print("connected")
        self._callback = callback
        self._decode = Thread(target=self.decode)
        self._decode.run()
        return True

    def decode(self):
        while True:
            if (
                self._receiver != None
                and self._frameSync != None
                and self._callback != None
            ):
                break
            if not self._is_running:
                return
            time.sleep(0.1)
            continue
        if (
            self._receiver == None
            or self._frameSync == None
            or self._callback == None
        ):
            return
        while self._is_running:
            frame_rate = self._frameSync.get_frame_rate()
            print(f"FPS: {frame_rate}")
            wait = (1.0 / frame_rate)
            shape = self._frameSync.get_resolution()
            if min(shape) <= 0:
                time.sleep(0.1)
                self._receiver.frame_sync.capture_video()
                continue
            data = self._frameSync.get_array().reshape([shape[0], shape[1], 4])
            self._callback(data, shape)
            time.sleep(wait)
            self._receiver.frame_sync.capture_video()
            pass
        pass

    def stop(self):
        if self._decode != None and self._decode.is_alive():
            self._is_running = False
            try:
                self._decode.join(timeout=3)
            except TimeoutError:
                pass
        if self._receiver != None and self._receiver.is_connected():
            print("Stop Receiver")
            self._receiver.disconnect()
