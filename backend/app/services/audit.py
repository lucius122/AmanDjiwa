import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AuditLog


async def record_access(
    session: AsyncSession,
    actor_id: uuid.UUID,
    action: str,
    case_id: uuid.UUID | None = None,
    target_id: uuid.UUID | None = None,
) -> None:
    """Catat akses staf ke data sensitif / perubahan akun staf (CLAUDE.md §7).

    Ikut commit transaksi pemanggil.
    """
    session.add(AuditLog(actor_id=actor_id, action=action, case_id=case_id, target_id=target_id))
