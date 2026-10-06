"""State machine percakapan (CLAUDE.md §4 `dialog/`). Web & Telegram memakai jalur yang sama.

Urutan per pesan teks:
1. Selalu lewat pipeline dulu (krisis, emosi, penanda), termasuk saat skrining sedang berjalan.
2. Merah → respons krisis; skrining dihentikan; intent diabaikan.
3. Hijau → intent ("cek perasaan", "napas") boleh berlaku. Kuning/oranye → bank respons.
State (skrining aktif, sudah minta pendamping) disimpan di Redis per remaja.
"""

import json
import uuid
from dataclasses import asdict, dataclass, field
from typing import Literal

import yaml
from pydantic import BaseModel
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app import screening
from app.models import (
    Channel,
    Conversation,
    Instrument,
    Kelurahan,
    MessageKind,
    RiskAssessment,
    RiskLevel,
    Sender,
    User,
)
from app.pipeline import Models, llm, process
from app.pipeline.normalize import Normalized, compile_pattern
from app.pipeline.responder import BANK, CrisisCard, Hotline, Reply, ReplyContext, crisis_reply
from app.services import chat as store
from app.settings import CONFIG_DIR

SCREEN = yaml.safe_load((CONFIG_DIR / "screening.yaml").read_text("utf-8"))
_DIALOG = BANK["dialog"]
_INTENTS = {k: [compile_pattern(w) for w in v] for k, v in _DIALOG["intents"].items()}
STATE_TTL = 7 * 24 * 3600
SKIP_LABEL = "Lewati"  # bubble jawaban saat "Lewati dulu" ditekan (teks desain)

Action = Literal["answer", "skip", "stop", "continue", "connect"]


class ScreeningQuestion(BaseModel):
    instrument: Instrument
    item: int
    n: int
    total: int
    text: str
    options: list[str]


class BotMessage(BaseModel):
    sender: Sender = Sender.bot
    kind: MessageKind = MessageKind.text
    text: str = ""


class ChatTurn(BaseModel):
    messages: list[BotMessage] = []
    card: CrisisCard | None = None
    hotlines: list[Hotline] = []
    offer_connect: bool = False
    connected: bool = False
    screening: ScreeningQuestion | None = None  # kartu pertanyaan yang sedang aktif
    followup_offer: bool = False  # tombol "Lanjut" / "Berhenti" setelah PHQ-4 positif
    client_action: Literal["open_napas"] | None = None


class DialogError(Exception):
    """Aksi tidak cocok dengan state (mis. menjawab padahal tidak ada pertanyaan)."""


@dataclass
class DialogState:
    turn: int = 0
    connected: bool = False
    stage: str = "none"  # none | phq4 | followup_offer | full
    queue: list[list[str | int]] = field(default_factory=list)  # [[instrumen, item], ...]
    current: list[str | int] | None = None
    answers: dict[str, dict[str, int | None]] = field(
        default_factory=lambda: {"phq9": {}, "gad7": {}}
    )
    total: int = 0
    asked: int = 0

    def int_answers(self) -> dict[str, dict[int, int | None]]:
        return {k: {int(i): v for i, v in a.items()} for k, a in self.answers.items()}

    def reset_screening(self) -> None:
        fresh = DialogState(turn=self.turn, connected=self.connected)
        self.__dict__.update(asdict(fresh))


def _key(user_id: uuid.UUID) -> str:
    return f"dialog:{user_id}"


async def load_state(r: Redis, user_id: uuid.UUID) -> DialogState:
    raw = await r.get(_key(user_id))
    return DialogState(**json.loads(raw)) if raw else DialogState()


async def mark_connected(r: Redis, user_id: uuid.UUID) -> None:
    """Pendamping sudah menyapa → chat remaja tidak menawarkan "hubungkan" lagi."""
    st = await load_state(r, user_id)
    st.connected = True
    await r.set(_key(user_id), json.dumps(asdict(st)), ex=STATE_TTL)


def _from_reply(reply: Reply) -> ChatTurn:
    messages = [BotMessage(text=t) for t in reply.messages]
    if reply.card:
        messages.append(BotMessage(kind=MessageKind.crisis_card))
    return ChatTurn(
        messages=messages,
        card=reply.card,
        hotlines=list(reply.hotlines),
        offer_connect=reply.offer_connect,
    )


def _has_intent(norm: Normalized, name: str) -> bool:
    return any(p.search(norm.text) for p in _INTENTS[name])


