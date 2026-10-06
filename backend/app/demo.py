"""Seed data demo hackathon — SEMUANYA SINTETIS (CLAUDE.md §10). Tidak pernah data remaja asli.

Penanda: remaja demo ber-auth_id `demo-…`, staf demo ber-email `demo-…@example.com`, jadi
`reset()` hanya menghapus baris demo. Seed hanya jalan kalau DEMO_MODE=true (§6.9: sistem
belum boleh dipakai remaja sungguhan; DB produksi tidak boleh tercampur data contoh).

Kasus di antrian pendamping memakai data contoh dari prototipe di design/.
"""

import random
import secrets
import time
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import pyotp
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    Case,
    CaseNote,
    CaseStatus,
    Channel,
    Conversation,
    Emotion,
    FollowUp,
    Instrument,
    JournalEntry,
    Kelurahan,
    Message,
    RiskAssessment,
    RiskLevel,
    Role,
    Screening,
    Sender,
    User,
    UserStatus,
)
from app.services.auth import hash_password
from app.services.chat import WIB
from app.services.crypto import decrypt, encrypt
from app.settings import settings

TEEN_PREFIX = "demo-"
STAFF_EMAIL = "demo-{}@example.com"
HOME = "Krobokan"  # kelurahan pendamping demo (sama dengan prototipe)
HIDDEN = ("Tambakharjo", "Kembangarum")  # < 10 pengguna → tampil "Disembunyikan"
DAYS = 91  # cukup untuk pilihan "3 bulan" di dasbor kota

# (nama samaran, umur, level, status, menit lalu, pesan pemicu, penanda, lintasan 14 hari,
#  emosi negatif dominan, PHQ-9, GAD-7, catatan) — dari seedCases() di prototipe.
QUEUE = [
    ("Langit Biru", 16, RiskLevel.merah, CaseStatus.baru, 12,
     ["rasanya semuanya selalu salah, aku nggak pernah bisa apa-apa", "mending aku ngilang aja"],
     ["ide_bunuh_diri", "kata_absolut", "putus_asa"],
     [1, 0, 0, -1, 0, -1, -1, -2, -1, -2, -2, -1, -2, -2], Emotion.sedih, 19, 13, None),
    ("Kopi Susu", 17, RiskLevel.oranye, CaseStatus.baru, 60,
     ["di rumah ribut terus, aku nggak bisa tidur"], ["gangguan_tidur", "topik:keluarga"],
     [0, 0, -1, 0, -1, -1, 0, -1, 0, -1, -1, 0, -1, -1], Emotion.marah, 12, 9, None),
    ("Awan Teduh", 14, RiskLevel.oranye, CaseStatus.ditangani, 720,
     ["temen-temen di kelas pada ngetawain aku lagi"], ["menarik_diri", "topik:pertemanan"],
     [0, -1, -1, 0, -1, -1, -1, 0, -1, -1, 0, 0, -1, 0], Emotion.cemas, 10, 14,
     "Sudah chat, jadwal ketemu Rabu sore di balai RW."),
    ("Mie Ayam", 16, RiskLevel.kuning, CaseStatus.baru, 840,
     ["takut banget nilai rapor jelek"], ["topik:akademik"],
     [1, 0, 0, 1, 0, -1, 0, 0, -1, 0, 0, 1, 0, -1], Emotion.cemas, 7, 8, None),
    ("Pelangi", 13, RiskLevel.kuning, CaseStatus.ditangani, 1020,
     ["nggak ada yang ngajak main"], ["kesepian"],
     [1, 1, 0, 0, -1, 0, 1, 0, 0, -1, 0, 1, 0, 0], Emotion.sedih, 6, 5, None),
    ("Kucing Oren", 18, RiskLevel.kuning, CaseStatus.selesai, 2880,
     ["bingung mau kuliah di mana"], ["topik:akademik"],
     [0, -1, 0, 0, -1, 0, 0, 1, 0, 1, 1, 0, 1, 1], Emotion.cemas, 5, 6,
     "Diarahkan ke BK sekolah. Kondisi stabil."),
]  # fmt: skip

_NAMES = ["Bintang", "Bulan", "Ombak", "Daun", "Senja", "Hujan", "Kopi", "Teh", "Gerimis", "Embun"]
_WORDS = ["Pagi", "Malam", "Teduh", "Cerah", "Kecil", "Manis", "Hijau", "Jingga", "Sunyi", "Riang"]
_TOPICS = ["akademik"] * 34 + ["keluarga"] * 22 + ["pertemanan"] * 18 + ["percintaan"] * 11
_TOPICS += ["citra_diri"] * 9 + ["ekonomi"] * 6
_EMOS = [Emotion.senang] * 28 + [Emotion.cemas] * 24 + [Emotion.sedih] * 16
_EMOS += [Emotion.netral] * 25 + [Emotion.marah] * 4 + [Emotion.malu_bersalah] * 3


