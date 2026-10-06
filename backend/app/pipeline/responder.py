"""Pilih balasan menurut level (CLAUDE.md §6.3). Hanya dari response_bank.yaml; tanpa LLM.

LLM opsional untuk level hijau belum dipasang (YAGNI): bank respons hijau sudah cukup untuk demo.
"""

from dataclasses import dataclass

import yaml

from app.models import RiskLevel
from app.pipeline.emotion import EmotionResult
from app.pipeline.normalize import Normalized, compile_pattern
from app.settings import CONFIG_DIR

BANK = yaml.safe_load((CONFIG_DIR / "response_bank.yaml").read_text("utf-8"))
_HOTLINES = yaml.safe_load((CONFIG_DIR / "hotlines.yaml").read_text("utf-8"))["hotlines"]
_HIJAU_KEYS = {
    key: [compile_pattern(w) for w in words] for key, words in BANK["hijau"]["keywords"].items()
}


@dataclass(frozen=True)
class Hotline:
    id: str
    label: str
    number: str
    note: str


HOTLINES = tuple(Hotline(**h) for h in _HOTLINES)


@dataclass(frozen=True)
class CrisisCard:
    title: str
    body: str
    call_label: str
    connect_label: str
    connect_sub: str
    footer: str


@dataclass(frozen=True)
class ReplyContext:
    nickname: str
    kelurahan: str
    turn: int = 0  # untuk merotasi balasan umum


@dataclass(frozen=True)
class Reply:
    messages: tuple[str, ...]
    hotlines: tuple[Hotline, ...] = ()
    card: CrisisCard | None = None
    offer_connect: bool = False  # tampilkan tombol "Hubungkan aku ke pendamping"


def _fill(text: str, ctx: ReplyContext) -> str:
    return text.format(nama=ctx.nickname, kelurahan=ctx.kelurahan)


def fallback_safe(ctx: ReplyContext) -> Reply:
    return Reply(
        tuple(_fill(t, ctx) for t in BANK["fallback_safe"]),
        hotlines=HOTLINES,
        offer_connect=True,
    )


def crisis_reply(ctx: ReplyContext) -> Reply:
    """Respons merah: teks tervalidasi + kartu krisis + hotline + tombol pendamping (§6.3)."""
    m = BANK["merah"]
    card = CrisisCard(**{k: _fill(v, ctx) for k, v in m["card"].items()})
    return Reply(
        tuple(_fill(t, ctx) for t in m["messages"]),
        hotlines=HOTLINES,
        card=card,
        offer_connect=True,
    )


def respond(
    level: RiskLevel, ctx: ReplyContext, norm: Normalized, emotions: EmotionResult
) -> Reply:
    if level == RiskLevel.merah:
        return crisis_reply(ctx)
    if level == RiskLevel.oranye:
        options = BANK["oranye"]
        return Reply((_fill(options[ctx.turn % len(options)], ctx),), offer_connect=True)
    if level == RiskLevel.kuning:
        k = BANK["kuning"]
        return Reply((_fill(k.get(emotions.dominant, k["default"]), ctx),))

    h = BANK["hijau"]
    for key, pats in _HIJAU_KEYS.items():
        if any(p.search(norm.text) for p in pats):
            return Reply((_fill(h["replies"][key], ctx),))
    return Reply((_fill(h["default"][ctx.turn % len(h["default"])], ctx),))
