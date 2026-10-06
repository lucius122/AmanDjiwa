"""Dasbor pendamping/konselor: RBAC per role, audit akses, alur status, sapaan, catatan, jadwal."""

import uuid
from datetime import UTC, datetime, time, timedelta
from typing import Any

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.models import (
    AuditLog,
    Case,
    CaseNote,
    Conversation,
    Emotion,
    FollowUp,
    JournalEntry,
    Message,
    Role,
    Sender,
)
from app.services.chat import WIB
from app.services.crypto import encrypt
from tests.conftest import KROBOKAN, MANYARAN, TestSession, bearer, make_staff, staff_login
from tests.test_chat import _say, _teen

pytestmark = pytest.mark.anyio
CRISIS = "aku pengen mati aja"


async def _staff(client: AsyncClient, role: Role, kel: int | None, email: str) -> dict[str, str]:
    secret = await make_staff(role, kel, email=email)
    return bearer((await staff_login(client, secret, email=email))["access_token"])


async def _setup(client: AsyncClient) -> dict[str, Any]:
    """Remaja Krobokan (merah, setelah 1 pesan hijau) + remaja Manyaran (kuning) + 3 staf."""
    krobokan = await _teen(client, "teen-k")
    await _say(client, krobokan, "hari ini biasa aja sih")
    await _say(client, krobokan, CRISIS)
    manyaran = await _teen(client, "teen-m", pseudonym="Awan Teduh", kelurahan_id=MANYARAN)
    await _say(client, manyaran, "aku cemas banget, takut, panik terus")
    return {
        "teen": krobokan,
        "pendamping": await _staff(client, Role.pendamping, KROBOKAN, "p@example.com"),
        "konselor": await _staff(client, Role.konselor, None, "k@example.com"),
        "kota": await _staff(client, Role.admin_kota, None, "kota@example.com"),
    }


async def _queue(
    client: AsyncClient, h: dict[str, str], status: list[str] | None = None
) -> list[dict[str, Any]]:
    r = await client.get("/cases", headers=h, params={"status": status} if status else None)
    assert r.status_code == 200, r.text
    rows: list[dict[str, Any]] = r.json()
    return rows


async def _audit() -> list[str]:
    """Akses ke data kasus (login staf juga diaudit, tapi tidak relevan di sini)."""
    async with TestSession() as s:
        rows = await s.execute(select(AuditLog.action).where(AuditLog.case_id.is_not(None)))
        return list(rows.scalars())


async def test_queue_is_scoped_per_role(client: AsyncClient) -> None:
    x = await _setup(client)
    (row,) = await _queue(client, x["pendamping"])
    assert (row["pseudonym"], row["kelurahan"], row["level"], row["status"]) == (
        "Bintang Senja",
        "Krobokan",
        "merah",
        "baru",
    )
    assert set(row) == {"id", "pseudonym", "kelurahan", "level", "status", "detected_at"}
    assert [r["level"] for r in await _queue(client, x["konselor"])] == ["merah"]  # kuning tidak
    assert await _queue(client, x["pendamping"], status=["selesai", "dirujuk"]) == []
    assert (await client.get("/cases", headers=x["kota"])).status_code == 403
    assert (await client.get("/cases", headers=x["teen"])).status_code == 401


async def test_detail_shows_summary_and_is_audited(client: AsyncClient) -> None:
    x = await _setup(client)
    (row,) = await _queue(client, x["pendamping"])
    r = await client.get(f"/cases/{row['id']}", headers=x["pendamping"])
    assert r.status_code == 200, r.text
    c = r.json()
    assert c["age"] == 19 and "Ungkapan ingin mati / menghilang" in c["markers"]
    assert len(c["trajectory"]) == 14 and c["trajectory"][-1] is not None
    assert c["phq9"] == {"total": None, "severity": None}  # "Belum lengkap"
    assert c["notes"] == [] and "text" not in c
    assert await _audit() == ["view_case"]


