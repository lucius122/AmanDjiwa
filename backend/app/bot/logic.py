"""Logika bot Telegram, terpisah dari aiogram supaya bisa dites tanpa token.

Aturan keselamatan: pesan krisis dari akun yang BELUM tersambung tetap dijawab dengan kartu
krisis + hotline (tanpa membuat kasus, karena belum ada akun/persetujuan).
"""

import secrets
import uuid
from dataclasses import dataclass, field

import yaml
from redis.asyncio import Redis
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dialog import Action, ChatTurn, Dialog, DialogError
from app.models import Channel, ChannelLink, MessageKind, User, UserStatus
from app.pipeline import Models, analyze
from app.pipeline.responder import BANK, Hotline, ReplyContext, crisis_reply
from app.redis import hit_rate_limit
from app.settings import CONFIG_DIR

TG = yaml.safe_load((CONFIG_DIR / "telegram.yaml").read_text("utf-8"))
LINK_TTL = 15 * 60  # §7: token deep link sekali pakai, kedaluwarsa 15 menit
_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # tanpa 0/O/1/I
_CALLBACKS: dict[str, Action] = {"connect": "connect", "skip": "skip", "stop": "stop",
                                 "continue": "continue"}  # fmt: skip


@dataclass(frozen=True)
class OutMsg:
    text: str
    buttons: list[list[tuple[str, str]]] = field(default_factory=list)  # (label, callback_data)


# ---------- tautan akun ----------


async def create_link_code(r: Redis, user_id: uuid.UUID) -> str:
    code = "DJW-" + "".join(secrets.choice(_ALPHABET) for _ in range(6))
    await r.set(f"tg:link:{code}", str(user_id), ex=LINK_TTL)
    return code


async def _linked_user(session: AsyncSession, telegram_id: int) -> User | None:
    return (
        await session.execute(
            select(User)
            .join(ChannelLink, ChannelLink.user_id == User.id)
            .where(ChannelLink.telegram_id == telegram_id)
        )
    ).scalar_one_or_none()


async def on_start(
    r: Redis, session: AsyncSession, telegram_id: int, payload: str | None
) -> list[OutMsg]:
    if not payload:
        return [OutMsg(TG["start"])]
    # Batasi tebakan kode dari satu akun Telegram.
    if await hit_rate_limit(r, f"rl:tg-start:{telegram_id}", limit=5, window_s=600):
        return [OutMsg(TG["rate_limited"])]
    user_id = await r.getdel(f"tg:link:{payload.strip().upper()}")
    user = await session.get(User, uuid.UUID(user_id)) if user_id else None
    if user is None:
        return [OutMsg(TG["link_invalid"])]
    await session.execute(
        delete(ChannelLink).where(
            (ChannelLink.telegram_id == telegram_id) | (ChannelLink.user_id == user.id)
        )
    )
    session.add(ChannelLink(user_id=user.id, telegram_id=telegram_id))
    await session.commit()
    return [OutMsg(TG["linked"].format(nama=user.pseudonym or "kamu"))]


async def toggle_reminder(session: AsyncSession, telegram_id: int) -> list[OutMsg]:
    """/pengingat: nyalakan/matikan pengingat jurnal harian (default menyala)."""
    user = await _linked_user(session, telegram_id)
    if user is None or user.status != UserStatus.active:
        return [OutMsg(TG["not_linked"])]
    on = user.settings.get("journal_reminder", True) is False
    user.settings = {
        **user.settings,
        "journal_reminder": on,
    }  # dict baru: JSONB tidak dilacak in-place
    await session.commit()
    return [OutMsg(TG["reminder_on" if on else "reminder_off"])]


# ---------- pesan & tombol ----------


async def on_text(
    r: Redis, session: AsyncSession, telegram_id: int, text: str, models: Models
) -> list[OutMsg]:
    if await hit_rate_limit(r, f"rl:tg:{telegram_id}", limit=20):
        return [OutMsg(TG["rate_limited"])]
    user = await _linked_user(session, telegram_id)
    if user is None or user.status != UserStatus.active:
        return await _unlinked(text, models)
    turn = await Dialog(session, r, user, models, Channel.telegram).handle_text(text[:2000])
    return render(turn)


