"""Pipeline per pesan (CLAUDE.md §5), urutan wajib:

normalize → gather(krisis, emosi, penanda) → TER → krisis menang → responder.
Fail-safe (§6.2): komponen emosi/penanda gagal = jalan terus tanpa komponen itu; detektor krisis
gagal atau error lain = balasan `fallback_safe` (+ hotline), tidak pernah diam / stack trace.
"""

import asyncio
import logging
from dataclasses import dataclass
from functools import cache

from app.models import Emotion, RiskLevel
from app.pipeline import crisis, emotion, markers
from app.pipeline.crisis import CrisisResult
from app.pipeline.emotion import EmotionResult
from app.pipeline.markers import Markers
from app.pipeline.model import Classifier, load
from app.pipeline.normalize import Normalized, normalize
from app.pipeline.responder import Reply, ReplyContext, fallback_safe, respond
from app.pipeline.ter import level_for, ter_score

log = logging.getLogger(__name__)
MODEL_TIMEOUT = 2.0  # detik per model; lewat dari ini → leksikon/kata kunci saja


@dataclass(frozen=True)
class Models:
    crisis: Classifier | None = None
    emotion: Classifier | None = None


NO_MODELS = Models()  # leksikon & kata kunci saja


def load_models() -> Models:
    return Models(crisis=load("crisis"), emotion=load("emotion"))


@cache
def default_models() -> Models:
    """Dimuat sekali per proses; None per model kalau filenya belum ada."""
    return load_models()


@dataclass(frozen=True)
class Analysis:
    normalized: Normalized
    crisis: CrisisResult
    emotions: EmotionResult
    markers: Markers
    ter: float
    level: RiskLevel


async def _markers(norm: Normalized) -> Markers:
    return markers.detect(norm)


async def analyze(text: str, *, neg_day_ratio: float = 0.0, models: Models = NO_MODELS) -> Analysis:
    norm = normalize(text)
    crisis_r, emo_r, mark_r = await asyncio.gather(
        crisis.detect(norm, models.crisis, MODEL_TIMEOUT),
        emotion.classify(norm, models.emotion, MODEL_TIMEOUT),
        _markers(norm),
        return_exceptions=True,
    )
    if isinstance(crisis_r, BaseException):
        raise crisis_r  # tanpa detektor krisis tidak aman lanjut → fallback_safe
    if isinstance(emo_r, BaseException):
        log.error("emotion_failed error=%s", type(emo_r).__name__)
        emo_r = EmotionResult({Emotion.netral: 1.0}, "failed")
    if isinstance(mark_r, BaseException):
        log.error("markers_failed error=%s", type(mark_r).__name__)
        mark_r = Markers(frozenset(), frozenset())

    ter = ter_score(emo_r.scores, mark_r, neg_day_ratio)
    level = RiskLevel.merah if crisis_r.is_crisis else level_for(ter)  # krisis selalu menang
    return Analysis(norm, crisis_r, emo_r, mark_r, ter, level)


async def process(
    text: str, ctx: ReplyContext, *, neg_day_ratio: float = 0.0, models: Models = NO_MODELS
) -> tuple[Analysis | None, Reply]:
    """Analisis + balasan. Tidak pernah raise: kegagalan apa pun → fallback_safe."""
    try:
        analysis = await analyze(text, neg_day_ratio=neg_day_ratio, models=models)
        return analysis, respond(analysis.level, ctx, analysis.normalized, analysis.emotions)
    except Exception as e:  # noqa: BLE001 — bot tidak boleh diam (§6.2)
        log.error("pipeline_failed error=%s", type(e).__name__)  # tanpa isi pesan (§7)
        return None, fallback_safe(ctx)
