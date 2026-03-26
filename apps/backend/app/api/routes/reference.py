from fastapi import APIRouter

from app.domain.enums import OrderStatus

router = APIRouter(prefix="/reference")


@router.get("/config")
def reference_config():
    return {
        "order_statuses": [s.value for s in OrderStatus],
        "directions": [
            "CARD_UAH_TO_CRYPTO_USDT",
            "CRYPTO_USDT_TO_CARD_UAH",
            "CASH_UAH_TO_CRYPTO_USDT",
            "CRYPTO_USDT_TO_CASH_UAH",
            "IBAN_UAH_TO_CRYPTO_USDT",
            "CRYPTO_USDT_TO_IBAN_UAH",
        ],
        "version": "v1",
    }