async def test_other_kelurahan_case_is_404(client: AsyncClient) -> None:
    x = await _setup(client)
    other = await _staff(client, Role.pendamping, MANYARAN, "m@example.com")
    (row,) = await _queue(client, x["pendamping"])
    for path in ("", "/messages"):
        assert (await client.get(f"/cases/{row['id']}{path}", headers=other)).status_code == 404
    r = await client.patch(f"/cases/{row['id']}", json={"action": "contacted"}, headers=other)
    assert r.status_code == 404
    assert await _audit() == []


async def test_only_trigger_messages_are_shown(client: AsyncClient) -> None:
    x = await _setup(client)
    (row,) = await _queue(client, x["pendamping"])
    r = await client.get(f"/cases/{row['id']}/messages", headers=x["pendamping"])
    body = r.json()
    assert [m["text"] for m in body["messages"]] == [CRISIS]  # pesan hijau tetap privat
    assert body["accessed_by"] == "Kak Dimas P."
    assert await _audit() == ["view_case_messages"]


async def test_contact_greets_teen_then_done(client: AsyncClient) -> None:
    x = await _setup(client)
    (row,) = await _queue(client, x["pendamping"])
    url, h = f"/cases/{row['id']}", x["pendamping"]
    assert (await client.patch(url, json={"action": "done"}, headers=h)).status_code == 409

    r = await client.patch(url, json={"action": "contacted", "note": "lewat chat"}, headers=h)
    assert r.status_code == 200, r.text
    c = r.json()
    assert c["status"] == "ditangani"
    assert [n["text"] for n in c["notes"]] == ["Sudah dihubungi. lewat chat"]

    chat = (await client.get("/chat/history", headers=x["teen"])).json()
    last = chat["messages"][-1]
    assert (last["sender"], last["author"]) == ("pendamping", "Kak Dimas P.")
    assert last["text"].startswith("Hai Bintang Senja, aku Kak Dimas P., pendamping di Krobokan.")
    assert chat["connected"] is True

    assert (await client.patch(url, json={"action": "contacted"}, headers=h)).status_code == 409
    c = (await client.patch(url, json={"action": "done"}, headers=h)).json()
    assert c["status"] == "selesai" and c["notes"][-1]["text"] == "Ditandai selesai"
    assert (await client.patch(url, json={"action": "done"}, headers=h)).status_code == 409
    assert await _queue(client, h, status=["baru", "ditangani"]) == []


async def test_greeting_sent_once_even_after_escalation(client: AsyncClient) -> None:
    teen = await _teen(client, "teen-e")
    await _say(client, teen, "aku cemas banget, takut, panik terus")  # kuning
    h = await _staff(client, Role.pendamping, KROBOKAN, "p@example.com")
    (row,) = await _queue(client, h)
    await client.patch(f"/cases/{row['id']}", json={"action": "contacted"}, headers=h)
    await _say(client, teen, CRISIS)  # naik ke merah → status kembali "baru"
    (row,) = await _queue(client, h)
    assert (row["level"], row["status"]) == ("merah", "baru")
    await client.patch(f"/cases/{row['id']}", json={"action": "contacted"}, headers=h)
    chat = (await client.get("/chat/history", headers=teen)).json()["messages"]
    assert [m["sender"] for m in chat].count("pendamping") == 1


async def test_refer_and_notes(client: AsyncClient) -> None:
    x = await _setup(client)
    (row,) = await _queue(client, x["konselor"])
    url, h = f"/cases/{row['id']}", x["konselor"]
    assert (await client.patch(url, json={"action": "refer"}, headers=h)).status_code == 422
    r = await client.post(f"{url}/notes", json={"text": "sudah telepon ortu"}, headers=h)
    assert r.status_code == 201 and r.json()[0]["text"] == "sudah telepon ortu"
    c = (
        await client.patch(
            url, json={"action": "refer", "referred_to": "Psikolog mitra USM"}, headers=h
        )
    ).json()
    assert (c["status"], c["referred_to"]) == ("dirujuk", "Psikolog mitra USM")
    assert c["notes"][-1]["text"] == "Dirujuk ke Psikolog mitra USM"
    async with TestSession() as s:
        raw = [n.text_enc for n in (await s.execute(select(CaseNote))).scalars()]
    assert raw and all(b"telepon" not in blob for blob in raw)
    assert [r["id"] for r in await _queue(client, h, status=["dirujuk"])] == [row["id"]]


