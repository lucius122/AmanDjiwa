"""Dasbor kota: hanya admin_kota, hanya agregat, sel < 10 pengguna disembunyikan (§7)."""

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from httpx import AsyncClient

from app.models import (
    Case,
    CaseStatus,
    Emotion,
    JournalEntry,
    RiskAssessment,
    RiskLevel,
    Role,
    User,
)
from app.services.chat import WIB
from tests.conftest import KROBOKAN, MANYARAN, TestSession, bearer, make_staff, staff_login

pytestmark = pytest.mark.anyio
H, K, OR, M = RiskLevel.hijau, RiskLevel.kuning, RiskLevel.oranye, RiskLevel.merah


async def _teens(
    kel: int,
    levels: list[RiskLevel],
    topics: list[str] | None = None,
    journal: list[Emotion] | None = None,
) -> list[uuid.UUID]:
    """Remaja sintetis + satu asesmen hari ini per orang (opsional topik & jurnal)."""
    ids = []
    async with TestSession() as s:
        for i, level in enumerate(levels):
            u = User(
                role=Role.remaja,
                auth_id=uuid.uuid4().hex,
                pseudonym=f"Anon{i}",
                avatar=0,
                kelurahan_id=kel,
                birth_year=2009,
            )
            s.add(u)
            await s.flush()
            triggers = [f"topik:{topics[i]}"] if topics else []
            s.add(RiskAssessment(user_id=u.id, level=level, ter_score=0.0, triggers=triggers))
            if journal:
                today = datetime.now(WIB).date()
                s.add(JournalEntry(user_id=u.id, entry_date=today, emotion=journal[i], intensity=3))
            ids.append(u.id)
        await s.commit()
    return ids


async def _staff(client: AsyncClient, role: Role, kel: int | None = None) -> dict[str, str]:
    email = f"{role.value}@example.com"
    secret = await make_staff(role, kel, email=email)
    return bearer((await staff_login(client, secret, email=email))["access_token"])


async def _aggregate(client: AsyncClient, h: dict[str, str]) -> dict[str, Any]:
    r = await client.get("/dashboard/aggregate", headers=h)
    assert r.status_code == 200, r.text
    body: dict[str, Any] = r.json()
    return body


def _kel(body: dict[str, Any], kel_id: int) -> dict[str, Any]:
    found: dict[str, Any] = next(k for k in body["kelurahan"] if k["id"] == kel_id)
    return found


async def test_only_admin_kota(client: AsyncClient) -> None:
    for role, kel in ((Role.pendamping, KROBOKAN), (Role.konselor, None)):
        h = await _staff(client, role, kel)
        assert (await client.get("/dashboard/aggregate", headers=h)).status_code == 403
    assert (await client.get("/dashboard/aggregate")).status_code == 401


async def test_small_cells_hidden_and_no_individual_rows(client: AsyncClient) -> None:
    ids = await _teens(KROBOKAN, [H] * 5 + [K] * 2 + [OR] * 2 + [M])
    ids += await _teens(MANYARAN, [M] * 9)  # 9 pengguna → disembunyikan
    r = await client.get("/dashboard/aggregate", headers=await _staff(client, Role.admin_kota))
    body = r.json()
    krobokan = _kel(body, KROBOKAN)
    assert (krobokan["users"], krobokan["risk_pct"]) == (10, 30)
    assert krobokan["levels"] == {"hijau": 50, "kuning": 20, "oranye": 20, "merah": 10}
    manyaran = _kel(body, MANYARAN)
    assert manyaran["users"] is None and manyaran["risk_pct"] is None and manyaran["levels"] is None
    assert body["kpis"]["active_users"] == 19
    assert body["min_cell"] == 10
    assert "Anon" not in r.text and not any(str(i) in r.text for i in ids)


async def test_everything_hidden_below_k(client: AsyncClient) -> None:
    await _teens(KROBOKAN, [M] * 9, topics=["keluarga"] * 9, journal=[Emotion.sedih] * 9)
    body = await _aggregate(client, await _staff(client, Role.admin_kota))
    assert body["kpis"] is None and body["topics"] == []
    assert all(w["pct"] is None for w in body["trend"])
    assert all(k["users"] is None for k in body["kelurahan"])


async def test_trend_and_topics(client: AsyncClient) -> None:
    await _teens(
        KROBOKAN,
        [H] * 10,
        topics=["akademik"] * 7 + ["keluarga"] * 3,
        journal=[Emotion.senang] * 6 + [Emotion.cemas] * 4,
    )
    body = await _aggregate(client, await _staff(client, Role.admin_kota))
    assert [(t["label"], t["pct"]) for t in body["topics"]] == [
        ("Akademik & ujian", 70),
        ("Keluarga", 30),
    ]
    assert len(body["trend"]) in (8, 9)  # 8 minggu terakhir (+ minggu berjalan)
    this_week = body["trend"][-1]["pct"]
    assert (this_week["senang"], this_week["cemas"], this_week["sedih"]) == (60, 40, 0)
    assert all(w["pct"] is None for w in body["trend"][:-1])  # minggu tanpa data


async def test_handled_and_referral_kpis(client: AsyncClient) -> None:
    ids = await _teens(KROBOKAN, [H] * 8 + [M] * 2)
    now = datetime.now(UTC)
    async with TestSession() as s:
        for uid, minutes, status in (
            (ids[8], 5, CaseStatus.ditangani),
            (ids[9], 40, CaseStatus.dirujuk),
        ):
            c = Case(
                user_id=uid,
                kelurahan_id=KROBOKAN,
                level=M,
                status=status,
                handled_at=now + timedelta(minutes=minutes),
            )
            s.add(c)
            await s.flush()
            s.add(RiskAssessment(user_id=uid, level=M, ter_score=1.0, case_id=c.id))
        await s.commit()
    kpis = (await _aggregate(client, await _staff(client, Role.admin_kota)))["kpis"]
    assert (kpis["handled_15m_pct"], kpis["referrals"]) == (50, 1)


async def test_rejects_bad_range(client: AsyncClient) -> None:
    h = await _staff(client, Role.admin_kota)
    r = await client.get("/dashboard/aggregate?from=2026-10-05&to=2026-10-01", headers=h)
    assert r.status_code == 422


async def test_kelurahan_filter_keeps_k_anonymity(client: AsyncClient) -> None:
    await _teens(KROBOKAN, [H] * 8 + [M] * 2, journal=[Emotion.senang] * 10)
    await _teens(MANYARAN, [M] * 9, journal=[Emotion.sedih] * 9)
    h = await _staff(client, Role.admin_kota)
    krobokan = (await client.get(f"/dashboard/aggregate?kelurahan={KROBOKAN}", headers=h)).json()
    assert [k["id"] for k in krobokan["kelurahan"]] == [KROBOKAN]
    assert krobokan["kpis"]["active_users"] == 10
    assert krobokan["trend"][-1]["pct"]["senang"] == 100  # jurnal Manyaran tidak ikut
    manyaran = (await client.get(f"/dashboard/aggregate?kelurahan={MANYARAN}", headers=h)).json()
    assert manyaran["kpis"] is None and manyaran["kelurahan"][0]["users"] is None
    assert all(w["pct"] is None for w in manyaran["trend"])
    r = await client.get("/dashboard/aggregate?kelurahan=9999", headers=h)
    assert r.status_code == 404
