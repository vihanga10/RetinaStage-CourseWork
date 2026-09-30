"""Exact P2 image operations from the final Colab notebook, cell 38."""

import cv2
import numpy as np

IMAGE_SIZE = 224


def retinal_crop(image_bgr: np.ndarray) -> np.ndarray:
    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    foreground = np.uint8(gray > 10) * 255
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))
    foreground = cv2.morphologyEx(
        foreground, cv2.MORPH_CLOSE, kernel, iterations=2
    )
    contours, _ = cv2.findContours(
        foreground, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )
    if not contours:
        return image_bgr.copy()
    x, y, width, height = cv2.boundingRect(max(contours, key=cv2.contourArea))
    margin = round(0.02 * max(width, height))
    x0, y0 = max(0, x - margin), max(0, y - margin)
    x1 = min(image_bgr.shape[1], x + width + margin)
    y1 = min(image_bgr.shape[0], y + height + margin)
    return image_bgr[y0:y1, x0:x1].copy()


def pad_and_resize(image_bgr: np.ndarray) -> np.ndarray:
    height, width = image_bgr.shape[:2]
    side = max(height, width)
    canvas = np.zeros((side, side, 3), dtype=np.uint8)
    top, left = (side - height) // 2, (side - width) // 2
    canvas[top:top + height, left:left + width] = image_bgr
    interpolation = cv2.INTER_AREA if side > IMAGE_SIZE else cv2.INTER_CUBIC
    return cv2.resize(canvas, (IMAGE_SIZE, IMAGE_SIZE), interpolation=interpolation)


def preprocess_png(data: bytes) -> np.ndarray:
    original = cv2.imdecode(np.frombuffer(data, dtype=np.uint8), cv2.IMREAD_COLOR)
    if original is None or original.ndim != 3:
        raise ValueError("The upload is not a readable image.")
    result = pad_and_resize(retinal_crop(original))
    lab = cv2.cvtColor(result, cv2.COLOR_BGR2LAB)
    lightness, channel_a, channel_b = cv2.split(lab)
    improved = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(lightness)
    result = cv2.cvtColor(
        cv2.merge((improved, channel_a, channel_b)), cv2.COLOR_LAB2BGR
    )
    blurred = cv2.GaussianBlur(result, (0, 0), sigmaX=1.0)
    result = cv2.addWeighted(result, 1.5, blurred, -0.5, 0)
    return cv2.cvtColor(result, cv2.COLOR_BGR2RGB).astype(np.float32)
