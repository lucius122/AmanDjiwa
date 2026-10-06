"""Normalisasi pesan (langkah pertama pipeline, CLAUDE.md §5).

Menghasilkan dua bentuk:
- `masked`: teks asli dengan PII diganti token ([EMAIL], [NOMOR], ...). Untuk LLM/tampilan staf.
- `tokens`: bentuk kanonik untuk pencocokan saja (huruf kecil, leet & sensor dibuka, huruf berulang
  dikerangkakan, slang/Jawa → kata baku). Tidak pernah ditampilkan.
Pencocokan krisis memakai teks ASLI (bukan yang dimasking) supaya tidak ada kata yang hilang.
"""

import difflib
import re
from dataclasses import dataclass

import yaml

from app.settings import CONFIG_DIR

_cfg = yaml.safe_load((CONFIG_DIR / "normalize.yaml").read_text("utf-8"))


def skeleton(text: str) -> str:
    """Huruf yang berulang jadi satu: 'capekkk' → 'capek', 'maaf' → 'maf'. Dipakai di kedua sisi."""
    return re.sub(r"([a-z])\1+", r"\1", text)


_SLANG: dict[str, list[str]] = {skeleton(k): skeleton(v).split() for k, v in _cfg["slang"].items()}
_EMOJI: dict[str, str] = _cfg["emoji"]
_FUZZY: list[str] = [skeleton(w) for w in _cfg["fuzzy_targets"]]
_LEET = str.maketrans({"4": "a", "@": "a", "3": "e", "1": "i", "!": "i", "0": "o", "5": "s",
                       "$": "s", "7": "t"})  # fmt: skip

# Urutan penting: NIK (16 digit) sebelum nomor HP.
_PII = [
    (re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+"), "[EMAIL]"),
    (re.compile(r"\b\d{16}\b"), "[NIK]"),
    (re.compile(r"(?:\+?62|0)\s?8[\d\s-]{7,13}\d"), "[NOMOR]"),
    (re.compile(r"\b\d{10,}\b"), "[NOMOR]"),
    (
        re.compile(r"\b(?:jl|jln|jalan|gg|gang)\.?\s+[\w .]{2,40}?\bno\.?\s*\d+\w*", re.I),
        "[ALAMAT]",
    ),
    (re.compile(r"\brt\.?\s*\d+\s*/?\s*rw\.?\s*\d+", re.I), "[ALAMAT]"),
]


@dataclass(frozen=True)
class Normalized:
    original: str
    masked: str
    tokens: tuple[str, ...]

    @property
    def text(self) -> str:
        return " ".join(self.tokens)


def mask_pii(text: str) -> str:
    for pattern, token in _PII:
        text = pattern.sub(token, text)
    return text


def _canonical(word: str) -> list[str]:
    word = skeleton(word)
    if word in _SLANG:
        return _SLANG[word]
    if len(word) >= 5:
        close = difflib.get_close_matches(word, _FUZZY, n=1, cutoff=0.8)
        if close:
            return [close[0]]
    return [word]


def _raw_tokens(text: str) -> list[str]:
    text = text.replace("️", "")  # variation selector emoji (⚰️ → ⚰)
    for emoji, word in _EMOJI.items():
        text = text.replace(emoji, f" {word} ")
    out: list[str] = []
    for chunk in text.lower().replace("'", "").replace("’", "").split():
        if re.search(r"[a-z]", chunk) and re.search(r"[0-9@$!*]", chunk):
            chunk = re.sub(r"([a-z]+)2\b", r"\1 \1", chunk)  # teman2 → teman teman
            chunk = chunk.translate(_LEET).replace("*", "")  # m4ti → mati, b*nuh → bnuh
        out += re.findall(r"[a-z0-9_]+", chunk)
    return out


def normalize(text: str) -> Normalized:
    tokens = [c for raw in _raw_tokens(text) for c in _canonical(raw)]
    return Normalized(original=text, masked=mask_pii(text), tokens=tuple(tokens))


GAP = r"(?:\s+\S+){0,3}\s+"
SUFFIX = r"(?:ku|mu|nya)?"  # akhiran yang menempel: hidupku, terakhirnya, diriku


def compile_pattern(pattern: str) -> re.Pattern[str]:
    """Pola leksikon → regex atas `Normalized.text`.

    Ditulis dengan ejaan biasa; spasi = batas kata; `...` = boleh diselingi 0–3 kata.
    Setiap kata otomatis menerima akhiran -ku/-mu/-nya.
    Contoh: "(ingin|mau) ... mati" cocok dengan "aku ingin banget mati".
    """
    # Tanpa .lower(): akan mengubah \S jadi \s. Pola memang ditulis huruf kecil.
    parts = [
        p.strip().replace(" ", SUFFIX + r"\s+") + SUFFIX for p in skeleton(pattern).split("...")
    ]
    return re.compile(rf"(?<!\S)(?:{GAP.join(parts)})(?!\S)")
