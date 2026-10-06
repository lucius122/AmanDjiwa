"""Penanda linguistik: fokus diri, kata absolut, putus asa, ruminasi, dll. + topik pemicu."""

from dataclasses import dataclass

import yaml

from app.pipeline.normalize import Normalized, compile_pattern, skeleton
from app.settings import CONFIG_DIR

_cfg = yaml.safe_load((CONFIG_DIR / "markers.yaml").read_text("utf-8"))
_FIRST = {skeleton(w) for w in _cfg["first_person"]["words"]}
_ABSOLUTE = [compile_pattern(w) for w in _cfg["absolute"]["words"]]
_FLAGS = {k: [compile_pattern(p) for p in v["patterns"]] for k, v in _cfg["flags"].items()}
_TOPICS = {k: [compile_pattern(w) for w in v["words"]] for k, v in _cfg["topics"].items()}

LABELS: dict[str, str] = {k: v["label"] for k, v in _cfg["flags"].items()} | _cfg["labels"]
TOPIC_LABELS: dict[str, str] = {k: v["label"] for k, v in _cfg["topics"].items()}
TRIGGER_LABELS: dict[str, str] = _cfg["trigger_labels"]
BEHAVIOR: dict[str, dict[str, str | int]] = _cfg["behavior"]


@dataclass(frozen=True)
class Markers:
    flags: frozenset[str]  # kunci di LABELS
    topics: frozenset[str]  # kunci di TOPIC_LABELS


def detect(norm: Normalized) -> Markers:
    text, tokens = norm.text, norm.tokens
    flags = {k for k, pats in _FLAGS.items() if any(p.search(text) for p in pats)}

    fp = _cfg["first_person"]
    if len(tokens) >= fp["min_tokens"] and (
        sum(t in _FIRST for t in tokens) / len(tokens) >= fp["min_ratio"]
    ):
        flags.add("fokus_diri")
    if sum(len(p.findall(text)) for p in _ABSOLUTE) >= _cfg["absolute"]["min_hits"]:
        flags.add("kata_absolut")

    topics = {k for k, pats in _TOPICS.items() if any(p.search(text) for p in pats)}
    return Markers(frozenset(flags), frozenset(topics))
