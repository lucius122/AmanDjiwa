"""Klasifikasi emosi 6 label (skor 0–1). Model ONNX bila ada; selain itu skor kata kunci."""

import asyncio
import logging
from dataclasses import dataclass

import yaml

from app.models import Emotion
from app.pipeline.model import Classifier
from app.pipeline.normalize import Normalized, compile_pattern
from app.settings import CONFIG_DIR

log = logging.getLogger(__name__)
LABELS = [e.value for e in Emotion]
NEGATIVE = (Emotion.sedih, Emotion.cemas, Emotion.marah, Emotion.malu_bersalah)

_cfg = yaml.safe_load((CONFIG_DIR / "emotion_lexicon.yaml").read_text("utf-8"))
_WORDS = {label: [compile_pattern(w) for w in _cfg[label]] for label in LABELS if label in _cfg}
_INTENSIFIERS = [compile_pattern(w) for w in _cfg["intensifiers"]]
HIT_WEIGHT = 0.45  # 1 kata = 0,45; 2 kata ≈ 0,9
INTENSIFIER_BONUS = 0.15


@dataclass(frozen=True)
class EmotionResult:
    scores: dict[str, float]
    source: str  # "model" | "lexicon"

    @property
    def dominant(self) -> str:
        return max(self.scores, key=lambda k: self.scores[k])


def keyword_scores(norm: Normalized) -> dict[str, float]:
    text = norm.text
    boost = INTENSIFIER_BONUS if any(p.search(text) for p in _INTENSIFIERS) else 0.0
    scores = {label: 0.0 for label in LABELS}
    for label, pats in _WORDS.items():
        hits = sum(len(p.findall(text)) for p in pats)
        if hits:
            scores[label] = min(1.0, HIT_WEIGHT * hits + boost)
    scores[Emotion.netral] = max(0.0, 1.0 - max(scores.values()))
    return scores


async def classify(norm: Normalized, model: Classifier | None, timeout: float) -> EmotionResult:
    if model is not None:
        try:
            scores = await asyncio.wait_for(
                asyncio.to_thread(model.predict, norm.original), timeout
            )
            return EmotionResult({label: scores.get(label, 0.0) for label in LABELS}, "model")
        except Exception as e:  # noqa: BLE001 — jatuh ke kata kunci
            log.warning("emotion_model_failed error=%s", type(e).__name__)
    return EmotionResult(keyword_scores(norm), "lexicon")
