import uuid
from sqlalchemy import (
    BigInteger,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    JSON,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base
from app.domain.enums import OrderStatus, OrderEventType


def generate_public_id() -> str:
    return uuid.uuid4().hex[:12]


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    public_id: Mapped[str] = mapped_column(String(32), default=generate_public_id, unique=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    operator_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)

    direction: Mapped[str] = mapped_column(String(64), nullable=False)
    base_currency: Mapped[str] = mapped_column(String(16), nullable=False)
    quote_currency: Mapped[str] = mapped_column(String(16), nullable=False)
    amount_from: Mapped[Numeric | None] = mapped_column(Numeric(20, 8))
    amount_to: Mapped[Numeric | None] = mapped_column(Numeric(20, 8))
    rate: Mapped[Numeric | None] = mapped_column(Numeric(20, 8))
    fee_amount: Mapped[Numeric | None] = mapped_column(Numeric(20, 8))
    network: Mapped[str | None] = mapped_column(String(32))
    status: Mapped[OrderStatus] = mapped_column(Enum(OrderStatus), default=OrderStatus.pending_payment, nullable=False)
    expires_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))

    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user: Mapped["User"] = relationship("User", foreign_keys=[user_id], back_populates="orders")
    operator: Mapped["User | None"] = relationship("User", foreign_keys=[operator_id])
    payment_details: Mapped["OrderPaymentDetails | None"] = relationship(
        back_populates="order", cascade="all,delete-orphan", uselist=False
    )
    events: Mapped[list["OrderEvent"]] = relationship(back_populates="order", cascade="all,delete-orphan")
    attachments: Mapped[list["Attachment"]] = relationship(back_populates="order", cascade="all,delete-orphan")


class OrderPaymentDetails(Base):
    __tablename__ = "order_payment_details"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), unique=True, nullable=False)
    payout_card_masked: Mapped[str | None] = mapped_column(String(32))
    payout_wallet: Mapped[str | None] = mapped_column(String(128))
    payment_card: Mapped[str | None] = mapped_column(String(32))
    payment_wallet: Mapped[str | None] = mapped_column(String(128))
    tx_hash: Mapped[str | None] = mapped_column(String(128))
    comment: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    order: Mapped["Order"] = relationship(back_populates="payment_details")


class OrderEvent(Base):
    __tablename__ = "order_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), nullable=False, index=True)
    actor_type: Mapped[str] = mapped_column(String(16))
    actor_id: Mapped[int | None] = mapped_column(BigInteger)
    event_type: Mapped[OrderEventType] = mapped_column(Enum(OrderEventType), nullable=False)
    payload_json: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    order: Mapped["Order"] = relationship(back_populates="events")


class Attachment(Base):
    __tablename__ = "attachments"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), nullable=False, index=True)
    type: Mapped[str] = mapped_column(String(32))
    storage_url: Mapped[str] = mapped_column(String(256))
    mime_type: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    order: Mapped["Order"] = relationship(back_populates="attachments")
