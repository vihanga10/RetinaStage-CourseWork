"""Conservative visual screen for the APTOS-style colour fundus upload flow.

This is a pattern check, not a trained retinal-image detector or a diagnosis.
It rejects common non-fundus uploads before they reach the DR classifier.
"""

from __future__ import annotations

import io

import numpy as np
from PIL import Image, UnidentifiedImageError


REJECTION = (
    "This image does not resemble an APTOS-style retinal fundus photograph. "
    "Choose a colour fundus photo with a visible retinal field and dark surround. "
    "Some valid photographs may also be rejected by this screening check."
)


def validate_fundus_upload(data: bytes) -> None:
    """Raise ValueError for unreadable, undersized, or obvious non-fundus images.

    Use the original uploaded pixels, before the P2 crop removes the field edge.
    Requiring a central reddish field and dark corners is intentional for the
    APTOS-style images used by the coursework; it is not a clinical guarantee.
    """

    try:
        with Image.open(io.BytesIO(data)) as image:
            if image.format not in {"JPEG", "PNG"} or getattr(image, "n_frames", 1) != 1:
                raise ValueError("Choose a single JPEG or PNG retinal photograph.")
            width, height = image.size
            if min(width, height) < 400 or max(width / height, height / width) > 2.2:
                raise ValueError("Choose a retinal photograph at least 400 pixels wide and high.")
            if width * height > 25_000_000:
                raise ValueError("Choose a retinal photograph below 25 megapixels.")
            rgb = np.asarray(image.convert("RGB").resize((256, 256)), dtype=np.float32)
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as exc:
        raise ValueError("The upload is not a readable JPEG or PNG image.") from exc

    rows, columns = np.mgrid[:256, :256]
    radius = np.sqrt(((columns - 127.5) / 127.5) ** 2 +
                     ((rows - 127.5) / 127.5) ** 2)
    centre = radius < 0.58
    corners = radius > 1.12
    luminance = (0.299 * rgb[:, :, 0] + 0.587 * rgb[:, :, 1]
                 + 0.114 * rgb[:, :, 2])
    centre_pixels = rgb[centre]
    centre_brightness = float(np.median(luminance[centre]))
    corner_brightness = float(np.median(luminance[corners]))
    # Compare the field with its own background instead of requiring a bright
    # absolute exposure. Some genuine colour fundus photos are quite dim.
    field_separation = centre_brightness - corner_brightness
    dark_corner_fraction = float(np.mean(
        luminance[corners] < 0.70 * max(centre_brightness, 20)
    ))
    red_over_green = float(np.median(centre_pixels[:, 0] - centre_pixels[:, 1]))
    red_over_blue = float(np.median(centre_pixels[:, 0] - centre_pixels[:, 2]))

    if (centre_brightness < 12
            or field_separation < max(9, 0.12 * centre_brightness)
            or dark_corner_fraction < 0.50
            or red_over_green < max(2, 0.03 * centre_brightness)
            or red_over_blue < max(4, 0.07 * centre_brightness)):
        raise ValueError(REJECTION)
