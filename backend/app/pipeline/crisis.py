"""Detektor krisis (CLAUDE.md §6.1–6.2): leksikon ATAU model. Tidak ada flag untuk mematikannya.

Leksikon selalu jalan dan tidak bisa dilewati. Model hanya bisa MENAMBAH deteksi, tidak pernah
membatalkan hasil leksikon. Model error/timeout → hasil leksikon saja.
"""

import asyncio
import logging
from dataclasses import dataclass, field

import yaml

from app.pipeline.model import Classifier
from app.pipeline.normalize import Normalized, compile_pattern
from app.settings import CONFIG_DIR

log = logging.getLogger(__name__)
_cfg = yaml.safe_load((CONFIG_DIR / "crisis_lexicon.yaml").read_text("utf-8"))
_CATEGORIES = {
    name: [compile_pattern(p) for p in patterns] for name, patterns in _cfg["categories"].items()
}
_IDIOMS = [compile_pattern(p) for p in _cfg["idioms"]]
_CONCEPTS = {
    name: [compile_pattern(p) for p in patterns] for name, patterns in _cfg["concepts"].items()
}
_RULES: list[tuple[str, list[str]]] = [(r["category"], r["all"]) for r in _cfg["rules"]]
MODEL_LABEL = "krisis"


@dataclass(frozen=True)
class CrisisResult:
    is_crisis: bool
    categories: list[str] = field(default_factory=list)  # kategori leksikon yang cocok
    model_prob: float | None = None
    model_failed: bool = False


def match_lexicon(norm: Normalized) -> list[str]:
    text = norm.text
    for idiom in _IDIOMS:
        text = idiom.sub(" ", text)
    found = {name for name, pats in _CATEGORIES.items() if any(p.search(text) for p in pats)}
    present = {name for name, pats in _CONCEPTS.items() if any(p.search(text) for p in pats)}
    found |= {category for category, needed in _RULES if present.issuperset(needed)}
    return sorted(found)


async def detect(norm: Normalized, model: Classifier | None, timeout: float) -> CrisisResult:
    categories = match_lexicon(norm)
    prob: float | None = None
    failed = False
    if model is not None:
        try:
            scores = await asyncio.wait_for(
                asyncio.to_thread(model.predict, norm.original), timeout
            )
            prob = scores[MODEL_LABEL]
        except Exception as e:  # noqa: BLE001 — fail-safe: jatuh ke leksikon
            failed = True
            log.warning("crisis_model_failed error=%s", type(e).__name__)
    model_hit = prob is not None and model is not None and prob >= model.threshold
    return CrisisResult(
        is_crisis=bool(categories) or model_hit,
        categories=categories,
        model_prob=prob,
        model_failed=failed,
    )
