import time
from typing import Optional
from cyndilib import (
    Finder,
    Source,
    Receiver,
    RecvColorFormat,
    RecvBandwidth,
    VideoFrameSync,
)

from input import DecodeResult, ImageArgs, ImageCallback, Input


class NDI(Input):
    _finder: Finder
    _source: Optional[Source] = None
    _receiver: Optional[Receiver] = None
    _frameSync: Optional[VideoFrameSync] = None

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
        return self._source is not None

    def start(self, callback: ImageCallback) -> bool:
        if self._source is None:
            return False
        if self._receiver is not None and self._receiver.is_connected():
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
        print("Wait first frame")
        while self._receiver.is_connected():
            self._receiver.frame_sync.capture_video()
            shape = self._frameSync.get_resolution()
            if min(shape) > 0:
                break
            time.sleep(0.1)
        super().start(callback)
        return True

    def decode(self) -> DecodeResult:
        if self._frameSync is None or self._receiver is None:
            return (ImageArgs(), False, False)
        try:
            self._fps = self._frameSync.get_frame_rate()
        except ZeroDivisionError:
            return (ImageArgs(), False, True)
        shape = self._frameSync.get_resolution()
        self._receiver.frame_sync.capture_video()
        if min(shape) <= 0:
            time.sleep(0.1)
            return (ImageArgs(), False, True)
        data = self._frameSync.get_array()
        try:
            data = data.reshape([shape[1], shape[0], 4])
        except ValueError:
            return (ImageArgs(), False, True)
        return (ImageArgs(data, shape), False, False)

    def stop(self):
        super().stop()
        if self._receiver is not None:
            if self._receiver.is_connected():
                self._receiver.disconnect()
        if self._finder is not None:
            self._finder.close()
            print("Stop Receiver")