def question_of(st: DialogState) -> ScreeningQuestion | None:
    if st.current is None:
        return None
    instrument, item = str(st.current[0]), int(st.current[1])
    return ScreeningQuestion(
        instrument=Instrument(instrument),
        item=item,
        n=st.asked,
        total=st.total,
        text=SCREEN["stem"] + SCREEN["items"][instrument][item],
        options=SCREEN["options"],
    )


class Dialog:
    def __init__(
        self,
        session: AsyncSession,
        r: Redis,
        user: User,
        models: Models,
        channel: Channel = Channel.web,
    ) -> None:
        self.session, self.r, self.user, self.models, self.channel = (
            session,
            r,
            user,
            models,
            channel,
        )

    # ---------- entry points ----------

    async def handle_text(self, text: str) -> ChatTurn:
        st = await load_state(self.r, self.user.id)
        conv = await store.conversation_for(self.session, self.user, self.channel)
        history = await self._llm_history() if llm.enabled() else []  # sebelum pesan ini disimpan
        msg = await store.save_message(self.session, conv, Sender.remaja, text)
        ctx = await self._ctx(st)
        ratio = await store.negative_day_ratio(self.session, self.user)
        analysis, reply = await process(text, ctx, neg_day_ratio=ratio, models=self.models)
        st.turn += 1

        if analysis is None:  # pipeline gagal → fallback_safe (sudah berisi hotline)
            turn = _from_reply(reply)
        else:
            assessment = await store.record_analysis(self.session, self.user, msg, analysis)
            await store.upsert_case(self.session, self.user, analysis.level, assessment)
            green = analysis.level == RiskLevel.hijau
            if analysis.level == RiskLevel.merah:
                await self._end_screening(st)
                turn = _from_reply(reply)
            elif green and st.stage == "none" and _has_intent(analysis.normalized, "skrining"):
                turn = self._start_screening(st)
            elif green and _has_intent(analysis.normalized, "napas"):
                turn = ChatTurn(
                    messages=[BotMessage(text=_DIALOG["napas"])], client_action="open_napas"
                )
            else:
                turn = _from_reply(reply)
                # Hanya hijau boleh LLM (§6.3–6.4); gagal/ditolak = tetap balasan bank di atas.
                if green and not await store.has_open_high_risk_case(self.session, self.user):
                    free = await llm.green_reply(history, text, self.user.pseudonym)
                    if free:
                        turn = ChatTurn(messages=[BotMessage(text=free)])
        if turn.screening is None:  # kartu skrining tetap tampil kalau masih berjalan
            turn.screening = question_of(st)
        turn.followup_offer = turn.followup_offer or st.stage == "followup_offer"
        return await self._finish_turn(conv, st, turn)

    async def handle_action(self, action: Action, value: int | None = None) -> ChatTurn:
        st = await load_state(self.r, self.user.id)
        conv = await store.conversation_for(self.session, self.user, self.channel)
        ctx = await self._ctx(st)

        if action == "connect":
            turn = await self._connect(st, ctx)
        elif action in ("answer", "skip"):
            if st.current is None:
                raise DialogError("Tidak ada pertanyaan yang sedang aktif.")
            if action == "answer" and (value is None or not 0 <= value <= 3):
                raise DialogError("Jawaban tidak valid.")
            answer = value if action == "answer" else None
            label = SCREEN["options"][answer] if answer is not None else SKIP_LABEL
            await store.save_message(self.session, conv, Sender.remaja, label)
            turn = await self._answer(st, ctx, answer)
        elif action == "continue":
            if st.stage != "followup_offer":
                raise DialogError("Tidak ada skrining lanjutan.")
            answers = st.int_answers()
            st.queue = [
                [instrument.value, item]
                for instrument in screening.followup_needed(answers["phq9"], answers["gad7"])
                for item in screening.remaining_items(instrument, answers[instrument.value])
            ]
            st.stage, st.total, st.asked = "full", len(st.queue), 0
            turn = ChatTurn(screening=self._next_question(st))
        else:  # stop
            await self._end_screening(st)
            turn = ChatTurn(messages=[BotMessage(text=SCREEN["stop"])])
        return await self._finish_turn(conv, st, turn)

    # ---------- skrining ----------

    def _start_screening(self, st: DialogState) -> ChatTurn:
        st.reset_screening()
        st.stage = "phq4"
        st.queue = [[instrument.value, item] for instrument, item in screening.PHQ4_ORDER]
        st.total = len(st.queue)
        return ChatTurn(
            messages=[BotMessage(text=SCREEN["intro"])], screening=self._next_question(st)
        )

    def _next_question(self, st: DialogState) -> ScreeningQuestion | None:
        st.current = st.queue.pop(0) if st.queue else None
        if st.current is not None:
            st.asked += 1
        return question_of(st)

    async def _answer(self, st: DialogState, ctx: ReplyContext, answer: int | None) -> ChatTurn:
        assert st.current is not None
        instrument, item = str(st.current[0]), int(st.current[1])
        st.answers[instrument][str(item)] = answer
        if screening.is_crisis_answer(Instrument(instrument), item, answer):
            await self._end_screening(st)
            await self._flag(RiskLevel.merah, ["phq9_item9"])
            return _from_reply(crisis_reply(ctx))
        question = self._next_question(st)
        if question is not None:
            return ChatTurn(screening=question)
        answers = st.int_answers()
        if st.stage == "phq4" and screening.followup_needed(answers["phq9"], answers["gad7"]):
            st.stage = "followup_offer"
            return ChatTurn(
                messages=[BotMessage(text=SCREEN["followup_offer"])], followup_offer=True
            )
        return await self._complete(st, ctx)

    async def _complete(self, st: DialogState, ctx: ReplyContext) -> ChatTurn:
        answers = st.int_answers()
        phq, gad = answers["phq9"], answers["gad7"]
        level = screening.screening_level(phq, gad)
        key = screening.result_key(screening.phq4_total(phq, gad))
        if level in (RiskLevel.oranye, RiskLevel.merah):
            key = "high"
        elif level == RiskLevel.kuning and key == "low":
            key = "mid"
        await self._end_screening(st)
        if level is not None:
            await self._flag(level, ["skrining"])
        text = SCREEN["results"][key].format(kelurahan=ctx.kelurahan)
        return ChatTurn(
            messages=[BotMessage(text=f"{text}\n\n{SCREEN['disclaimer']}")],
            offer_connect=key == "high",
        )

    async def _end_screening(self, st: DialogState) -> None:
        if any(st.answers.values()):
            await store.save_screenings(self.session, self.user, st.int_answers())
        st.reset_screening()

    # ---------- lain-lain ----------

    async def _connect(self, st: DialogState, ctx: ReplyContext) -> ChatTurn:
        if st.connected:
            return ChatTurn()
        await self._flag(RiskLevel.oranye, ["minta_dihubungkan"])  # seperti prototipe
        st.connected = True
        return ChatTurn(messages=[BotMessage(text=_DIALOG["connect_ack"].format(**_fmt(ctx)))])

    async def _flag(self, level: RiskLevel, triggers: list[str]) -> None:
        """Asesmen tanpa pesan (skrining / minta pendamping). ter_score 0 = bukan dari TER."""
        assessment = RiskAssessment(
            user_id=self.user.id, level=level, ter_score=0.0, triggers=triggers
        )
        self.session.add(assessment)
        await self.session.flush()
        await store.upsert_case(self.session, self.user, level, assessment)

    async def _llm_history(self) -> list[llm.Turn]:
        """Giliran teks terakhir sebagai konteks LLM. Pesan pendamping & kartu krisis tidak ikut."""
        rows = await store.history(self.session, self.user, limit=llm.CFG["max_history"])
        return [
            ("user" if sender == Sender.remaja else "assistant", text)
            for _, sender, kind, text, _, _ in rows
            if kind == MessageKind.text and sender != Sender.pendamping and text
        ]

    async def _ctx(self, st: DialogState) -> ReplyContext:
        kel = await self.session.get(Kelurahan, self.user.kelurahan_id)
        return ReplyContext(
            nickname=self.user.pseudonym or "kamu",
            kelurahan=kel.name if kel else "",
            turn=st.turn,
        )

    async def _finish_turn(self, conv: Conversation, st: DialogState, turn: ChatTurn) -> ChatTurn:
        for m in turn.messages:
            await store.save_message(self.session, conv, m.sender, m.text, m.kind)
        turn.connected = st.connected
        await self.session.commit()
        await self.r.set(_key(self.user.id), json.dumps(asdict(st)), ex=STATE_TTL)
        return turn


def _fmt(ctx: ReplyContext) -> dict[str, str]:
    return {"nama": ctx.nickname, "kelurahan": ctx.kelurahan}
