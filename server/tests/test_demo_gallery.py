"""Verify the optional gallery exports only ten eligible training examples."""

import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile

import numpy as np
from PIL import Image

root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(root / "scripts"))
sys.path.insert(0, str(root / "server"))
from prepare_demo_gallery import prepare_gallery
from retinal_guard import validate_fundus_upload


class DemoGalleryTests(unittest.TestCase):
    def test_only_two_per_grade_from_train_split(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            photos = folder / "train_images"
            photos.mkdir()
            rows, columns = np.mgrid[:512, :512]
            image = np.zeros((512, 512, 3), dtype=np.uint8)
            image[(rows - 256) ** 2 + (columns - 256) ** 2 < 230 ** 2] = [100, 55, 30]
            records = []
            for grade in range(5):
                for index in range(2):
                    image_id = f"example{grade}{index}"
                    Image.fromarray(image, "RGB").save(photos / f"{image_id}.png")
                    records.append((image_id, grade, "train"))
            Image.fromarray(image, "RGB").save(photos / "aaaavalidation.png")
            records.append(("aaaavalidation", 0, "validation"))
            manifest = folder / "split_manifest.csv"
            with manifest.open("w", newline="") as output:
                writer = csv.writer(output)
                writer.writerow(["id_code", "diagnosis", "split"])
                writer.writerows(records)
            archive = folder / "demo_examples.zip"
            selected = prepare_gallery(manifest, photos, archive)
            self.assertEqual(len(selected), 10)
            self.assertNotIn("aaaavalidation", [item["id_code"] for item in selected])
            with ZipFile(archive) as z:
                listing = json.loads(z.read("demo_examples/manifest.json"))
                self.assertEqual(listing["images"], selected)
                for item in selected:
                    validate_fundus_upload(z.read(f"demo_examples/{item['id_code']}.png"))


if __name__ == "__main__":
    unittest.main()
