import httpx

from core.config import settings


class BackendClient:
    def __init__(self):
        self.base_url = settings.BACKEND_API_URL.rstrip("/")
        self.token = settings.BACKEND_BOT_TOKEN

    def _headers(self) -> dict[str, str]:
        headers = {}
        if self.token:
            headers["X-Service-Token"] = self.token
        return headers

    def _admin_headers(self) -> dict[str, str]:
        headers = self._headers()
        if settings.ADMIN_API_TOKEN:
            headers["X-Admin-Token"] = settings.ADMIN_API_TOKEN
        return headers

    async def create_order(
        self,
        *,
        telegram_id: int,
        username: str | None,
        lang: str | None,
        direction: str,
        base_currency: str,
        quote_currency: str,
        amount_from: float,
        network: str | None = None,
        payment_details: dict | None = None,
    ) -> dict:
        payload = {
            "telegram_id": telegram_id,
            "username": username,
            "lang": lang,
            "direction": direction,
            "base_currency": base_currency,
            "quote_currency": quote_currency,
            "amount_from": amount_from,
            "network": network,
            "payment_details": payment_details,
        }
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(f"{self.base_url}/api/v1/orders", json=payload, headers=self._headers())
            resp.raise_for_status()
            return resp.json()

    async def admin_list_orders(self, limit: int = 20, status: list[str] | None = None) -> dict:
        params = {"limit": limit}
        if status:
            params["status"] = status
        async with httpx.AsyncClient(timeout=10.0, headers=self._admin_headers()) as client:
            resp = await client.get(f"{self.base_url}/api/v1/admin/orders", params=params)
            resp.raise_for_status()
            return resp.json()

    async def admin_get_order(self, order_id: int) -> dict | None:
        async with httpx.AsyncClient(timeout=10.0, headers=self._admin_headers()) as client:
            resp = await client.get(f"{self.base_url}/api/v1/admin/orders/{order_id}")
            resp.raise_for_status()
            return resp.json()

    async def admin_set_status(self, order_id: int, status_value: str, comment: str | None = None) -> dict:
        payload = {"status": status_value, "comment": comment}
        async with httpx.AsyncClient(timeout=10.0, headers=self._admin_headers()) as client:
            resp = await client.post(f"{self.base_url}/api/v1/admin/orders/{order_id}/status", json=payload)
            resp.raise_for_status()
            return resp.json()

    async def admin_update_quote(
        self, order_id: int, rate: float, amount_to: float | None = None, fee_amount: float | None = None
    ) -> dict:
        payload = {"rate": rate, "amount_to": amount_to, "fee_amount": fee_amount}
        async with httpx.AsyncClient(timeout=10.0, headers=self._admin_headers()) as client:
            resp = await client.post(f"{self.base_url}/api/v1/admin/orders/{order_id}/quote", json=payload)
            resp.raise_for_status()
            return resp.json()

    async def admin_set_rate_pair(
        self, base_currency: str, quote_currency: str, buy_rate: float, sell_rate: float, source: str | None = None
    ) -> dict:
        payload = {
            "base_currency": base_currency,
            "quote_currency": quote_currency,
            "buy_rate": buy_rate,
            "sell_rate": sell_rate,
            "source": source,
        }
        async with httpx.AsyncClient(timeout=10.0, headers=self._admin_headers()) as client:
            resp = await client.post(f"{self.base_url}/api/v1/admin/rates/pair", json=payload)
            resp.raise_for_status()
            return resp.json()

    async def list_orders(self, telegram_id: int, limit: int = 10) -> dict:
        async with httpx.AsyncClient(timeout=10.0, headers={"X-Telegram-Id": str(telegram_id)}) as client:
            resp = await client.get(f"{self.base_url}/api/v1/orders", params={"limit": limit})
            resp.raise_for_status()
            return resp.json()

    async def mark_paid(self, telegram_id: int, order_id: int, comment: str | None = None) -> dict:
        async with httpx.AsyncClient(timeout=10.0, headers={"X-Telegram-Id": str(telegram_id)}) as client:
            resp = await client.post(
                f"{self.base_url}/api/v1/orders/{order_id}/mark-paid",
                json={"comment": comment} if comment else {},
            )
            resp.raise_for_status()
            return resp.json()

    async def add_attachment(
        self,
        telegram_id: int,
        order_id: int,
        type_: str,
        storage_url: str,
        mime_type: str | None = None,
    ) -> dict:
        payload = {"type": type_, "storage_url": storage_url, "mime_type": mime_type}
        async with httpx.AsyncClient(timeout=15.0, headers={"X-Telegram-Id": str(telegram_id)}) as client:
            resp = await client.post(f"{self.base_url}/api/v1/orders/{order_id}/attachments", json=payload)
            resp.raise_for_status()
            return resp.json()


backend_client = BackendClient()
