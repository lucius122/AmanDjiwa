"""Persistensi percakapan: pesan terenkripsi, asesmen risiko, kasus, lintasan 14 hari (§5, §7)."""

import uuid
from collections import defaultdict
from datetime import UTC, date, datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    Case,
    CaseStatus,
    Channel,
    Conversation,
    EmotionScore,
    Instrument,
    JournalEntry,
    Message,
    MessageKind,
    RiskAssessment,
    RiskLevel,
    Screening,
    Sender,
    User,
)
from app.pipeline import Analysis
from app.pipeline.ter import negative_day_ratio as day_ratio
from app.screening import gad7, phq9
from app.services.crypto import decrypt, encrypt

WIB = timezone(timedelta(hours=7), "WIB")  # batas hari = waktu Semarang (tanpa DST)
TRAJECTORY_DAYS = 14
GREETING = "Hai! Aku Djiwa. Gimana harimu hari ini?"  # teks desain
_RANK = {RiskLevel.hijau: 0, RiskLevel.kuning: 1, RiskLevel.oranye: 2, RiskLevel.merah: 3}
OPEN_STATUSES = (CaseStatus.baru, CaseStatus.ditangani)


async def conversation_for(session: AsyncSession, user: User, channel: Channel) -> Conversation:
    """Satu percakapan per remaja (web & Telegram nyambung). Dibuat bersama sapaan pertama."""
    conv = (
        await session.execute(select(Conversation).where(Conversation.user_id == user.id))
    ).scalar_one_or_none()
    if conv is None:
        conv = Conversation(user_id=user.id, channel=channel)
        session.add(conv)
        await session.flush()
        await save_message(session, conv, Sender.bot, GREETING)
    return conv


async def save_message(
    session: AsyncSession,
    conv: Conversation,
    sender: Sender,
    text: str,
    kind: MessageKind = MessageKind.text,
    author_id: uuid.UUID | None = None,
) -> Message:
    msg = Message(
        conversation_id=conv.id,
        sender=sender,
        kind=kind,
        author_id=author_id,
        encrypted_text=encrypt(text),
    )
    session.add(msg)
    await session.flush()
    return msg


async def record_analysis(
    session: AsyncSession, user: User, message: Message, analysis: Analysis
) -> RiskAssessment:
    triggers = sorted(analysis.crisis.categories) + sorted(analysis.markers.flags)
    if analysis.crisis.is_crisis and not analysis.crisis.categories:
        triggers.insert(0, "model_krisis")
    session.add(EmotionScore(message_id=message.id, scores=analysis.emotions.scores))
    assessment = RiskAssessment(
        user_id=user.id,
        message_id=message.id,
        level=analysis.level,
        ter_score=analysis.ter,
        triggers=triggers + [f"topik:{t}" for t in sorted(analysis.markers.topics)],
    )
    session.add(assessment)
    await session.flush()
    return assessment


async def upsert_case(
    session: AsyncSession, user: User, level: RiskLevel, assessment: RiskAssessment
) -> Case | None:
    """Kuning/oranye/merah → satu kasus terbuka per remaja; level hanya bisa naik.

    Naik level = status kembali "baru", supaya muncul lagi di atas antrian pendamping.
    """
    if level == RiskLevel.hijau:
        return None
    assert user.kelurahan_id is not None
    case = (
        await session.execute(
            select(Case)
            .where(Case.user_id == user.id, Case.status.in_(OPEN_STATUSES))
            .order_by(Case.created_at.desc())
            .limit(1)
        )
    ).scalar_one_or_none()
    if case is None:
        case = Case(user_id=user.id, kelurahan_id=user.kelurahan_id, level=level)
        session.add(case)
        await session.flush()
    elif _RANK[level] > _RANK[case.level]:
        case.level = level
        case.status = CaseStatus.baru
    assessment.case_id = case.id
    return case


async def has_open_high_risk_case(session: AsyncSession, user: User) -> bool:
    """Kasus oranye/merah masih terbuka → LLM tidak dipakai, bank respons saja (konservatif)."""
    found = await session.execute(
        select(Case.id).where(
            Case.user_id == user.id,
            Case.status.in_(OPEN_STATUSES),
            Case.level.in_([RiskLevel.oranye, RiskLevel.merah]),
        )
    )
    return found.first() is not None


async def negative_day_ratio(session: AsyncSession, user: User, today: date | None = None) -> float:
    """Porsi hari dengan emosi dominan negatif dalam 14 hari (jurnal menang atas obrolan)."""
    return day_ratio([emotion for emotion, _ in await daily_emotions(session, user.id, today)])


async def daily_emotions(
    session: AsyncSession, user_id: uuid.UUID, today: date | None = None
) -> list[tuple[str | None, int | None]]:
    """14 hari terakhir (lama → baru): (emosi dominan, intensitas jurnal) per hari.

    Jurnal menang atas obrolan; intensitas hanya ada dari jurnal. (None, None) = tidak ada data.
    """
    today = today or datetime.now(WIB).date()
    since = today - timedelta(days=TRAJECTORY_DAYS - 1)
    journal = {
        d: (str(emotion), intensity)
        for d, emotion, intensity in (
            await session.execute(
                select(JournalEntry.entry_date, JournalEntry.emotion, JournalEntry.intensity).where(
                    JournalEntry.user_id == user_id, JournalEntry.entry_date >= since
                )
            )
        ).all()
    }
    local_day = func.date(func.timezone("Asia/Jakarta", Message.created_at))
    rows = await session.execute(
        select(local_day, EmotionScore.scores)
        .join(Message, Message.id == EmotionScore.message_id)
        .join(Conversation, Conversation.id == Message.conversation_id)
        .where(Conversation.user_id == user_id, local_day >= since)
    )
    chat: dict[date, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    for day, scores in rows.all():
        for label, value in scores.items():
            chat[day][label] += value
    days: list[tuple[str | None, int | None]] = []
    for i in range(TRAJECTORY_DAYS):
        d = since + timedelta(days=i)
        if d in journal:
            days.append(journal[d])
        elif d in chat:
            days.append((max(chat[d], key=lambda k: chat[d][k]), None))
        else:
            days.append((None, None))
    return days


async def save_screenings(
    session: AsyncSession, user: User, answers: dict[str, dict[int, int | None]]
) -> None:
    scorers = {Instrument.phq9: phq9.score, Instrument.gad7: gad7.score}
    for instrument, scorer in scorers.items():
        given = answers.get(instrument.value) or {}
        if not given:
            continue
        total = scorer(given)
        session.add(
            Screening(
                user_id=user.id,
                instrument=instrument,
                answers={str(k): v for k, v in given.items()},
                total=total,
                completed_at=datetime.now(UTC) if total is not None else None,
            )
        )


async def history(
    session: AsyncSession, user: User, limit: int = 100
) -> list[tuple[uuid.UUID, Sender, MessageKind, str, datetime, str | None]]:
    """Pesan milik remaja ini saja (didekripsi), urut lama → baru. Elemen terakhir = nama penulis
    untuk pesan pendamping."""
    rows = await session.execute(
        select(Message, User.display_name)
        .join(Conversation, Conversation.id == Message.conversation_id)
        .outerjoin(User, User.id == Message.author_id)
        .where(Conversation.user_id == user.id)
        .order_by(Message.seq.desc())
        .limit(limit)
    )
    return [
        (m.id, m.sender, m.kind, decrypt(m.encrypted_text), m.created_at, author)
        for m, author in rows.all()[::-1]
    ]
