"""Profil remaja + hapus semua data (§7: DELETE /me = hard delete + cascade)."""

import logging

import httpx
from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import current_teen
from app.db import get_session
from app.models import Kelurahan, User, UserStatus
from app.settings import settings

router = APIRouter(tags=["me"])
log = logging.getLogger(__name__)


class MeOut(BaseModel):
    pseudonym: str
    avatar: int
    kelurahan_id: int
    kelurahan_name: str
    birth_year: int
    status: UserStatus


async def me_out(session: AsyncSession, user: User) -> MeOut:
    kel = await session.get(Kelurahan, user.kelurahan_id)
    assert kel is not None and user.pseudonym is not None  # dijamin CHECK + assent
    return MeOut(
        pseudonym=user.pseudonym,
        avatar=user.avatar or 0,
        kelurahan_id=kel.id,
        kelurahan_name=kel.name,
        birth_year=user.birth_year or 0,
        status=user.status,
    )


@router.get("/me")
async def get_me(
    user: User = Depends(current_teen), session: AsyncSession = Depends(get_session)
) -> MeOut:
    return await me_out(session, user)


@router.delete("/me", status_code=204)
async def delete_me(
    user: User = Depends(current_teen), session: AsyncSession = Depends(get_session)
) -> Response:
    user_id, auth_id = user.id, user.auth_id
    # Satu DELETE; obrolan, jurnal, skrining, kasus, consent, dst. ikut terhapus lewat FK CASCADE.
    await session.execute(delete(User).where(User.id == user_id))
    await session.commit()
    if auth_id:
        await _delete_auth_account(user_id, auth_id)
    return Response(status_code=204)


async def _delete_auth_account(user_id: object, auth_id: str) -> None:
    """Hapus juga akun login Supabase (berisi email). Gagal dicatat; data kita tetap terhapus."""
    key = settings.supabase_service_role_key
    if not (settings.supabase_url and key):
        log.warning("supabase_delete_skipped user_id=%s reason=not_configured", user_id)
        return
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            res = await client.delete(
                f"{settings.supabase_url}/auth/v1/admin/users/{auth_id}",
                headers={"apikey": key, "Authorization": f"Bearer {key}"},
            )
        if res.status_code >= 400 and res.status_code != 404:
            log.error("supabase_delete_failed user_id=%s status=%s", user_id, res.status_code)
    except httpx.HTTPError as e:
        log.error("supabase_delete_failed user_id=%s error=%s", user_id, type(e).__name__)
