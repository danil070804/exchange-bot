from sqlalchemy import DateTime, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.db.base import Base


class RatePair(Base):
    __tablename__ = "rate_pairs"

    id: Mapped[int] = mapped_column(primary_key=True)
    base_currency: Mapped[str] = mapped_column(String(16), nullable=False)
    quote_currency: Mapped[str] = mapped_column(String(16), nullable=False)
    buy_rate: Mapped[Numeric] = mapped_column(Numeric(20, 8), nullable=False)
    sell_rate: Mapped[Numeric] = mapped_column(Numeric(20, 8), nullable=False)
    source: Mapped[str | None] = mapped_column(String(64))
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
