from fastapi import APIRouter, Query

from api.backend_client import backend_admin_client

router = APIRouter()

@router.get("/")
async def list_users(limit: int = Query(default=100, le=500)):
    return await backend_admin_client.list_users(limit=limit)
