"""Admin kota pertama dari variabel environment (tanpa akses terminal ke server).

Hanya bekerja kalau BELUM ada satu pun admin kota, jadi variabel yang lupa dihapus tidak bisa
dipakai membuat admin baru lagi. Akun dibuat tanpa authenticator: login pertama memaksa pasang
authenticator + ganti password (alur yang sama dengan akun buatan admin kota).
"""

import logging

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.db import SessionLocal
from app.models import Role, User, UserStatus
from app.services.auth import hash_password
from app.settings import settings

log = logging.getLogger(__name__)
MIN_PASSWORD = 12


async def ensure_first_admin(sessions: async_sessionmaker[AsyncSession] = SessionLocal) -> bool:
    email = settings.bootstrap_admin_email.strip().lower()
    password = settings.bootstrap_admin_password
    if not email or not password:
        return False
    if len(password) < MIN_PASSWORD:
        log.error("bootstrap_admin_skipped reason=password_too_short min=%d", MIN_PASSWORD)
        return False
    async with sessions() as session:
        if (await session.execute(select(User.id).where(User.role == Role.admin_kota))).first():
            return False  # sudah ada admin kota → variabel diabaikan
        if (await session.execute(select(User.id).where(User.email == email))).first():
            log.error("bootstrap_admin_skipped reason=email_in_use")
            return False
        session.add(
            User(
                role=Role.admin_kota,
                email=email,
                display_name=settings.bootstrap_admin_name.strip() or "Admin Kota",
                password_hash=hash_password(password),
                status=UserStatus.active,
            )
        )
        try:
            await session.commit()
        except IntegrityError:  # dua instance start bersamaan: satu saja yang menang
            return False
    log.info("bootstrap_admin_created")  # tanpa email (§7)
    return True
