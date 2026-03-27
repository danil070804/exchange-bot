import httpx

from core.config import settings


class BackendAdminClient:
    def __init__(self):
        self.base_url = settings.BACKEND_API_URL.rstrip("/")

    def _headers(self) -> dict[str, str]:
        headers: dict[str, str] = {}
        if settings.ADMIN_API_TOKEN:
            headers["X-Admin-Token"] = settings.ADMIN_API_TOKEN
        return headers

    async def health(self) -> dict:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{self.base_url}/healthz")
            response.raise_for_status()
            return response.json()

    async def list_orders(self, limit: int = 50, status: list[str] | None = None) -> dict:
        params: dict[str, object] = {"limit": limit}
        if status:
            params["status"] = status
        async with httpx.AsyncClient(timeout=15.0, headers=self._headers()) as client:
            response = await client.get(f"{self.base_url}/api/v1/admin/orders", params=params)
            response.raise_for_status()
            return response.json()

    async def list_users(self, limit: int = 100) -> list[dict]:
        async with httpx.AsyncClient(timeout=15.0, headers=self._headers()) as client:
            response = await client.get(f"{self.base_url}/api/v1/admin/users", params={"limit": limit})
            response.raise_for_status()
            return response.json()


backend_admin_client = BackendAdminClient()