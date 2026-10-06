from collections.abc import Mapping

Answers = Mapping[int, int | None]  # nomor item → 0..3, atau None = dilewati


def total(answers: Answers, items: int) -> int | None:
    """Jumlah skor; None kalau ada item yang belum dijawab/dilewati ("Belum lengkap")."""
    for item, value in answers.items():
        if not 1 <= item <= items or (value is not None and not 0 <= value <= 3):
            raise ValueError(f"jawaban tidak valid: item {item} = {value}")
    values = [answers.get(i) for i in range(1, items + 1)]
    return None if any(v is None for v in values) else sum(v for v in values if v is not None)


def band(score: int, bands: tuple[tuple[int, str], ...]) -> str:
    return next(label for upper, label in bands if score <= upper)
