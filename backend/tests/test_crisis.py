"""Gerbang detektor krisis (CLAUDE.md §6.1, §6.2, §6.8). Wajib lolos untuk setiap perubahan
pada pipeline/crisis.py, crisis_lexicon.yaml, normalize.yaml, atau response_bank.yaml."""

import time
from pathlib import Path

import pytest
import yaml

from app.pipeline import crisis
from app.pipeline.crisis import detect, match_lexicon
from app.pipeline.normalize import normalize
from app.settings import CONFIG_DIR

pytestmark = pytest.mark.anyio
CASES = yaml.safe_load((Path(__file__).parent / "crisis_cases.yaml").read_text("utf-8"))
MIN_RECALL = 0.95
MAX_FALSE_POSITIVE_RATE = 0.10  # dipantau; recall tetap lebih penting


def _misses(sentences: list[str]) -> list[str]:
    return [s for s in sentences if not match_lexicon(normalize(s))]


def test_recall_on_crisis_cases() -> None:
    sentences = CASES["crisis"]
    assert len(sentences) >= 50
    misses = _misses(sentences)
    recall = 1 - len(misses) / len(sentences)
    assert recall >= MIN_RECALL, f"recall {recall:.3f} < {MIN_RECALL}. Terlewat: {misses}"


def test_recall_on_external_cases() -> None:
    """Kalimat dari tim/psikolog yang tidak melihat leksikon: ukuran yang lebih jujur."""
    sentences = CASES.get("crisis_external") or []
    if not sentences:
        pytest.skip("crisis_external masih kosong: minta tim/psikolog menulis kalimat uji")
    misses = _misses(sentences)
    recall = 1 - len(misses) / len(sentences)
    assert recall >= MIN_RECALL, f"recall eksternal {recall:.3f}. Terlewat: {misses}"


def test_false_positive_rate_is_monitored() -> None:
    sentences = CASES["not_crisis"]
    false_pos = [s for s in sentences if match_lexicon(normalize(s))]
    rate = len(false_pos) / len(sentences)
    assert rate <= MAX_FALSE_POSITIVE_RATE, f"salah tangkap {rate:.2f}: {false_pos}"


def test_lexicon_has_no_off_switch() -> None:
    # §6.1: detektor tidak boleh bisa dimatikan lewat config. Kunci baru = harus lewat review.
    cfg = yaml.safe_load((CONFIG_DIR / "crisis_lexicon.yaml").read_text("utf-8"))
    assert set(cfg) == {"categories", "concepts", "rules", "idioms"}


class _Model:
    def __init__(self, prob: float = 0.0, error: bool = False, delay: float = 0.0) -> None:
        self.threshold = 0.5
        self.prob, self.error, self.delay = prob, error, delay

    def predict(self, text: str) -> dict[str, float]:
        if self.delay:
            time.sleep(self.delay)
        if self.error:
            raise RuntimeError("model rusak")
        return {crisis.MODEL_LABEL: self.prob}


async def test_model_adds_detection_lexicon_missed() -> None:
    result = await detect(normalize("kalimat yang tidak dikenali leksikon"), _Model(0.9), 1.0)
    assert result.is_crisis and result.categories == []


async def test_model_cannot_veto_lexicon() -> None:
    result = await detect(normalize("aku pengen mati aja"), _Model(0.0), 1.0)
    assert result.is_crisis


@pytest.mark.parametrize("model", [_Model(error=True), _Model(prob=0.9, delay=0.5)])
async def test_model_failure_or_timeout_falls_back_to_lexicon(model: _Model) -> None:
    hit = await detect(normalize("aku pengen mati aja"), model, timeout=0.05)
    assert hit.is_crisis and hit.model_failed
    miss = await detect(normalize("lagi makan siang"), model, timeout=0.05)
    assert not miss.is_crisis and miss.model_failed


def test_idiom_removal_does_not_hide_crisis_in_same_message() -> None:
    assert match_lexicon(normalize("mati lampu lagi, aku juga pengen mati aja"))
    assert not match_lexicon(normalize("mati lampu lagi"))


async def test_detect_without_model_uses_lexicon_only() -> None:
    assert (await detect(normalize("halo"), None, 1.0)).is_crisis is False
    assert (await detect(normalize("pengen bundir"), None, 1.0)).is_crisis is True
