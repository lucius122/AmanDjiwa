"""Perintah admin:

    uv run python -m app.cli create-staff --email ... --role pendamping --kelurahan Krobokan
    uv run python -m app.cli seed-demo     # butuh DEMO_MODE=true; data SINTETIS + 3 akun staf demo
    uv run python -m app.cli reset-demo    # hapus hanya data demo

create-staff meminta password lewat prompt dan mencetak URI otpauth untuk aplikasi authenticator.
"""

import argparse
import asyncio
import getpass

import pyotp
from sqlalchemy import select

from app import demo
from app.db import SessionLocal
from app.models import Kelurahan, Role, User
from app.services.auth import hash_password
from app.services.crypto import encrypt


async def create_staff(email: str, name: str, role: Role, kelurahan: str | None) -> None:
    password = getpass.getpass("Password (min. 12 karakter): ")
    if len(password) < 12:
        raise SystemExit("Password terlalu pendek.")
    secret = pyotp.random_base32()
    async with SessionLocal() as session:
        kel_id = None
        if kelurahan:
            kel_id = (
                await session.execute(select(Kelurahan.id).where(Kelurahan.name == kelurahan))
            ).scalar_one()
        session.add(
            User(
                role=role,
                email=email.lower(),
                display_name=name,
                password_hash=hash_password(password),
                totp_secret_enc=encrypt(secret),
                kelurahan_id=kel_id,
            )
        )
        await session.commit()
    print(pyotp.TOTP(secret).provisioning_uri(name=email, issuer_name="AmanDjiwa"))


async def seed_demo() -> None:
    async with SessionLocal() as session:
        logins = await demo.seed(session)
    print("Data demo SINTETIS dibuat. Akun staf (pindai URI otpauth di aplikasi authenticator):")
    for x in logins:
        print(f"\n  {x.role.value}\n    email    : {x.email}")
        print(f"    password : {x.password}\n    otpauth  : {x.otpauth}")


async def reset_demo() -> None:
    async with SessionLocal() as session:
        print(f"Data demo dihapus ({await demo.reset(session)} remaja sintetis).")


def main() -> None:
    parser = argparse.ArgumentParser(prog="app.cli")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("create-staff")
    p.add_argument("--email", required=True)
    p.add_argument("--name", required=True, help='Nama tampil, mis. "Kak Dimas P."')
    p.add_argument("--role", required=True, choices=[r.value for r in Role if r != Role.remaja])
    p.add_argument("--kelurahan", help="Wajib untuk pendamping")
    sub.add_parser("seed-demo")
    sub.add_parser("reset-demo")
    a = parser.parse_args()
    if a.cmd == "seed-demo":
        asyncio.run(seed_demo())
    elif a.cmd == "reset-demo":
        asyncio.run(reset_demo())
    else:
        asyncio.run(create_staff(a.email, a.name, Role(a.role), a.kelurahan))


if __name__ == "__main__":
    main()