async def on_callback(
    r: Redis, session: AsyncSession, telegram_id: int, data: str, models: Models
) -> list[OutMsg]:
    user = await _linked_user(session, telegram_id)
    if user is None or user.status != UserStatus.active:
        return [OutMsg(TG["not_linked"])]
    action: Action | None = _CALLBACKS.get(data)
    value = None
    if data.startswith("ans:") and data[4:].isdigit():
        action, value = "answer", int(data[4:])
    if action is None:
        return []
    try:
        turn = await Dialog(session, r, user, models, Channel.telegram).handle_action(action, value)
    except DialogError:  # tombol lama dari pertanyaan yang sudah lewat
        return []
    return render(turn)


async def _unlinked(text: str, models: Models) -> list[OutMsg]:
    try:
        is_crisis = (await analyze(text, models=models)).crisis.is_crisis
    except Exception:  # noqa: BLE001 — ragu = anggap krisis, tampilkan hotline
        is_crisis = True
    if not is_crisis:
        return [OutMsg(TG["not_linked"])]
    reply = crisis_reply(ReplyContext(nickname="kamu", kelurahan=""))
    turn = ChatTurn(card=reply.card, hotlines=list(reply.hotlines))
    return [*render_card(turn, can_connect=False), OutMsg(TG["not_linked"])]


UNVERIFIED = "TODO_VERIFY"  # nilai awal hotlines.yaml (§6.6); web menampilkan "[ nomor ]"


def hotline_lines(hotlines: list[Hotline]) -> list[str]:
    """Nomor yang belum diverifikasi tidak pernah ditampilkan; ganti dengan pemberitahuan."""
    lines = [
        TG["hotline"].format(label=h.label, number=h.number)
        for h in hotlines
        if h.number != UNVERIFIED
    ]
    return lines + [TG["hotline_unverified"]] if len(lines) < len(hotlines) else lines


def render_card(turn: ChatTurn, can_connect: bool = True) -> list[OutMsg]:
    card = turn.card
    assert card is not None
    hotlines = hotline_lines(turn.hotlines)
    text = "\n".join([card.title, "", card.body, "", *hotlines, "", card.footer])
    buttons = [[(card.connect_label, "connect")]] if can_connect and not turn.connected else []
    return [OutMsg(text, buttons)]


def render(turn: ChatTurn) -> list[OutMsg]:
    """ChatTurn (sama dengan web) → pesan Telegram. Teks biasa, tanpa Markdown."""
    out: list[OutMsg] = []
    for m in turn.messages:
        if m.kind == MessageKind.crisis_card and turn.card is not None:
            out += render_card(turn)
        else:
            out.append(OutMsg(m.text))
    if turn.hotlines and turn.card is None:  # fallback_safe: hotline tetap dikirim
        out.append(OutMsg("\n".join(hotline_lines(turn.hotlines))))
    if turn.offer_connect and turn.card is None and not turn.connected:
        _attach(out, [[(BANK["merah"]["card"]["connect_label"], "connect")]])
    if turn.followup_offer:
        _attach(out, [[(TG["continue"], "continue"), (TG["stop"], "stop")]])
    if turn.client_action == "open_napas":
        out.append(OutMsg(TG["napas"]))
    if turn.screening is not None:
        q = turn.screening
        options = [[(label, f"ans:{i}")] for i, label in enumerate(q.options)]
        out.append(
            OutMsg(
                TG["question"].format(n=q.n, total=q.total) + "\n" + q.text,
                [*options, [(TG["skip"], "skip"), (TG["stop"], "stop")]],
            )
        )
    return out


def _attach(out: list[OutMsg], buttons: list[list[tuple[str, str]]]) -> None:
    """Tempel tombol ke pesan terakhir (Telegram: tombol menempel pada satu pesan)."""
    if out and not out[-1].buttons:
        out[-1] = OutMsg(out[-1].text, buttons)
