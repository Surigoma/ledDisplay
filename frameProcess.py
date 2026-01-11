from typing import Optional
import numpy as np
from PIL import Image

from input import ImageArgs, ImageCallback


class FrameProcessor:
    _callback: Optional[ImageCallback] = None

    def setCallback(self, callback: ImageCallback):
        self._callback = callback
        pass

    def process(self, image: ImageArgs):
        pass

    def resize(self, image: ImageArgs, shape: tuple[int, int]) -> ImageArgs:
        source = Image.fromarray(image)
        resized = source.resize(shape)
        return (np.array(resized), resized.size)
