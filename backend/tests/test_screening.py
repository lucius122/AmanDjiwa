import pytest

from app.models import Instrument, RiskLevel
from app.screening import (
    followup_needed,
    gad7,
    is_crisis_answer,
    phq4_total,
    phq9,
    remaining_items,
    result_key,
    screening_level,
)


def _all(n: int, value: int) -> dict[int, int | None]:
    return {i: value for i in range(1, n + 1)}


def test_scores_are_sums_and_incomplete_is_none() -> None:
    assert phq9.score(_all(9, 3)) == 27
    assert gad7.score(_all(7, 1)) == 7
    assert phq9.score({1: 2, 2: 2}) is None  # belum lengkap
    assert phq9.score(_all(9, 1) | {4: None}) is None  # dilewati


@pytest.mark.parametrize("bad", [{1: 4}, {1: -1}, {10: 0}, {0: 1}])
def test_invalid_answers_rejected(bad: dict[int, int | None]) -> None:
    with pytest.raises(ValueError):
        phq9.score(bad)


@pytest.mark.parametrize(
    ("total", "label"),
    [(0, "minimal"), (4, "minimal"), (5, "ringan"), (9, "ringan"), (10, "sedang"),
     (14, "sedang"), (15, "sedang_berat"), (19, "sedang_berat"), (20, "berat"), (27, "berat")],
)  # fmt: skip
def test_phq9_severity_bands(total: int, label: str) -> None:
    assert phq9.severity(total) == label


@pytest.mark.parametrize(
    ("total", "label"),
    [(4, "minimal"), (5, "ringan"), (9, "ringan"), (10, "sedang"), (14, "sedang"), (15, "berat")],
)
def test_gad7_severity_bands(total: int, label: str) -> None:
    assert gad7.severity(total) == label


def test_item9_any_positive_answer_is_crisis() -> None:
    assert is_crisis_answer(Instrument.phq9, 9, 1)
    assert not is_crisis_answer(Instrument.phq9, 9, 0)
    assert not is_crisis_answer(Instrument.phq9, 9, None)
    assert not is_crisis_answer(Instrument.gad7, 7, 3)
    low_total_but_item9 = _all(9, 0) | {9: 1}
    assert screening_level(low_total_but_item9, {}) == RiskLevel.merah


@pytest.mark.parametrize(
    ("phq4", "key"), [(0, "low"), (3, "low"), (4, "mid"), (7, "mid"), (8, "high")]
)
def test_phq4_result_thresholds_follow_design(phq4: int, key: str) -> None:
    assert result_key(phq4) == key


def test_phq4_total_counts_skips_as_zero() -> None:
    assert phq4_total({1: 2, 2: None}, {1: 3, 2: 1}) == 6


def test_followup_after_positive_phq2_or_gad2() -> None:
    assert followup_needed({1: 1, 2: 2}, {1: 0, 2: 1}) == [Instrument.phq9]
    assert followup_needed({1: 0, 2: 0}, {1: 2, 2: 2}) == [Instrument.gad7]
    assert followup_needed({1: 1, 2: 1}, {1: 1, 2: 1}) == []
    assert remaining_items(Instrument.gad7, {1: 2, 2: None}) == [3, 4, 5, 6, 7]


def test_screening_level_mapping() -> None:
    assert screening_level(_all(9, 2) | {9: 0}, {}) == RiskLevel.oranye  # PHQ-9 = 16
    assert screening_level({}, _all(7, 2) | {7: 0}) == RiskLevel.kuning  # GAD-7 = 12
    assert screening_level({1: 2, 2: 2}, {1: 2, 2: 2}) == RiskLevel.oranye  # PHQ-4 = 8
    assert screening_level({1: 1, 2: 1}, {1: 1, 2: 1}) is None
