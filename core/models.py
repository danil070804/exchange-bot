from sqlalchemy import Column, Integer, BigInteger, String, Numeric, TIMESTAMP, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from core.db import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    tg_id = Column(BigInteger, unique=True, nullable=False)
    username = Column(String)
    lang = Column(String, default="uk")
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    orders = relationship("Order", back_populates="user")


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    direction = Column(String, nullable=False)        # CARD_UAH_TO_CRYPTO_USDT / CRYPTO_USDT_TO_CARD_UAH
    base_currency = Column(String, nullable=False)    # UAH / USDT
    quote_currency = Column(String, nullable=False)   # USDT / UAH

    amount_base = Column(Numeric(20, 8))
    status = Column(String, default="new")            # new / paid / rejected / etc.

    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="orders")


class RatePair(Base):
    __tablename__ = "rate_pairs"

    id = Column(Integer, primary_key=True)
    base_currency = Column(String, nullable=False)    # e.g. "USDT"
    quote_currency = Column(String, nullable=False)   # e.g. "UAH"
    rate = Column(Numeric(20, 8), nullable=False)     # how many QUOTE per 1 BASE
