from typing import Iterator, Optional
import av
from av.container import InputContainer

from input import DecodeResult, ImageArgs, ImageCallback, Input


class FFmpeg(Input):
    _contents: Optional[InputContainer] = None
    _videoFrames: Optional[Iterator[av.VideoFrame]] = None
    _stream: int = 0
    _loop: bool = True

    def open(self, path: str, stream: int = 0, loop: bool = True) -> bool:
        self._contents = av.open(
            path, container_options={"-stream_loop": "-1", "-fflags": "+genpts"}
        )
        self._stream = stream
        self._loop = loop
        return True

    def start(self, callback: ImageCallback) -> bool:
        if self._contents is None:
            return False
        self._videoFrames = self._contents.decode(video=self._stream)
        timeBase = self._contents.streams[self._stream].time_base
        if timeBase is not None:
            self._fps = 1 / timeBase / 1000
        super().start(callback)
        return True

    def decode(self) -> DecodeResult:
        if self._contents is None or self._videoFrames is None:
            return (ImageArgs(), True, False)
        frame: av.VideoFrame
        try:
            frame = next(self._videoFrames)
            return (
                ImageArgs(
                    frame.to_rgb().to_ndarray(),
                    (frame.width, frame.height),
                ),
                False,
                False,
            )
        except StopIteration:
            if self._loop:
                self._contents.seek(0)
                self._videoFrames = self._contents.decode(self._stream)
                return (ImageArgs(), False, True)
        return (ImageArgs(), True, False)

    def stop(self):
        super().stop()
        if self._contents is not None:
            print("Stop FFmpeg")
            self._contents.close()
