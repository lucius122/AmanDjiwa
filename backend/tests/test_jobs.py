"""Tugas terjadwal: peringatan merah, pengingat jurnal, laporan mingguan."""

from datetime import datetime, timedelta

import pytest
from httpx import AsyncClient
from redis.asyncio import Redis
from sqlalchemy import select, update

from app import jobs
from app.api.dashboard import build_aggregate
from app.bot import logic
from app.models import Case, Role, User
from app.services.chat import WIB
from tests.conftest import KROBOKAN, MANYARAN, TestSession, make_staff, teen_headers
from tests.test_chat import _say, _teen
from tests.test_dashboard import H, M, _teens
from tests.test_telegram import TG_ID, _linked_teen

pytestmark = pytest.mark.anyio


class Outbox:
    def __init__(self, fail: bool = False) -> None:
        self.sent: list[tuple[str, str, str]] = []
        self.fail = fail

    async def __call__(self, to: str, subject: str, body: str) -> None:
        if self.fail:
            raise OSError("smtp down")
        self.sent.append((to, subject, body))


async def _red_case(client: AsyncClient) -> None:
    h = await _teen(client, "teen-red")  # Bintang Senja, Krobokan
    await _say(client, h, "aku pengen mati aja")


async def test_red_alert_goes_to_scoped_staff_without_identity(client: AsyncClient) -> None:
    await _red_case(client)
    await make_staff(Role.pendamping, KROBOKAN, email="p-krobokan@example.com")
    await make_staff(Role.pendamping, MANYARAN, email="p-manyaran@example.com")
    await make_staff(Role.konselor, email="k-on@example.com")
    await make_staff(Role.konselor, email="k-off@example.com")
    async with TestSession() as s:
        await s.execute(
            update(User)
            .where(User.email == "k-off@example.com")
            .values(settings={"notif_red": False})
        )
        await s.commit()

    outbox = Outbox()
    assert await jobs.red_alerts(TestSession, outbox) == 2
    assert sorted(to for to, _, _ in outbox.sent) == ["k-on@example.com", "p-krobokan@example.com"]
    _, subject, body = outbox.sent[0]
    assert "Krobokan" in subject and "/staf" in body
    assert "Bintang" not in subject + body and "pengen mati" not in body
    assert await jobs.red_alerts(TestSession, outbox) == 0  # sekali per kasus


async def test_red_alert_retried_when_mail_fails(client: AsyncClient) -> None:
    await _red_case(client)
    await make_staff(Role.pendamping, KROBOKAN, email="p@example.com")
    assert await jobs.red_alerts(TestSession, Outbox(fail=True)) == 0
    async with TestSession() as s:
        assert (await s.execute(select(Case.red_alerted_at))).scalar_one() is None
    assert await jobs.red_alerts(TestSession, Outbox()) == 1


async def test_journal_reminder_once_a_day_and_opt_out(
    client: AsyncClient, redis_client: Redis
) -> None:
    await _linked_teen(client, redis_client)
    sent: list[tuple[int, str]] = []

    async def tg(tg_id: int, text: str) -> bool:
        sent.append((tg_id, text))
        return True

    assert await jobs.journal_reminders(TestSession, redis_client, tg) == 1
    assert sent[0][0] == TG_ID and "Ombak Tenang" in sent[0][1] and "/jurnal" in sent[0][1]
    assert await jobs.journal_reminders(TestSession, redis_client, tg) == 0  # kunci harian

    await redis_client.flushdb()
    async with TestSession() as s:
        (out,) = await logic.toggle_reminder(s, TG_ID)
    assert out.text == logic.TG["reminder_off"]
    assert await jobs.journal_reminders(TestSession, redis_client, tg) == 0
    async with TestSession() as s:
        (out,) = await logic.toggle_reminder(s, TG_ID)
    assert out.text == logic.TG["reminder_on"]


async def test_no_reminder_after_journal_today(client: AsyncClient, redis_client: Redis) -> None:
    await _linked_teen(client, redis_client)
    r = await client.post(
        "/journal", json={"emotion": "senang", "intensity": 3}, headers=teen_headers("tg-teen")
    )
    assert r.status_code in (200, 201), r.text

    async def tg(tg_id: int, text: str) -> bool:
        raise AssertionError("tidak boleh dikirim")

    assert await jobs.journal_reminders(TestSession, redis_client, tg) == 0


async def test_weekly_report_is_aggregate_only(db: None, redis_client: Redis) -> None:
    await _teens(KROBOKAN, [H] * 8 + [M] * 2, topics=["akademik"] * 10)
    await make_staff(Role.admin_kota, email="kota@example.com")
    await make_staff(Role.pendamping, KROBOKAN, email="p@example.com")

    today = datetime.now(WIB).date()
    async with TestSession() as s:
        subject, body = jobs.report_text(await build_aggregate(s, today - timedelta(days=6), today))
    assert "Pengguna aktif: 10" in body and "Krobokan: 20%" in body and "Akademik" in body
    assert "Anon" not in body and "/kota" in body and "Laporan mingguan" in subject

    outbox = Outbox()
    assert await jobs.weekly_report(TestSession, redis_client, outbox) == 1
    assert [to for to, _, _ in outbox.sent] == ["kota@example.com"]
    assert await jobs.weekly_report(TestSession, redis_client, outbox) == 0  # kunci mingguan
