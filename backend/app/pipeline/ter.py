"""Skor TER (0–1) → level risiko. Deterministik, tidak pernah dihitung LLM (CLAUDE.md §6.5).

TER = 0,4·E + 0,35·M + 0,25·T   (disetujui 2026-10-05)
  E = emosi negatif terkuat − 0,5·senang          (pesan ini)
  M = penanda: putus asa 0,4 + kata absolut 0,2 + ruminasi 0,2 + fokus diri 0,2
  T = porsi hari negatif dalam 14 hari terakhir    (jurnal + obrolan)
TODO_VERIFY: bobot & ambang adalah titik awal; kalibrasi dengan data berlabel + psikolog.
"""

from collections.abc import Mapping, Sequence

from app.models import RiskLevel
from app.pipeline.emotion import NEGATIVE
from app.pipeline.markers import Markers

W_EMOTION, W_MARKERS, W_TRAJECTORY = 0.4, 0.35, 0.25
MARKER_WEIGHTS = {"putus_asa": 0.4, "kata_absolut": 0.2, "ruminasi": 0.2, "fokus_diri": 0.2}
# Batas atas (eksklusif) tiap level; ≥ 0,75 = merah.
THRESHOLDS = ((0.35, RiskLevel.hijau), (0.55, RiskLevel.kuning), (0.75, RiskLevel.oranye))


def _clamp(x: float) -> float:
    return max(0.0, min(1.0, x))


def emotion_component(scores: Mapping[str, float]) -> float:
    negative = max((scores.get(e, 0.0) for e in NEGATIVE), default=0.0)
    return _clamp(negative - 0.5 * scores.get("senang", 0.0))


def marker_component(markers: Markers) -> float:
    return _clamp(sum(w for k, w in MARKER_WEIGHTS.items() if k in markers.flags))


def negative_day_ratio(daily_dominant: Sequence[str | None]) -> float:
    """Emosi dominan per hari (14 hari). None = tidak ada data, tidak ikut dihitung."""
    known = [d for d in daily_dominant if d is not None]
    return sum(d in NEGATIVE for d in known) / len(known) if known else 0.0


def ter_score(scores: Mapping[str, float], markers: Markers, neg_day_ratio: float) -> float:
    return round(
        W_EMOTION * emotion_component(scores)
        + W_MARKERS * marker_component(markers)
        + W_TRAJECTORY * _clamp(neg_day_ratio),
        4,
    )


def level_for(ter: float) -> RiskLevel:
    for upper, level in THRESHOLDS:
        if ter < upper:
            return level
    return RiskLevel.merah
