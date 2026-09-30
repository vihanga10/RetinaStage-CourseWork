"""Loads only the checkpoint whose digest was recorded during Colab calibration."""

import base64
import hashlib
import io
import json
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

from guide import LABELS, review_rule
from preprocess import preprocess_png


def _png_url(rgb: np.ndarray) -> str:
    buffer = io.BytesIO()
    Image.fromarray(np.asarray(rgb, dtype=np.uint8), "RGB").save(buffer, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode("ascii")


class ModelService:
    def __init__(self, model_dir: Path):
        self.model_dir = model_dir
        self.model_path = model_dir / "selected_fine_model.keras"
        self.calibration_path = model_dir / "temperature_calibration.json"
        self._model = None
        self._feature_model = None
        self._head_layers = None
        self._temperature = None

    @property
    def ready(self) -> bool:
        return self.model_path.is_file() and self.calibration_path.is_file()

    def _load(self):
        if self._model is not None:
            return
        if not self.ready:
            raise RuntimeError("Colab model and calibration artifacts have not been installed.")
        import tensorflow as tf

        record = json.loads(self.calibration_path.read_text(encoding="utf-8"))
        digest = hashlib.sha256(self.model_path.read_bytes()).hexdigest()
        if digest != record["model_sha256"] or record["preprocessing"] != "P2":
            raise RuntimeError("Checkpoint or preprocessing does not match the calibration record.")
        temperature = float(record["temperature"])
        if not np.isfinite(temperature) or temperature <= 0:
            raise RuntimeError("Invalid calibration temperature.")
        model = tf.keras.models.load_model(self.model_path, compile=False)
        backbones = [layer for layer in model.layers
                     if isinstance(layer, tf.keras.Model)
                     and "efficientnet" in layer.name.lower()]
        if len(backbones) != 1:
            raise RuntimeError("The checkpoint is not the expected EfficientNet model.")
        backbone = backbones[0]
        features = tf.keras.Model(
            backbone.inputs,
            [backbone.get_layer("top_conv").output, backbone.output],
        )
        self._model = model
        self._feature_model = features
        self._head_layers = model.layers[model.layers.index(backbone) + 1:]
        self._temperature = temperature

    def _probabilities(self, rgb: np.ndarray) -> np.ndarray:
        from scipy.special import softmax
        raw = self._model.predict(rgb[None].astype(np.float32), verbose=0)[0]
        return softmax(np.log(np.clip(raw, 1e-7, 1.0)) / self._temperature).astype(float)

    def _heatmap(self, rgb: np.ndarray, grade: int) -> np.ndarray:
        import tensorflow as tf
        tensor = tf.convert_to_tensor(rgb[None], dtype=tf.float32)
        with tf.GradientTape() as tape:
            conv, features = self._feature_model(tensor, training=False)
            scores = features
            for layer in self._head_layers:
                scores = (layer(scores, training=False)
                          if isinstance(layer, tf.keras.layers.Dropout)
                          else layer(scores))
            target = scores[:, grade]
        gradient = tape.gradient(target, conv)
        if gradient is None:
            raise RuntimeError("Could not compute Grad-CAM for this checkpoint.")
        weights = tf.reduce_mean(gradient, axis=(1, 2), keepdims=True)
        heat = tf.nn.relu(tf.reduce_sum(weights * conv, axis=-1))[0].numpy()
        heat = cv2.resize(heat, (224, 224), interpolation=cv2.INTER_LINEAR)
        return heat / (float(heat.max()) + 1e-8)

    def analyze(self, raw_image: bytes) -> dict:
        self._load()
        rgb = preprocess_png(raw_image)
        probabilities = self._probabilities(rgb)
        grade = int(np.argmax(probabilities))
        heat = self._heatmap(rgb, grade)
        colour = cv2.cvtColor(cv2.applyColorMap(
            np.uint8(255 * heat), cv2.COLORMAP_JET), cv2.COLOR_BGR2RGB)
        overlay = np.uint8(0.6 * rgb + 0.4 * colour)
        blurred = cv2.GaussianBlur(rgb.astype(np.uint8), (5, 5), 1.0)
        blur_probabilities = self._probabilities(blurred)
        blur_grade = int(np.argmax(blur_probabilities))
        flagged, reasons = review_rule(probabilities.tolist())
        return {
            "grade": grade, "label": LABELS[grade],
            "confidence": float(probabilities[grade]),
            "probabilities": probabilities.tolist(),
            "review_required": flagged, "review_reasons": reasons,
            "processed_image": _png_url(rgb),
            "heatmap_overlay": _png_url(overlay),
            "blur_check": {
                "grade": blur_grade, "label": LABELS[blur_grade],
                "confidence": float(blur_probabilities[blur_grade]),
                "changed": blur_grade != grade,
            },
            "notice": "Research prototype only. Not a medical diagnosis.",
        }
