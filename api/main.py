from fastapi import FastAPI

from api.backend_client import backend_admin_client
from api.routers import admin, orders, users
from core.config import settings

app = FastAPI(title="Exchange Admin API")

app.include_router(admin.router, prefix="/admin")
app.include_router(orders.router, prefix="/orders")
app.include_router(users.router, prefix="/users")


@app.get("/health")
async def health():
    try:
        backend_health = await backend_admin_client.health()
        return {
            "status": "ok",
            "tz": settings.TIMEZONE,
            "backend": backend_health,
            "backend_url": backend_admin_client.base_url,
        }
    except Exception as exc:
        return {
            "status": "degraded",
            "tz": settings.TIMEZONE,
            "backend": {"status": "unreachable"},
            "backend_url": backend_admin_client.base_url,
            "error": str(exc),
        }
