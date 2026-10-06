import pytest
from fastapi import HTTPException

from app.api.deps import case_scope
from app.models import Case, RiskLevel, Role, User
from tests.conftest import KROBOKAN, MANYARAN, TestSession

pytestmark = pytest.mark.anyio


def _teen(sub: str, kelurahan_id: int) -> User:
    return User(
        role=Role.remaja,
        auth_id=sub,
        pseudonym=sub,
        avatar=0,
        kelurahan_id=kelurahan_id,
        birth_year=2010,
    )


async def test_case_scope_per_role(db: None) -> None:
    async with TestSession() as s:
        a, b = _teen("a", KROBOKAN), _teen("b", MANYARAN)
        s.add_all([a, b])
        await s.flush()
        s.add_all(
            [
                Case(user_id=a.id, kelurahan_id=KROBOKAN, level=RiskLevel.merah),
                Case(user_id=a.id, kelurahan_id=KROBOKAN, level=RiskLevel.kuning),
                Case(user_id=b.id, kelurahan_id=MANYARAN, level=RiskLevel.oranye),
            ]
        )
        await s.commit()

        pendamping = User(role=Role.pendamping, kelurahan_id=KROBOKAN)
        seen = (await s.execute(case_scope(pendamping))).scalars().all()
        assert {(c.kelurahan_id, c.level) for c in seen} == {
            (KROBOKAN, RiskLevel.merah),
            (KROBOKAN, RiskLevel.kuning),
        }

        konselor = User(role=Role.konselor)
        seen = (await s.execute(case_scope(konselor))).scalars().all()
        assert {c.level for c in seen} == {RiskLevel.merah, RiskLevel.oranye}

    with pytest.raises(HTTPException) as e:
        case_scope(User(role=Role.admin_kota))
    assert e.value.status_code == 403
