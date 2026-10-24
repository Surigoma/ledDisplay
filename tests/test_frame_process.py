import unittest

import numpy as np

from frameProcess import FrameProcessor
from input import ImageArgs


class FrameProcessorCompatibilityTest(unittest.TestCase):
    def test_rgb_frame_survives_pillow_resize(self):
        source = np.full((6, 8, 3), (16, 96, 224), dtype=np.uint8)
        processor = FrameProcessor()
        processor.setResizeShape((4, 3))

        result = processor.process(ImageArgs(source, (8, 6)))

        self.assertEqual(result.shape, (4, 3))
        self.assertEqual(result.image.shape, (3, 4, 3))
        np.testing.assert_array_equal(
            result.image, np.full((3, 4, 3), (16, 96, 224), dtype=np.uint8)
        )
        np.testing.assert_array_equal(source[0, 0], (16, 96, 224))

    def test_missing_frame_remains_empty(self):
        result = FrameProcessor().process(ImageArgs())

        self.assertIsNone(result.image)
        self.assertIsNone(result.shape)


if __name__ == "__main__":
    unittest.main()
