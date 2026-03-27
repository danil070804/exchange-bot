from fastapi import APIRouter, Query

from api.backend_client import backend_admin_client

router = APIRouter()

@router.get("/", response_model=list[dict])
async def list_orders(limit: int = Query(default=100, le=200)):
    payload = await backend_admin_client.list_orders(limit=limit)
    return payload.get("items", [])
