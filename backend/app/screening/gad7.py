"""GAD-7: skoring deterministik (Spitzer dkk., 2006). Bukan diagnosis."""

from app.screening._common import Answers, band, total

ITEMS = 7
BANDS = ((4, "minimal"), (9, "ringan"), (14, "sedang"), (21, "berat"))


def score(answers: Answers) -> int | None:
    return total(answers, ITEMS)


def severity(score: int) -> str:
    return band(score, BANDS)