@dataclass
class StaffLogin:
    role: Role
    email: str
    password: str
    otpauth: str


def _answers(total: int, items: int) -> dict[str, int]:
    """Bagi skor total ke item 0–3 (item terakhir PHQ-9 = 0: bukan sinyal krisis)."""
    out, left = {}, total
    for i in range(1, items + 1):
        out[str(i)] = 0 if items == 9 and i == 9 else min(3, left)
        left -= out[str(i)]
    return out


def _next(weekday: int, hour: int, minute: int = 0) -> datetime:
    today = datetime.now(WIB)
    days = (weekday - today.weekday()) % 7 or 7
    return (today + timedelta(days=days)).replace(hour=hour, minute=minute, second=0, microsecond=0)


async def _staff(session: AsyncSession, role: Role, name: str, kel: int | None) -> StaffLogin:
    email = STAFF_EMAIL.format(role.value.replace("_", "-"))
    password = secrets.token_urlsafe(12)
    secret = pyotp.random_base32()
    session.add(
        User(
            role=role,
            email=email,
            display_name=name,
            password_hash=hash_password(password),
            totp_secret_enc=encrypt(secret),
            kelurahan_id=kel,
        )
    )
    uri = pyotp.TOTP(secret).provisioning_uri(name=email, issuer_name="AmanDjiwa Demo")
    return StaffLogin(role, email, password, uri)


def _teen(name: str, kel: int, birth_year: int) -> User:
    return User(
        role=Role.remaja,
        auth_id=f"{TEEN_PREFIX}{uuid.uuid4().hex}",
        pseudonym=name,
        avatar=random.randrange(8),
        kelurahan_id=kel,
        birth_year=birth_year,
        status=UserStatus.active,
        assented_at=datetime.now(UTC),
    )


async def _queue(session: AsyncSession, kel: int, pendamping: User) -> None:
    now = datetime.now(UTC)
    today = datetime.now(WIB).date()
    for name, age, level, status, ago, texts, triggers, traj, neg, phq, gad, note in QUEUE:
        teen = _teen(name, kel, today.year - age)
        session.add(teen)
        await session.flush()
        conv = Conversation(user_id=teen.id, channel=Channel.web)
        session.add(conv)
        await session.flush()
        at = now - timedelta(minutes=ago)
        case = Case(user_id=teen.id, kelurahan_id=kel, level=level, status=status, created_at=at)
        if status != CaseStatus.baru:
            case.handled_at, case.assigned_to = at + timedelta(minutes=9), pendamping.id
        session.add(case)
        await session.flush()
        for i, text in enumerate(texts):
            sent = at - timedelta(minutes=2 * (len(texts) - 1 - i))
            msg = Message(
                conversation_id=conv.id,
                sender=Sender.remaja,
                encrypted_text=encrypt(text),
                created_at=sent,
            )
            session.add(msg)
            await session.flush()
            session.add(
                RiskAssessment(
                    user_id=teen.id,
                    message_id=msg.id,
                    case_id=case.id,
                    level=level,
                    ter_score=0.8,
                    triggers=triggers,
                    created_at=sent,
                )
            )
        for d, v in enumerate(traj):
            emotion = Emotion.senang if v > 0 else Emotion.netral if v == 0 else neg
            session.add(
                JournalEntry(
                    user_id=teen.id,
                    entry_date=today - timedelta(days=13 - d),
                    emotion=emotion,
                    intensity=5 if abs(v) == 2 else 3,
                )
            )
        for inst, total, items in ((Instrument.phq9, phq, 9), (Instrument.gad7, gad, 7)):
            session.add(
                Screening(
                    user_id=teen.id,
                    instrument=inst,
                    answers=_answers(total, items),
                    total=total,
                    completed_at=at,
                )
            )
        if note:
            session.add(CaseNote(case_id=case.id, author_id=pendamping.id, text_enc=encrypt(note)))
    session.add_all(
        FollowUp(staff_id=pendamping.id, scheduled_at=s, ends_at=e, title_enc=encrypt(t))
        for t, s, e in (
            ("Ketemu Awan Teduh · balai RW 03", _next(2, 16), _next(2, 17)),
            ("Follow-up chat Pelangi", _next(3, 19), None),
            ("Supervisi bersama konselor Puskesmas", _next(5, 9), _next(5, 11)),
        )
    )


