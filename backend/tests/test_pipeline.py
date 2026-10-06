import re
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import numpy as np
import pytest
import yaml

import app.pipeline as pipeline
from app.models import RiskLevel
from app.pipeline import Models, analyze, process
from app.pipeline import model as model_mod
from app.pipeline.emotion import classify
from app.pipeline.markers import Markers, detect
from app.pipeline.model import OnnxClassifier, load
from app.pipeline.normalize import normalize
from app.pipeline.responder import HOTLINES, ReplyContext
from app.pipeline.ter import level_for, negative_day_ratio, ter_score
from app.settings import CONFIG_DIR

pytestmark = pytest.mark.anyio
CTX = ReplyContext(nickname="Bintang", kelurahan="Krobokan")


# ---------- urutan & keputusan pipeline ----------


async def test_crisis_always_wins_and_uses_bank_with_hotlines() -> None:
    analysis, reply = await process("aku pengen mati aja", CTX)
    assert analysis is not None and analysis.level == RiskLevel.merah
    assert analysis.ter < 0.75  # TER sendiri tidak merah; krisis yang menentukan
    assert reply.card is not None and reply.offer_connect
    assert reply.hotlines == HOTLINES
    assert reply.messages[0] == "Makasih udah mau cerita ke aku, Bintang. Itu butuh keberanian."
    assert "Krobokan" in reply.card.connect_sub


async def test_everyday_message_gets_green_reply_from_bank() -> None:
    analysis, reply = await process("lagi capek nih", CTX)
    assert analysis is not None and analysis.level == RiskLevel.hijau
    assert reply.card is None and not reply.hotlines
    assert reply.messages[0].startswith("Kedengarannya berat ya")


async def test_sustained_negativity_raises_level_without_crisis_words() -> None:
    text = "aku selalu gagal, semuanya percuma, aku sedih banget dan nggak pernah bisa apa-apa"
    calm = await analyze(text, neg_day_ratio=0.0)
    heavy = await analyze(text, neg_day_ratio=1.0)
    assert not calm.crisis.is_crisis
    assert {"putus_asa", "kata_absolut", "fokus_diri"} <= calm.markers.flags
    assert calm.level == RiskLevel.kuning  # TER 0,52
    # Putus asa + 14 hari negatif berturut-turut → TER 0,77 = merah tanpa satu pun kata krisis.
    # TODO_VERIFY: titik kalibrasi untuk direview psikolog.
    assert heavy.ter > calm.ter and heavy.level == RiskLevel.merah


async def test_crisis_detector_failure_gives_fallback_safe(monkeypatch: pytest.MonkeyPatch) -> None:
    async def broken(*_: object) -> None:
        raise RuntimeError("leksikon rusak")

    monkeypatch.setattr(pipeline.crisis, "detect", broken)
    analysis, reply = await process("halo", CTX)
    assert analysis is None
    assert reply.hotlines == HOTLINES and reply.offer_connect and reply.messages


async def test_any_error_gives_fallback_safe(monkeypatch: pytest.MonkeyPatch) -> None:
    def boom(_: str) -> None:
        raise ValueError("x")

    monkeypatch.setattr(pipeline, "normalize", boom)
    analysis, reply = await process("halo", CTX)
    assert analysis is None and reply.hotlines


