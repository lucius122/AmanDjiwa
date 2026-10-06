"""URL Postgres dari Railway (postgres:// / postgresql://) dipakai apa adanya oleh backend."""

import base64
import os

import pytest

from app.settings import Settings


@pytest.mark.parametrize(
    "url",
    ["postgresql://u:p@h:5432/d", "postgres://u:p@h:5432/d", "postgresql+asyncpg://u:p@h:5432/d"],
)
def test_database_url_gets_asyncpg_driver(url: str) -> None:
    key = base64.b64encode(os.urandom(32)).decode()
    s = Settings(database_url=url, message_enc_key=key, jwt_secret="x" * 40, _env_file=None)  # type: ignore[call-arg]
    assert s.database_url == "postgresql+asyncpg://u:p@h:5432/d"
