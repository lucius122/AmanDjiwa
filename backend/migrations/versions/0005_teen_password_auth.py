"""teen password auth, staff account management

Revision ID: 0005
Revises: 0004
Create Date: 2026-10-06 12:30:00

Remaja login dengan email + password (bukan Supabase). Status "onboarding" = akun sudah dibuat,
profil belum. Admin kota mengelola akun staf (audit_logs.target_id).
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0005"
down_revision: str | Sequence[str] | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

STATUS_OLD = "status IN ('pending_guardian', 'active', 'disabled')"
STATUS_NEW = "status IN ('onboarding', 'pending_guardian', 'active', 'disabled')"


def upgrade() -> None:
    op.add_column("users", sa.Column("email_hash", sa.String(length=64), nullable=True))
    op.add_column("users", sa.Column("email_enc", sa.LargeBinary(), nullable=True))
    op.create_unique_constraint(op.f("uq_users_email_hash"), "users", ["email_hash"])
    op.add_column("audit_logs", sa.Column("target_id", sa.Uuid(), nullable=True))

    op.drop_constraint(op.f("ck_users_remaja_has_auth_id"), "users", type_="check")
    op.create_check_constraint(
        op.f("ck_users_remaja_has_login"),
        "users",
        "role != 'remaja' OR auth_id IS NOT NULL OR email_hash IS NOT NULL",
    )
    op.drop_constraint(op.f("ck_users_scoped_role_has_kelurahan"), "users", type_="check")
    op.create_check_constraint(
        op.f("ck_users_scoped_role_has_kelurahan"),
        "users",
        "role != 'pendamping' OR kelurahan_id IS NOT NULL",
    )
    op.create_check_constraint(
        op.f("ck_users_teen_profile_has_kelurahan"),
        "users",
        "role != 'remaja' OR pseudonym IS NULL OR kelurahan_id IS NOT NULL",
    )
    op.drop_constraint(op.f("ck_users_userstatus"), "users", type_="check")
    op.create_check_constraint(op.f("ck_users_userstatus"), "users", STATUS_NEW)


def downgrade() -> None:
    # Gagal kalau sudah ada akun remaja email+password tanpa auth_id (memang tidak bisa dikembalikan).
    op.drop_constraint(op.f("ck_users_userstatus"), "users", type_="check")
    op.create_check_constraint(op.f("ck_users_userstatus"), "users", STATUS_OLD)
    op.drop_constraint(op.f("ck_users_teen_profile_has_kelurahan"), "users", type_="check")
    op.drop_constraint(op.f("ck_users_scoped_role_has_kelurahan"), "users", type_="check")
    op.create_check_constraint(
        op.f("ck_users_scoped_role_has_kelurahan"),
        "users",
        "role NOT IN ('remaja', 'pendamping') OR kelurahan_id IS NOT NULL",
    )
    op.drop_constraint(op.f("ck_users_remaja_has_login"), "users", type_="check")
    op.create_check_constraint(
        op.f("ck_users_remaja_has_auth_id"), "users", "(role = 'remaja') = (auth_id IS NOT NULL)"
    )
    op.drop_column("audit_logs", "target_id")
    op.drop_constraint(op.f("uq_users_email_hash"), "users", type_="unique")
    op.drop_column("users", "email_enc")
    op.drop_column("users", "email_hash")
