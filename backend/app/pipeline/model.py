"""Slot model ONNX (IndoBERTweet). Selama file model belum ada, pipeline jalan tanpa model.

Struktur yang diharapkan per model (hasil export, mis. `optimum-cli export onnx`):
    ml/models/<nama>/model.onnx, config.json (id2label), file tokenizer,
    calibration.json {"threshold": x}  (wajib untuk model krisis: dikalibrasi recall ≥ 0,95)
"""

import json
import logging
from pathlib import Path
from typing import Any, Protocol

import numpy as np

from app.settings import ROOT

MODELS_DIR = ROOT / "ml" / "models"
log = logging.getLogger(__name__)


class Classifier(Protocol):
    threshold: float

    def predict(self, text: str) -> dict[str, float]: ...


class OnnxClassifier:
    """Klasifikasi multi-label: sigmoid per label. Sinkron & CPU-bound, panggil via to_thread."""

    # Any: objek pihak ketiga (tokenizer transformers, InferenceSession onnxruntime).
    def __init__(  # noqa: ANN401
        self, tokenizer: Any, session: Any, labels: list[str], threshold: float  # noqa: ANN401
    ) -> None:
        self.tokenizer = tokenizer
        self.session = session
        self.labels = labels
        self.threshold = threshold
        self._inputs = {i.name for i in session.get_inputs()}

    def predict(self, text: str) -> dict[str, float]:
        enc = self.tokenizer(text, truncation=True, max_length=128, return_tensors="np")
        logits = self.session.run(None, {k: v for k, v in enc.items() if k in self._inputs})[0][0]
        probs = 1 / (1 + np.exp(-np.asarray(logits, dtype=np.float64)))
        return {label: float(p) for label, p in zip(self.labels, probs, strict=True)}

    @classmethod
    def from_dir(cls, path: Path) -> "OnnxClassifier":
        import onnxruntime as ort  # impor berat; hanya saat model benar-benar ada
        from transformers import AutoTokenizer

        cfg = json.loads((path / "config.json").read_text("utf-8"))
        labels = [cfg["id2label"][str(i)] for i in range(len(cfg["id2label"]))]
        calibration = path / "calibration.json"
        threshold = (
            json.loads(calibration.read_text("utf-8"))["threshold"] if calibration.exists() else 0.5
        )
        session = ort.InferenceSession(str(path / "model.onnx"), providers=["CPUExecutionProvider"])
        return cls(AutoTokenizer.from_pretrained(path), session, labels, threshold)


def load(name: str) -> Classifier | None:
    """Muat model kalau ada. Gagal muat = None + log; leksikon tetap jalan (§6.2)."""
    path = MODELS_DIR / name
    if not (path / "model.onnx").exists():
        return None
    if name == "crisis" and not (path / "calibration.json").exists():
        log.error("model_not_loaded name=crisis reason=missing_calibration")
        return None
    try:
        return OnnxClassifier.from_dir(path)
    except Exception as e:  # noqa: BLE001 — model rusak tidak boleh menjatuhkan bot
        log.error("model_not_loaded name=%s error=%s", name, type(e).__name__)
        return None
