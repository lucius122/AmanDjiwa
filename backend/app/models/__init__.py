"""Skema DB (CLAUDE.md §8). Penghapusan data remaja mengandalkan ON DELETE CASCADE di DB."""

import enum
import uuid
from datetime import date, datetime
from typing import Any

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Identity,
    Index,
    Integer,
    LargeBinary,
    MetaData,
    SmallInteger,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    metadata = MetaData(
        naming_convention={
            "ix": "ix_%(column_0_label)s",
            "uq": "uq_%(table_name)s_%(column_0_name)s",
            "ck": "ck_%(table_name)s_%(constraint_name)s",
            "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
            "pk": "pk_%(table_name)s",
        }
    )


class Role(enum.StrEnum):
    remaja = "remaja"
    pendamping = "pendamping"
    konselor = "konselor"
    admin_kota = "admin_kota"


class UserStatus(enum.StrEnum):
    pending_guardian = "pending_guardian"
    active = "active"
    disabled = "disabled"


class ConsentStatus(enum.StrEnum):
    pending = "pending"
    approved = "approved"
    declined = "declined"
    revoked = "revoked"


class GuardianRelation(enum.StrEnum):
    orang_tua = "orang_tua"
    wali = "wali"


class Channel(enum.StrEnum):
    web = "web"
    telegram = "telegram"


class Sender(enum.StrEnum):
    remaja = "remaja"
    bot = "bot"
    pendamping = "pendamping"


class MessageKind(enum.StrEnum):
    text = "text"
    crisis_card = "crisis_card"  # kartu "Kamu nggak harus hadapi ini sendirian"


class RiskLevel(enum.StrEnum):
    hijau = "hijau"
    kuning = "kuning"
    oranye = "oranye"
    merah = "merah"


class CaseStatus(enum.StrEnum):
    baru = "baru"
    ditangani = "ditangani"
    selesai = "selesai"
    dirujuk = "dirujuk"


class Instrument(enum.StrEnum):
    phq9 = "phq9"
    gad7 = "gad7"


class Emotion(enum.StrEnum):
    """Label model (CLAUDE.md §3 ML). Di UI: malu_bersalah = "Malu", netral = "Biasa aja"."""

    sedih = "sedih"
    cemas = "cemas"
    marah = "marah"
    malu_bersalah = "malu_bersalah"
    senang = "senang"
    netral = "netral"


def _enum(e: type[enum.StrEnum]) -> SAEnum:
    # VARCHAR + CHECK, bukan enum native Postgres: nilai baru cukup ubah CHECK di migrasi.
    return SAEnum(
        e,
        name=e.__name__.lower(),
        native_enum=False,
        create_constraint=True,
        length=24,
        values_callable=lambda x: [m.value for m in x],
    )


def _uuid_pk() -> Mapped[uuid.UUID]:
    return mapped_column(primary_key=True, default=uuid.uuid4)


def _user_fk(*, index: bool = True) -> Mapped[uuid.UUID]:
    return mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=index)


def _created() -> Mapped[datetime]:
    return mapped_column(DateTime(timezone=True), server_default=func.now())


