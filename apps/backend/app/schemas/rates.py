from decimal import Decimal
from pydantic import BaseModel


class RatePairUpsert(BaseModel):
    base_currency: str
    quote_currency: str
    buy_rate: Decimal
    sell_rate: Decimal
    source: str | None = None