async def test_markers_failure_degrades_but_crisis_still_decides(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def boom(_: object) -> None:
        raise RuntimeError("penanda rusak")

    monkeypatch.setattr(pipeline.markers, "detect", boom)
    analysis, _ = await process("pengen bundir", CTX)
    assert analysis is not None and analysis.level == RiskLevel.merah


async def test_emotion_model_failure_falls_back_to_keywords() -> None:
    class Broken:
        threshold = 0.5

        def predict(self, text: str) -> dict[str, float]:
            raise RuntimeError

    result = await classify(normalize("aku sedih banget"), Broken(), 1.0)
    assert result.source == "lexicon" and result.dominant == "sedih"


async def test_models_are_used_when_present() -> None:
    class Crisis:
        threshold = 0.5

        def predict(self, text: str) -> dict[str, float]:
            return {"krisis": 0.99}

    analysis = await analyze("kalimat netral sekali", models=Models(crisis=Crisis()))
    assert analysis.level == RiskLevel.merah


# ---------- TER (rumus disetujui 2026-10-05) ----------


def test_ter_formula_and_level_bands() -> None:
    m = Markers(frozenset({"putus_asa", "kata_absolut", "ruminasi", "fokus_diri"}), frozenset())
    assert ter_score({"sedih": 1.0}, m, 1.0) == 1.0
    assert ter_score({"sedih": 0.6, "senang": 0.4}, Markers(frozenset(), frozenset()), 0) == 0.16
    assert [level_for(x) for x in (0.0, 0.3499, 0.35, 0.5499, 0.55, 0.7499, 0.75, 1.0)] == [
        RiskLevel.hijau, RiskLevel.hijau, RiskLevel.kuning, RiskLevel.kuning,
        RiskLevel.oranye, RiskLevel.oranye, RiskLevel.merah, RiskLevel.merah,
    ]  # fmt: skip


def test_negative_day_ratio_ignores_days_without_data() -> None:
    assert negative_day_ratio(["sedih", None, "senang", "cemas", None]) == pytest.approx(2 / 3)
    assert negative_day_ratio([None, None]) == 0.0


def test_markers_detect_topics() -> None:
    m = detect(normalize("di rumah ribut terus sama ayah, aku nggak bisa tidur"))
    assert "keluarga" in m.topics and "gangguan_tidur" in m.flags


# ---------- teks untuk remaja tidak boleh membocorkan level/skor (§6.7) ----------

_FORBIDDEN = re.compile(r"\b(risiko|berisiko|skor|level|merah|oranye|kuning|hijau)\b", re.I)


def _strings(node: object) -> list[str]:
    if isinstance(node, str):
        return [node]
    if isinstance(node, dict):
        return [s for v in node.values() for s in _strings(v)]
    if isinstance(node, list):
        return [s for v in node for s in _strings(v)]
    return []


@pytest.mark.parametrize("name", ["response_bank.yaml", "screening.yaml", "hotlines.yaml"])
def test_teen_facing_texts_never_mention_risk_levels(name: str) -> None:
    cfg = yaml.safe_load((CONFIG_DIR / name).read_text("utf-8"))
    if name == "screening.yaml":
        cfg.pop("severity_labels")  # khusus dasbor staf
    leaks = [s for s in _strings(cfg) if _FORBIDDEN.search(s)]
    assert not leaks, leaks


def test_hotline_numbers_come_only_from_yaml() -> None:
    cfg = yaml.safe_load((CONFIG_DIR / "hotlines.yaml").read_text("utf-8"))["hotlines"]
    assert [h.number for h in HOTLINES] == [h["number"] for h in cfg]


# ---------- slot model ONNX ----------


def test_onnx_classifier_glue() -> None:
    class Session:
        def get_inputs(self) -> list[SimpleNamespace]:
            return [SimpleNamespace(name="input_ids"), SimpleNamespace(name="attention_mask")]

        def run(self, _: None, feed: dict[str, Any]) -> list[Any]:
            assert set(feed) == {"input_ids", "attention_mask"}  # input ekstra dibuang
            return [np.array([[0.0, 3.0, -3.0]])]

    def tokenizer(text: str, **_: object) -> dict[str, Any]:
        ones = np.ones((1, 4), dtype=np.int64)
        return {"input_ids": ones, "attention_mask": ones, "token_type_ids": ones * 0}

    probs = OnnxClassifier(tokenizer, Session(), ["a", "b", "c"], 0.5).predict("halo")
    assert probs["a"] == 0.5 and probs["b"] > 0.95 and probs["c"] < 0.05


def test_missing_or_uncalibrated_model_is_not_loaded(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(model_mod, "MODELS_DIR", tmp_path)
    assert load("emotion") is None  # belum ada file
    (tmp_path / "crisis").mkdir()
    (tmp_path / "crisis" / "model.onnx").write_bytes(b"x")
    assert load("crisis") is None  # tanpa calibration.json: ambang recall belum dikalibrasi
