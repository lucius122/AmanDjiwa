"""LLM untuk balasan level HIJAU saja (CLAUDE.md §6.3–6.4), via NVIDIA NIM (kompatibel OpenAI).

Gagal apa pun (tanpa key, timeout, error, balasan terpotong, atau melanggar pola terlarang) →
None, dan dialog memakai balasan dari response_bank.yaml. Tidak pernah dipakai untuk kuning,
oranye, atau merah — keputusan level sudah diambil pipeline deterministik sebelum sampai sini.
"""

import logging
import re
import time

import httpx
import yaml

from app.pipeline.normalize import mask_pii
from app.settings import CONFIG_DIR, settings

log = logging.getLogger(__name__)
CFG = yaml.safe_load((CONFIG_DIR / "llm.yaml").read_text("utf-8"))
_BLOCKED = [re.compile(p, re.I) for p in CFG["blocked_patterns"]]

Turn = tuple[str, str]  # (role "user" | "assistant", teks)


def enabled() -> bool:
    return bool(settings.nvidia_api_key)


def build_messages(history: list[Turn], text: str, nickname: str | None) -> list[dict[str, str]]:
    """Pseudonimisasi (§6.4): PII dimasking dan nama samaran diganti "kamu" sebelum dikirim."""

    def clean(t: str) -> str:
        t = mask_pii(t)
        return re.sub(re.escape(nickname), "kamu", t, flags=re.I) if nickname else t

    recent = history[-CFG["max_history"] :]
    return [
        {"role": "system", "content": CFG["system_prompt"]},
        *({"role": role, "content": clean(t)} for role, t in recent),
        {"role": "user", "content": clean(text)},
    ]


def acceptable(reply: str) -> bool:
    return bool(reply) and not any(p.search(reply) for p in _BLOCKED)


async def _complete(messages: list[dict[str, str]]) -> tuple[str, str]:
    """Satu panggilan chat completion. Kembalikan (isi, finish_reason)."""
    async with httpx.AsyncClient(timeout=CFG["timeout_s"]) as client:
        res = await client.post(
            f"{CFG['base_url']}/chat/completions",
            headers={"Authorization": f"Bearer {settings.nvidia_api_key}"},
            json={
                "model": CFG["model"],
                "messages": messages,
                "max_tokens": CFG["max_tokens"],
                "temperature": CFG["temperature"],
                **CFG.get("extra_body", {}),
            },
        )
        res.raise_for_status()
        choice = res.json()["choices"][0]
        return (choice["message"].get("content") or "").strip(), choice.get("finish_reason") or ""


async def green_reply(history: list[Turn], text: str, nickname: str | None) -> str | None:
    if not enabled():
        return None
    start = time.perf_counter()
    try:
        reply, finish = await _complete(build_messages(history, text, nickname))
    except Exception as e:  # noqa: BLE001 — LLM opsional; gagal = bank respons
        log.warning("llm_failed error=%s", type(e).__name__)
        return None
    ms = (time.perf_counter() - start) * 1000
    if finish == "length" or not acceptable(reply):  # log tanpa isi balasan (§7)
        log.warning(
            "llm_rejected reason=%s ms=%.0f", "length" if finish == "length" else "guard", ms
        )
        return None
    log.info("llm_ok ms=%.0f", ms)
    return reply
