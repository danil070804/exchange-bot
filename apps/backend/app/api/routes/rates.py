from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.api.deps import get_db
from app.models import RatePair

router = APIRouter(prefix="/rates")


@router.get("/quote")
def quote(
    base: str = Query(..., alias="base_currency"),
    quote: str = Query(..., alias="quote_currency"),
    direction: str = Query(...),
    amount: Decimal = Query(..., alias="amount_from"),
    db: Session = Depends(get_db),
):
    pair = db.scalar(
        select(RatePair).where(RatePair.base_currency == base.upper(), RatePair.quote_currency == quote.upper())
    )
    if not pair:
        raise HTTPException(status_code=404, detail="Rate pair not configured")

    rate = pair.buy_rate if direction.endswith("TO_CRYPTO_USDT") else pair.sell_rate
    amount_to = Decimal(amount) / rate if direction.endswith("TO_CRYPTO_USDT") else Decimal(amount) * rate
    return {
        "rate": str(rate),
        "amount_from": str(amount),
        "amount_to": str(amount_to),
        "base_currency": base.upper(),
        "quote_currency": quote.upper(),
    }
