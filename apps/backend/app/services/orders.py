from decimal import Decimal
from typing import Iterable

from sqlalchemy.orm import Session
from sqlalchemy import select, func

from app.domain.enums import OrderStatus, OrderEventType
from app.models import (
    Order,
    OrderPaymentDetails,
    OrderEvent,
    Attachment,
    User,
)


ALLOWED_STATUS_TRANSITIONS: dict[OrderStatus, set[OrderStatus]] = {
    OrderStatus.draft: {OrderStatus.pending_payment, OrderStatus.cancelled, OrderStatus.expired},
    OrderStatus.pending_payment: {
        OrderStatus.payment_submitted,
        OrderStatus.payment_review,
        OrderStatus.processing,
        OrderStatus.cancelled,
        OrderStatus.expired,
    },
    OrderStatus.payment_submitted: {
        OrderStatus.payment_review,
        OrderStatus.processing,
        OrderStatus.rejected,
        OrderStatus.cancelled,
    },
    OrderStatus.payment_review: {
        OrderStatus.processing,
        OrderStatus.rejected,
        OrderStatus.cancelled,
        OrderStatus.completed,
    },
    OrderStatus.processing: {OrderStatus.completed, OrderStatus.rejected, OrderStatus.cancelled},
    OrderStatus.completed: set(),
    OrderStatus.cancelled: set(),
    OrderStatus.expired: set(),
    OrderStatus.rejected: set(),
}


def _log_event(
    session: Session,
    order: Order,
    event_type: OrderEventType,
    actor_type: str,
    actor_id: int | None,
    payload: dict | None = None,
) -> None:
    event = OrderEvent(
        order_id=order.id,
        event_type=event_type,
        actor_type=actor_type,
        actor_id=actor_id,
        payload_json=payload,
    )
    session.add(event)


def create_order(
    session: Session,
    *,
    user: User,
    direction: str,
    base_currency: str,
    quote_currency: str,
    amount_from: Decimal,
    rate: Decimal | None,
    fee_amount: Decimal | None,
    network: str | None,
    payment_details: dict | None,
) -> Order:
    amount_to = None
    if amount_from is not None and rate is not None:
        to_crypto = direction.endswith("_TO_CRYPTO_USDT")
        amount_to = Decimal(amount_from) / Decimal(rate) if to_crypto else Decimal(amount_from) * Decimal(rate)

    order = Order(
        user_id=user.id,
        direction=direction,
        base_currency=base_currency,
        quote_currency=quote_currency,
        amount_from=amount_from,
        amount_to=amount_to,
        rate=rate,
        fee_amount=fee_amount,
        network=network,
        status=OrderStatus.pending_payment,
    )
    session.add(order)
    session.flush()  # ensure order.id

    if payment_details:
        details = OrderPaymentDetails(
            order_id=order.id,
            payout_wallet=payment_details.get("payout_wallet"),
            payout_card_masked=payment_details.get("payout_card_masked"),
            payment_card=payment_details.get("payment_card"),
            payment_wallet=payment_details.get("payment_wallet"),
            tx_hash=payment_details.get("tx_hash"),
            comment=payment_details.get("comment"),
        )
        session.add(details)

    _log_event(
        session,
        order,
        event_type=OrderEventType.created,
        actor_type="client",
        actor_id=user.tg_id,
        payload={"direction": direction, "amount_from": str(amount_from)},
    )

    return order


def list_orders(
    session: Session,
    *,
    user: User | None = None,
    statuses: Iterable[OrderStatus] | None = None,
    limit: int = 50,
) -> tuple[list[Order], int]:
    query = select(Order)
    if user:
        query = query.where(Order.user_id == user.id)
    if statuses:
        query = query.where(Order.status.in_(list(statuses)))
    query = query.order_by(Order.id.desc()).limit(limit)
    orders = session.scalars(query).all()

    count_query = select(func.count()).select_from(Order)
    if user:
        count_query = count_query.where(Order.user_id == user.id)
    total = session.scalar(count_query) or 0
    return orders, total


def get_order(session: Session, *, order_id: int, user: User | None = None) -> Order | None:
    query = select(Order).where(Order.id == order_id)
    if user:
        query = query.where(Order.user_id == user.id)
    return session.scalar(query)


def mark_paid(session: Session, *, order: Order, actor_id: int | None, comment: str | None):
    if order.status not in {OrderStatus.pending_payment, OrderStatus.draft}:
        return False
    order.status = OrderStatus.payment_submitted
    _log_event(
        session,
        order,
        event_type=OrderEventType.payment_marked,
        actor_type="client",
        actor_id=actor_id,
        payload={"comment": comment} if comment else None,
    )
    return True


def add_attachment(session: Session, *, order: Order, type_: str, storage_url: str, mime_type: str | None):
    attachment = Attachment(order_id=order.id, type=type_, storage_url=storage_url, mime_type=mime_type)
    session.add(attachment)
    _log_event(
        session,
        order,
        event_type=OrderEventType.attachment_added,
        actor_type="client",
        actor_id=order.user.tg_id if order.user else None,
        payload={"type": type_, "storage_url": storage_url},
    )
    return attachment


def update_status(
    session: Session,
    *,
    order: Order,
    new_status: OrderStatus,
    actor_type: str,
    actor_id: int | None,
    comment: str | None = None,
) -> bool:
    allowed = ALLOWED_STATUS_TRANSITIONS.get(order.status, set())
    if new_status not in allowed and new_status != order.status:
        return False

    order.status = new_status
    _log_event(
        session,
        order,
        event_type=OrderEventType.status_changed,
        actor_type=actor_type,
        actor_id=actor_id,
        payload={"status": new_status, "comment": comment},
    )
    return True


def update_quote(
    session: Session,
    *,
    order: Order,
    rate: Decimal,
    amount_to: Decimal | None = None,
    fee_amount: Decimal | None = None,
    actor_id: int | None,
):
    order.rate = rate
    if amount_to is not None:
        order.amount_to = amount_to
    if fee_amount is not None:
        order.fee_amount = fee_amount
    _log_event(
        session,
        order,
        event_type=OrderEventType.quote_updated,
        actor_type="operator",
        actor_id=actor_id,
        payload={"rate": str(rate), "amount_to": str(amount_to) if amount_to else None, "fee_amount": str(fee_amount) if fee_amount else None},
    )
