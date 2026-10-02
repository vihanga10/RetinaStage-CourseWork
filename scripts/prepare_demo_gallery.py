"""Export ten labelled APTOS training images for a local-only website gallery.

The source must be the final notebook's split_manifest.csv and train_images/.
The ZIP is installed locally under web/public/ and is intentionally not in Git.
"""

from __future__ import annotations

import argparse
import csv
import io
import json
from collections import defaultdict
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

import numpy as np
from PIL import Image


def suitable_for_gallery(raw: bytes) -> bool:
    """Match the application's simple fundus screen before offering an example."""
    try:
        with Image.open(io.BytesIO(raw)) as image:
            if image.format != "PNG" or getattr(image, "n_frames", 1) != 1:
                return False
            width, height = image.size
            if (min(width, height) < 400 or width * height > 25_000_000
                    or max(width / height, height / width) > 2.2):
                return False
            rgb = np.asarray(image.convert("RGB").resize((256, 256)), dtype=np.float32)
    except (ValueError, OSError):
        return False
    rows, columns = np.mgrid[:256, :256]
    radius = np.sqrt(((columns - 127.5) / 127.5) ** 2 +
                     ((rows - 127.5) / 127.5) ** 2)
    centre, corners = radius < 0.58, radius > 1.12
    luminance = 0.299 * rgb[:, :, 0] + 0.587 * rgb[:, :, 1] + 0.114 * rgb[:, :, 2]
    field = float(np.median(luminance[centre]))
    background = float(np.median(luminance[corners]))
    warm = rgb[centre]
    return (field >= 12 and field - background >= max(9, 0.12 * field)
            and float(np.mean(luminance[corners] < 0.70 * max(field, 20))) >= 0.50
            and float(np.median(warm[:, 0] - warm[:, 1])) >= max(2, 0.03 * field)
            and float(np.median(warm[:, 0] - warm[:, 2])) >= max(4, 0.07 * field))


def prepare_gallery(manifest: Path, image_dir: Path, output: Path) -> list[dict]:
    by_grade: dict[int, list[str]] = defaultdict(list)
    with manifest.open(newline="", encoding="utf-8") as source:
        for row in csv.DictReader(source):
            if row["split"] == "train":
                grade = int(row["diagnosis"])
                if grade not in range(5) or not row["id_code"].isalnum():
                    raise ValueError("Unexpected grade or image ID in split manifest.")
                by_grade[grade].append(row["id_code"])

    selected: list[tuple[str, int, bytes]] = []
    for grade in range(5):
        for image_id in sorted(set(by_grade[grade])):
            path = image_dir / f"{image_id}.png"
            if not path.is_file() or path.stat().st_size > 10 * 1024 * 1024:
                continue
            raw = path.read_bytes()
            if not suitable_for_gallery(raw):
                continue
            selected.append((image_id, grade, raw))
            if sum(item[1] == grade for item in selected) == 2:
                break
        if sum(item[1] == grade for item in selected) != 2:
            raise ValueError(f"Fewer than two suitable training images found for Grade {grade}.")

    images = [{"id_code": image_id, "diagnosis": grade} for image_id, grade, _ in selected]
    output.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(output, "w", ZIP_DEFLATED, compresslevel=5) as archive:
        archive.writestr("demo_examples/manifest.json", json.dumps({
            "source": "APTOS 2019", "split": "train", "images": images,
        }, indent=2) + "\n")
        for image_id, _, raw in selected:
            archive.writestr(f"demo_examples/{image_id}.png", raw)
    return images


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--images", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("demo_examples.zip"))
    args = parser.parse_args()
    rows = prepare_gallery(args.manifest, args.images, args.output)
    print(f"Saved {len(rows)} training examples (two per grade) to {args.output}")
