import logging
import time
from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, cases, chat, consent, dashboard, journal, me, telegram
from app.settings import settings

# Log hanya: method, pola route (bukan path asli: bisa berisi token), status, latensi, user_id.
# Tidak pernah isi pesan atau PII (§7). Access log uvicorn mencatat path asli, jadi dimatikan.
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logging.getLogger("uvicorn.access").disabled = True
logging.getLogger("httpx").setLevel(logging.WARNING)  # INFO-nya mencatat URL keluar (berisi id)
log = logging.getLogger("amandjiwa.http")

app = FastAPI(title="AmanDjiwa API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_methods=["*"],
    allow_headers=["Authorization", "Content-Type"],
)
app.include_router(auth.router)
app.include_router(consent.router)
app.include_router(me.router)
app.include_router(chat.router)
app.include_router(telegram.router)
app.include_router(journal.router)
app.include_router(cases.router)
app.include_router(dashboard.router)


@app.middleware("http")
async def access_log(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    start = time.perf_counter()
    status = 500
    try:
        response = await call_next(request)
        status = response.status_code
        return response
    finally:
        route = getattr(request.scope.get("route"), "path", "-")
        user_id = getattr(request.state, "user_id", "-")
        ms = (time.perf_counter() - start) * 1000
        log.info("%s %s %s %.0fms user_id=%s", request.method, route, status, ms, user_id)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