async def test_follow_ups_are_personal(client: AsyncClient) -> None:
    x = await _setup(client)
    (row,) = await _queue(client, x["pendamping"])
    start = datetime.now(UTC) + timedelta(days=1)
    item = {"title": "Ketemu Bintang · balai RW 03", "scheduled_at": start.isoformat()}
    h = x["pendamping"]
    r = await client.post("/follow-ups", json=item | {"case_id": row["id"]}, headers=h)
    assert r.status_code == 201, r.text
    supervisi = {"title": "Supervisi", "scheduled_at": start.isoformat()}
    end_before = (start - timedelta(hours=1)).isoformat()
    bad = await client.post("/follow-ups", json=supervisi | {"ends_at": end_before}, headers=h)
    assert bad.status_code == 422
    other = await _staff(client, Role.pendamping, MANYARAN, "m@example.com")
    r = await client.post("/follow-ups", json=item | {"case_id": row["id"]}, headers=other)
    assert r.status_code == 404
    assert [f["title"] for f in (await client.get("/follow-ups", headers=h)).json()] == [
        item["title"]
    ]
    assert (await client.get("/follow-ups", headers=other)).json() == []
    async with TestSession() as s:
        (raw,) = [f.title_enc for f in (await s.execute(select(FollowUp))).scalars()]
    assert b"Bintang" not in raw
    item_id = (await client.get("/follow-ups", headers=h)).json()[0]["id"]
    assert (await client.delete(f"/follow-ups/{item_id}", headers=other)).status_code == 404
    assert (await client.delete(f"/follow-ups/{item_id}", headers=h)).status_code == 204
    assert (await client.get("/follow-ups", headers=h)).json() == []


async def test_staff_settings(client: AsyncClient) -> None:
    h = await _staff(client, Role.pendamping, KROBOKAN, "p@example.com")
    assert (await client.get("/auth/staff/settings", headers=h)).json() == {
        "notif_red": True,
        "sound": False,
        "compact": True,
    }
    new = {"notif_red": False, "sound": True, "compact": False}
    assert (await client.put("/auth/staff/settings", json=new, headers=h)).json() == new
    assert (await client.get("/auth/staff/settings", headers=h)).json() == new


async def test_behavior_markers_late_night_and_journal_stopped(client: AsyncClient) -> None:
    x = await _setup(client)
    (row,) = await _queue(client, x["pendamping"])
    today = datetime.now(WIB).date()
    async with TestSession() as s:
        case = await s.get(Case, uuid.UUID(row["id"]))
        assert case is not None
        conv = (
            await s.execute(select(Conversation).where(Conversation.user_id == case.user_id))
        ).scalar_one()
        for days_ago in (2, 4):  # dua malam berbeda, pukul 01.30 WIB
            at = datetime.combine(today - timedelta(days=days_ago), time(1, 30), WIB)
            s.add(
                Message(
                    conversation_id=conv.id,
                    sender=Sender.remaja,
                    encrypted_text=encrypt("x"),
                    created_at=at,
                )
            )
        for days_ago in (5, 6, 7):  # rutin, lalu berhenti 5 hari
            s.add(
                JournalEntry(
                    user_id=case.user_id,
                    entry_date=today - timedelta(days=days_ago),
                    emotion=Emotion.sedih,
                    intensity=3,
                )
            )
        await s.commit()
    c = (await client.get(f"/cases/{row['id']}", headers=x["pendamping"])).json()
    assert "Aktif larut malam" in c["markers"] and "Jurnal berhenti 5 hari" in c["markers"]
