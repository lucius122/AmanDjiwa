"""Alur skrining di chat: PHQ-4 dulu, lanjut bertahap ke PHQ-9/GAD-7 (keputusan 2026-10-05).

PHQ-4 = PHQ-2 (item 1–2 PHQ-9) + GAD-2 (item 1–2 GAD-7), urutan mengikuti desain.
Semua skor deterministik di sini; tidak pernah oleh LLM (CLAUDE.md §6.5).
"""

from app.models import Instrument, RiskLevel
from app.screening import gad7, phq9
from app.screening._common import Answers

PHQ4_ORDER = (
    (Instrument.phq9, 2),
    (Instrument.phq9, 1),
    (Instrument.gad7, 1),
    (Instrument.gad7, 2),
)
POSITIVE_SCREEN = 3  # PHQ-2 / GAD-2 ≥ 3 (Kroenke dkk.) → tawarkan instrumen lengkap
# Ambang pesan hasil PHQ-4 mengikuti prototipe: ≤ 3 rendah, ≤ 7 sedang, ≥ 8 tinggi.
PHQ4_MID, PHQ4_HIGH = 4, 8
_ITEMS = {Instrument.phq9: phq9.ITEMS, Instrument.gad7: gad7.ITEMS}


def _sum(answers: Answers, items: tuple[int, ...]) -> int:
    return sum(answers.get(i) or 0 for i in items)  # dilewati = 0, seperti prototipe


def phq4_total(phq: Answers, gad: Answers) -> int:
    return _sum(phq, (1, 2)) + _sum(gad, (1, 2))


def followup_needed(phq: Answers, gad: Answers) -> list[Instrument]:
    out = []
    if _sum(phq, (1, 2)) >= POSITIVE_SCREEN:
        out.append(Instrument.phq9)
    if _sum(gad, (1, 2)) >= POSITIVE_SCREEN:
        out.append(Instrument.gad7)
    return out


def remaining_items(instrument: Instrument, answers: Answers) -> list[int]:
    """Item yang belum ditanyakan (yang dilewati tetap dianggap sudah ditanyakan)."""
    return [i for i in range(1, _ITEMS[instrument] + 1) if i not in answers]


def is_crisis_answer(instrument: Instrument, item: int, answer: int | None) -> bool:
    """Item 9 PHQ-9 (pikiran lebih baik mati / menyakiti diri) > 0 → alur krisis (§6)."""
    return instrument == Instrument.phq9 and item == phq9.SUICIDE_ITEM and bool(answer)


def result_key(phq4: int) -> str:
    return "low" if phq4 < PHQ4_MID else "mid" if phq4 < PHQ4_HIGH else "high"


def screening_level(phq: Answers, gad: Answers) -> RiskLevel | None:
    """Level kasus dari skrining; None = tidak perlu kasus. TODO_VERIFY: kalibrasi ambang."""
    if is_crisis_answer(Instrument.phq9, phq9.SUICIDE_ITEM, phq.get(phq9.SUICIDE_ITEM)):
        return RiskLevel.merah
    p, g = phq9.score(phq), gad7.score(gad)
    if (
        (p is not None and p >= 15)
        or (g is not None and g >= 15)
        or phq4_total(phq, gad) >= PHQ4_HIGH
    ):
        return RiskLevel.oranye
    if (p is not None and p >= 10) or (g is not None and g >= 10):
        return RiskLevel.kuning
    return None
