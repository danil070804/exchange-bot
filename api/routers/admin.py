from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from api.backend_client import backend_admin_client

router = APIRouter()
templates = Jinja2Templates(directory="api/templates")


@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    orders: list[dict] = []
    users: list[dict] = []
    backend_health: dict = {"status": "unreachable"}
    backend_error: str | None = None

    try:
        backend_health = await backend_admin_client.health()
        orders_payload = await backend_admin_client.list_orders(limit=10)
        users = await backend_admin_client.list_users(limit=10)
        orders = orders_payload.get("items", [])
    except Exception as exc:
        backend_error = str(exc)

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "backend_url": backend_admin_client.base_url,
            "backend_health": backend_health,
            "backend_error": backend_error,
            "orders": orders,
            "users": users,
        },
    )