class Kelurahan(Base):
    __tablename__ = "kelurahan"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(64), unique=True)


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("(role = 'remaja') = (auth_id IS NOT NULL)", name="remaja_has_auth_id"),
        CheckConstraint(
            "role = 'remaja' OR (email IS NOT NULL AND password_hash IS NOT NULL)",
            name="staff_has_login",
        ),
        CheckConstraint(
            "role NOT IN ('remaja', 'pendamping') OR kelurahan_id IS NOT NULL",
            name="scoped_role_has_kelurahan",
        ),
        CheckConstraint("avatar BETWEEN 0 AND 7", name="avatar_range"),
    )

    id: Mapped[uuid.UUID] = _uuid_pk()
    role: Mapped[Role] = mapped_column(_enum(Role))
    status: Mapped[UserStatus] = mapped_column(_enum(UserStatus), default=UserStatus.active)
    kelurahan_id: Mapped[int | None] = mapped_column(ForeignKey("kelurahan.id"))
    created_at: Mapped[datetime] = _created()

    # remaja: identitas hanya nama samaran; email login disimpan Supabase, bukan di sini.
    auth_id: Mapped[str | None] = mapped_column(String(64), unique=True)
    pseudonym: Mapped[str | None] = mapped_column(String(20))
    avatar: Mapped[int | None] = mapped_column(SmallInteger)
    birth_year: Mapped[int | None] = mapped_column(SmallInteger)
    assented_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # staf
    email: Mapped[str | None] = mapped_column(String(254), unique=True)
    display_name: Mapped[str | None] = mapped_column(String(64))
    password_hash: Mapped[str | None] = mapped_column(String(255))
    totp_secret_enc: Mapped[bytes | None] = mapped_column(LargeBinary)
    totp_last_step: Mapped[int] = mapped_column(BigInteger, default=0)
    # Preferensi dasbor staf (Pengaturan): notif_red, sound, compact.
    settings: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, server_default="{}")
    failed_logins: Mapped[int] = mapped_column(SmallInteger, default=0)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class GuardianConsent(Base):
    __tablename__ = "guardian_consents"
    id: Mapped[uuid.UUID] = _uuid_pk()
    user_id: Mapped[uuid.UUID] = _user_fk()
    token_hash: Mapped[str] = mapped_column(
        String(64), unique=True
    )  # sha256, token asli tak disimpan
    email_enc: Mapped[bytes] = mapped_column(LargeBinary)
    guardian_name_enc: Mapped[bytes | None] = mapped_column(LargeBinary)
    relation: Mapped[GuardianRelation | None] = mapped_column(_enum(GuardianRelation))
    status: Mapped[ConsentStatus] = mapped_column(
        _enum(ConsentStatus), default=ConsentStatus.pending
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = _created()


class ChannelLink(Base):
    __tablename__ = "channel_links"
    id: Mapped[uuid.UUID] = _uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True
    )
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True)
    linked_at: Mapped[datetime] = _created()


class Conversation(Base):
    __tablename__ = "conversations"
    id: Mapped[uuid.UUID] = _uuid_pk()
    user_id: Mapped[uuid.UUID] = _user_fk()
    channel: Mapped[Channel] = mapped_column(_enum(Channel))
    started_at: Mapped[datetime] = _created()


class Message(Base):
    __tablename__ = "messages"
    __table_args__ = (Index("ix_messages_conversation_created", "conversation_id", "created_at"),)
    id: Mapped[uuid.UUID] = _uuid_pk()
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE")
    )
    sender: Mapped[Sender] = mapped_column(_enum(Sender))
    kind: Mapped[MessageKind] = mapped_column(_enum(MessageKind), default=MessageKind.text)
    author_id: Mapped[uuid.UUID | None] = mapped_column(  # pendamping yang menulis (nama di chat)
        ForeignKey("users.id", ondelete="SET NULL")
    )
    # Urutan pasti: now() Postgres sama untuk semua baris dalam satu transaksi.
    seq: Mapped[int] = mapped_column(BigInteger, Identity(), unique=True)
    encrypted_text: Mapped[bytes] = mapped_column(LargeBinary)
    created_at: Mapped[datetime] = _created()


class EmotionScore(Base):
    __tablename__ = "emotion_scores"
    message_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("messages.id", ondelete="CASCADE"), primary_key=True
    )
    scores: Mapped[dict[str, float]] = mapped_column(JSONB)  # {label: 0..1} untuk 6 label


