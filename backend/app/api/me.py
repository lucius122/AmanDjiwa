"""Profil remaja + hapus semua data (§7: DELETE /me = hard delete + cascade)."""

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import current_teen
from app.db import get_session
from app.models import Kelurahan, User, UserStatus

router = APIRouter(tags=["me"])


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
    if user.pseudonym is None:  # akun baru: lanjut ke langkah profil
        raise HTTPException(404, "Profil belum dibuat.")
    return await me_out(session, user)


@router.delete("/me", status_code=204)
async def delete_me(
    user: User = Depends(current_teen), session: AsyncSession = Depends(get_session)
) -> Response:
    # Satu DELETE; akun login (email terenkripsi + password), obrolan, jurnal, skrining, kasus,
    # consent, dst. ikut terhapus lewat FK CASCADE.
    await session.execute(delete(User).where(User.id == user.id))
    await session.commit()
    return Response(status_code=204)
