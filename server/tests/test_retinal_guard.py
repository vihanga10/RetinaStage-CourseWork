"""Check obvious upload rejections and the documented APTOS-style pattern.

The constructed pattern is a software fixture, not a clinical validation set.
"""

import io
import sys
import unittest
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from retinal_guard import validate_fundus_upload


def png(pixels: np.ndarray) -> bytes:
    output = io.BytesIO()
    Image.fromarray(pixels, "RGB").save(output, format="PNG")
    return output.getvalue()


class RetinalGuardTests(unittest.TestCase):
    def test_central_reddish_field_with_dark_surround_passes(self):
        rows, columns = np.mgrid[:512, :512]
        radius = np.sqrt((rows - 256) ** 2 + (columns - 256) ** 2)
        pixels = np.zeros((512, 512, 3), dtype=np.uint8)
        pixels[radius < 230] = [180, 105, 62]
        validate_fundus_upload(png(pixels))

    def test_dim_colour_field_with_dark_surround_passes(self):
        rows, columns = np.mgrid[:512, :512]
        radius = np.sqrt((rows - 256) ** 2 + (columns - 256) ** 2)
        pixels = np.zeros((512, 512, 3), dtype=np.uint8)
        pixels[radius < 230] = [35, 20, 12]
        validate_fundus_upload(png(pixels))

    def test_ordinary_full_frame_photo_pattern_is_rejected(self):
        pixels = np.full((512, 512, 3), [166, 115, 72], dtype=np.uint8)
        with self.assertRaisesRegex(ValueError, "does not resemble"):
            validate_fundus_upload(png(pixels))

    def test_invalid_and_small_images_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "readable"):
            validate_fundus_upload(b"not an image")
        with self.assertRaisesRegex(ValueError, "400 pixels"):
            validate_fundus_upload(png(np.zeros((200, 200, 3), dtype=np.uint8)))


if __name__ == "__main__":
    unittest.main()