async def _population(session: AsyncSession, kels: list[Kelurahan], rnd: random.Random) -> None:
    """Remaja latar untuk agregat dasbor kota (± 300 orang, 13 minggu)."""
    now = datetime.now(UTC)
    today = datetime.now(WIB).date()
    for kel in kels:
        n = rnd.randint(5, 8) if kel.name in HIDDEN else rnd.randint(12, 34)
        risk = rnd.uniform(0.04, 0.2)  # porsi oranye+merah per kelurahan
        for _ in range(n):
            name = f"{rnd.choice(_NAMES)} {rnd.choice(_WORDS)}"
            teen = _teen(name, kel.id, today.year - rnd.randint(13, 19))
            session.add(teen)
            await session.flush()
            conv = Conversation(user_id=teen.id, channel=Channel.web)
            session.add(conv)
            await session.flush()
            for _ in range(rnd.randint(1, 6)):
                at = now - timedelta(days=rnd.randint(0, DAYS - 1), hours=rnd.randint(0, 20))
                session.add(
                    Message(
                        conversation_id=conv.id,
                        sender=Sender.remaja,
                        encrypted_text=encrypt("(pesan demo)"),
                        created_at=at,
                    )
                )
                topic = [f"topik:{rnd.choice(_TOPICS)}"] if rnd.random() < 0.6 else []
                session.add(
                    RiskAssessment(
                        user_id=teen.id,
                        level=RiskLevel.hijau,
                        ter_score=0.1,
                        triggers=topic,
                        created_at=at,
                    )
                )
            x = rnd.random()
            level = (
                RiskLevel.merah
                if x < risk * 0.35
                else RiskLevel.oranye if x < risk else RiskLevel.kuning if x < risk + 0.2 else None
            )
            if level:
                await _flagged(session, teen, kel, level, rnd)
            for d in rnd.sample(range(DAYS), rnd.randint(4, 24)):
                session.add(
                    JournalEntry(
                        user_id=teen.id,
                        entry_date=today - timedelta(days=d),
                        emotion=rnd.choice(_EMOS),
                        intensity=rnd.randint(1, 5),
                    )
                )


async def _flagged(
    session: AsyncSession, teen: User, kel: Kelurahan, level: RiskLevel, rnd: random.Random
) -> None:
    at = datetime.now(UTC) - timedelta(days=rnd.randint(1, DAYS - 1))
    triggers = {RiskLevel.merah: ["ide_bunuh_diri"], RiskLevel.oranye: ["putus_asa"]}
    ra = RiskAssessment(
        user_id=teen.id,
        level=level,
        ter_score=0.6,
        triggers=triggers.get(level, ["ruminasi"]),
        created_at=at,
    )
    session.add(ra)
    if level == RiskLevel.kuning:
        return
    # Antrian pendamping demo hanya berisi kasus dari prototipe; kasus latar di sana sudah ditutup.
    closed = [CaseStatus.selesai, CaseStatus.dirujuk]
    status = rnd.choice(closed if kel.name == HOME else [*closed, CaseStatus.ditangani])
    case = Case(
        user_id=teen.id,
        kelurahan_id=kel.id,
        level=level,
        status=status,
        created_at=at,
        handled_at=at + timedelta(minutes=rnd.choice([3, 6, 9, 12, 14, 22, 35])),
        referred_to="Puskesmas Krobokan" if status == CaseStatus.dirujuk else None,
    )
    session.add(case)
    await session.flush()
    ra.case_id = case.id


async def seed(session: AsyncSession) -> list[StaffLogin]:
    if not settings.demo_mode:
        raise RuntimeError("Seed demo hanya boleh dengan DEMO_MODE=true (bukan DB produksi).")
    await reset(session)
    kels = list((await session.execute(select(Kelurahan).order_by(Kelurahan.id))).scalars())
    home = next(k for k in kels if k.name == HOME)
    logins = [
        await _staff(session, Role.pendamping, "Kak Dimas P.", home.id),
        await _staff(session, Role.konselor, "Kak Sari (Konselor)", None),
        await _staff(session, Role.admin_kota, "Dinkes Kota", None),
    ]
    await session.flush()
    pendamping = (
        await session.execute(select(User).where(User.email == logins[0].email))
    ).scalar_one()
    await _queue(session, home.id, pendamping)
    await _population(session, kels, random.Random(2026))
    await session.commit()
    return logins


async def current_code(session: AsyncSession, role: Role) -> tuple[str, int]:
    """(kode TOTP sekarang, sisa detik) untuk akun staf DEMO: presentasi tanpa authenticator.

    Hanya mencari email demo-…@example.com, jadi 2FA akun staf asli tidak bisa dilewati lewat sini.
    """
    email = STAFF_EMAIL.format(role.value.replace("_", "-"))
    secret_enc = (
        await session.execute(select(User.totp_secret_enc).where(User.email == email))
    ).scalar_one_or_none()
    if secret_enc is None:
        raise RuntimeError("Akun demo belum ada. Jalankan seed-demo dulu.")
    totp = pyotp.TOTP(decrypt(secret_enc))
    return totp.now(), int(totp.interval - time.time() % totp.interval)


async def reset(session: AsyncSession) -> int:
    """Hapus HANYA data demo (cascade ke pesan, jurnal, kasus, jadwal)."""
    teens = await session.execute(delete(User).where(User.auth_id.like(f"{TEEN_PREFIX}%")))
    await session.execute(delete(User).where(User.email.like(STAFF_EMAIL.format("%"))))
    await session.commit()
    return int(teens.rowcount)  # type: ignore[attr-defined]
