from datetime import datetime
from decimal import Decimal
from typing import List

from pydantic import BaseModel, Field

from app.domain.enums import OrderStatus, OrderEventType


class PaymentDetailsIn(BaseModel):
    payout_wallet: str | None = None
    payout_card_masked: str | None = None
    payment_card: str | None = None
    payment_wallet: str | None = None
    iban: str | None = Field(default=None, alias="payout_iban")
    tx_hash: str | None = None
    comment: str | None = None


class OrderCreate(BaseModel):
    telegram_id: int
    username: str | None = None
    lang: str | None = None
    direction: str
    base_currency: str
    quote_currency: str
    amount_from: Decimal
    rate: Decimal | None = None
    fee_amount: Decimal | None = None
    network: str | None = None
    payment_details: PaymentDetailsIn | None = None


class OrderOut(BaseModel):
    user_id: int | None = None
    user_tg_id: int | None = None
    id: int
    public_id: str
    status: OrderStatus
    direction: str
    base_currency: str
    quote_currency: str
    amount_from: Decimal | None
    amount_to: Decimal | None
    rate: Decimal | None
    fee_amount: Decimal | None
    network: str | None

    class Config:
        from_attributes = True


class PaymentDetailsOut(BaseModel):
    payout_wallet: str | None = None
    payout_card_masked: str | None = None
    payment_card: str | None = None
    payment_wallet: str | None = None
    tx_hash: str | None = None
    comment: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    class Config:
        from_attributes = True


class AttachmentOut(BaseModel):
    id: int
    type: str
    storage_url: str
    mime_type: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class OrderEventOut(BaseModel):
    id: int
    actor_type: str
    actor_id: int | None = None
    event_type: OrderEventType
    payload_json: dict | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class OrderDetailsOut(OrderOut):
    created_at: datetime | None = None
    updated_at: datetime | None = None
    expires_at: datetime | None = None
    payment_details: PaymentDetailsOut | None = None
    attachments: List[AttachmentOut] = []
    events: List[OrderEventOut] = []


class OrderList(BaseModel):
    items: List[OrderOut]
    total: int


class OrderAttachmentIn(BaseModel):
    type: str = Field(default="payment_proof")
    storage_url: str
    mime_type: str | None = None


class OrderStatusUpdate(BaseModel):
    status: OrderStatus
    comment: str | None = None


class OrderMarkPaid(BaseModel):
    comment: str | None = None


class AdminOrderUpdateQuote(BaseModel):
    rate: Decimal
    amount_to: Decimal | None = None
    fee_amount: Decimal | None = None
