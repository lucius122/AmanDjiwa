"""PHQ-9: skoring deterministik (Kroenke dkk., 2001). Bukan diagnosis."""

from app.screening._common import Answers, band, total

ITEMS = 9
SUICIDE_ITEM = 9  # jawaban > 0 = krisis, apa pun total skornya
BANDS = ((4, "minimal"), (9, "ringan"), (14, "sedang"), (19, "sedang_berat"), (27, "berat"))


def score(answers: Answers) -> int | None:
    return total(answers, ITEMS)


def severity(score: int) -> str:
    return band(score, BANDS)