class RiskAssessment(Base):
    __tablename__ = "risk_assessments"
    id: Mapped[uuid.UUID] = _uuid_pk()
    user_id: Mapped[uuid.UUID] = _user_fk()
    message_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("messages.id", ondelete="CASCADE")
    )
    level: Mapped[RiskLevel] = mapped_column(_enum(RiskLevel))
    ter_score: Mapped[float] = mapped_column(Float)
    case_id: Mapped[uuid.UUID | None] = mapped_column(  # pemicu kasus = yang boleh dibaca staf
        ForeignKey("cases.id", ondelete="SET NULL"), index=True
    )
    triggers: Mapped[list[str]] = mapped_column(JSONB, default=list)
    created_at: Mapped[datetime] = _created()


class Screening(Base):
    __tablename__ = "screenings"
    id: Mapped[uuid.UUID] = _uuid_pk()
    user_id: Mapped[uuid.UUID] = _user_fk()
    instrument: Mapped[Instrument] = mapped_column(_enum(Instrument))
    answers: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)  # {"1": 0..3, ...}
    total: Mapped[int | None] = mapped_column(SmallInteger)  # None = "Belum lengkap"
    created_at: Mapped[datetime] = _created()
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Case(Base):
    __tablename__ = "cases"
    __table_args__ = (Index("ix_cases_kelurahan_status", "kelurahan_id", "status"),)
    id: Mapped[uuid.UUID] = _uuid_pk()
    user_id: Mapped[uuid.UUID] = _user_fk()
    kelurahan_id: Mapped[int] = mapped_column(ForeignKey("kelurahan.id"))  # untuk filter scope
    level: Mapped[RiskLevel] = mapped_column(_enum(RiskLevel))
    status: Mapped[CaseStatus] = mapped_column(_enum(CaseStatus), default=CaseStatus.baru)
    assigned_to: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    referred_to: Mapped[str | None] = mapped_column(String(120))
    # Email peringatan kasus merah sudah terkirim (jobs.red_alerts). Null = belum.
    red_alerted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    handled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )  # pertama dihubungi
    created_at: Mapped[datetime] = _created()
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class CaseNote(Base):
    __tablename__ = "case_notes"
    id: Mapped[uuid.UUID] = _uuid_pk()
    case_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("cases.id", ondelete="CASCADE"), index=True
    )
    author_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    text_enc: Mapped[bytes] = mapped_column(LargeBinary)
    created_at: Mapped[datetime] = _created()


class JournalEntry(Base):
    __tablename__ = "journal_entries"
    __table_args__ = (
        UniqueConstraint("user_id", "entry_date"),  # satu entri per hari ("Perbarui jurnal")
        CheckConstraint("intensity BETWEEN 1 AND 5", name="intensity_range"),
    )
    id: Mapped[uuid.UUID] = _uuid_pk()
    user_id: Mapped[uuid.UUID] = _user_fk(index=False)
    entry_date: Mapped[date] = mapped_column(Date)
    emotion: Mapped[Emotion] = mapped_column(_enum(Emotion))
    intensity: Mapped[int] = mapped_column(SmallInteger)
    note_enc: Mapped[bytes | None] = mapped_column(LargeBinary)
    created_at: Mapped[datetime] = _created()


class FollowUp(Base):
    """Agenda staf (halaman "Jadwal"). Boleh tanpa kasus (mis. supervisi).

    Judul dienkripsi: bisa memuat nama samaran / detail kasus.
    """

    __tablename__ = "follow_ups"
    id: Mapped[uuid.UUID] = _uuid_pk()
    staff_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    case_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("cases.id", ondelete="CASCADE"))
    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    title_enc: Mapped[bytes] = mapped_column(LargeBinary)
    created_at: Mapped[datetime] = _created()


class AuditLog(Base):
    """Jejak akses staf. case_id sengaja tanpa FK: log tetap ada walau data remaja dihapus."""

    __tablename__ = "audit_logs"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    actor_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    action: Mapped[str] = mapped_column(String(48))
    case_id: Mapped[uuid.UUID | None]
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
