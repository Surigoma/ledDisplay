from typing import Iterator, Optional
import av
from av.container import InputContainer
from pathlib import Path

from input import ImageCallback, Input


class FFmpeg(Input):
    _contents: Optional[InputContainer] = None
    _videoFrames: Optional[Iterator[av.VideoFrame]] = None
    _stream: int = 0

    def open(self, path: Path, stream: int = 0):
        self._contents = av.open(path)
        self._stream = stream

    def start(self, callback: ImageCallback):
        if self._contents is None:
            return
        self._videoFrames = self._contents.decode(video=self._stream)
        super().start(callback)

    def decode(self):
        if self._videoFrames is None:
            return ((None, None), True)
        frame = next(self._videoFrames)
        self._fps = 1.0 / float(frame.duration)
        return ((frame.to_ndarray(), (frame.width, frame.height)), False)

    pass
