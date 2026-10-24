import tempfile
import unittest
from pathlib import Path

import av
import numpy as np

from ffmpeg import FFmpeg


class FFmpegCompatibilityTest(unittest.TestCase):
    def test_decodes_lossless_video_to_rgb_and_reaches_end(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "frames.mkv"
            expected = np.full((8, 8, 3), (16, 96, 224), dtype=np.uint8)
            with av.open(str(path), mode="w") as container:
                stream = container.add_stream("ffv1", rate=25)
                stream.width = 8
                stream.height = 8
                stream.pix_fmt = "bgr0"
                frame = av.VideoFrame.from_ndarray(expected, format="rgb24")
                for packet in stream.encode(frame):
                    container.mux(packet)
                for packet in stream.encode():
                    container.mux(packet)

            reader = FFmpeg()
            try:
                self.assertTrue(reader.open(str(path), loop=False))
                reader._videoFrames = reader._contents.decode(video=0)
                result, ended, skipped = reader.decode()
                self.assertFalse(ended)
                self.assertFalse(skipped)
                self.assertEqual(result.shape, (8, 8))
                np.testing.assert_array_equal(result.image, expected)
                self.assertTrue(reader.decode()[1])
            finally:
                reader.stop()


if __name__ == "__main__":
    unittest.main()
