from core.db import get_session
from core.models import RatePair

async def get_market_rate(base: str, quote: str) -> float:
    """Берем курс из таблицы rate_pairs, если есть, иначе дефолтный."""
    with get_session() as db:
        pair = (
            db.query(RatePair)
            .filter(
                RatePair.base_currency == base,
                RatePair.quote_currency == quote,
            )
            .one_or_none()
        )
        if pair:
            return float(pair.rate)

    # дефолтный курс, если админ ещё не задавал
    if (base, quote) == ("USDT", "UAH"):
        return 41.0
    if (base, quote) == ("UAH", "USDT"):
        return 1.0 / 41.0

    return 1.0  # fallback
