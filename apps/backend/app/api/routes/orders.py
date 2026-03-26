from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, current_user, service_auth
from app.domain.enums import OrderStatus
from app.schemas.orders import (
    OrderCreate,
    OrderOut,
    OrderList,
    OrderAttachmentIn,
    OrderMarkPaid,
)
from app.services import orders as order_service
from app.services.users import get_or_create_user
from app.models import Order

router = APIRouter(prefix="/orders")


@router.post("", response_model=OrderOut, dependencies=[Depends(service_auth)])
def create_order(payload: OrderCreate, db: Session = Depends(get_db)):
    user = get_or_create_user(db, tg_id=payload.telegram_id, username=payload.username, lang=payload.lang)
    order = order_service.create_order(
        db,
        user=user,
        direction=payload.direction,
        base_currency=payload.base_currency.upper(),
        quote_currency=payload.quote_currency.upper(),
        amount_from=payload.amount_from,
        rate=payload.rate,
        fee_amount=payload.fee_amount,
        network=payload.network,
        payment_details=payload.payment_details.dict(by_alias=True) if payload.payment_details else None,
    )
    order.user_tg_id = user.tg_id
    return order


@router.get("", response_model=OrderList)
def list_my_orders(
    status_filter: list[OrderStatus] | None = Query(default=None, alias="status"),
    limit: int = Query(default=20, le=100),
    user=Depends(current_user),
    db: Session = Depends(get_db),
):
    items, total = order_service.list_orders(db, user=user, statuses=status_filter, limit=limit)
    for item in items:
        item.user_tg_id = user.tg_id
    return {"items": items, "total": total}


@router.get("/{order_id}", response_model=OrderOut)
def order_details(order_id: int, user=Depends(current_user), db: Session = Depends(get_db)):
    order = order_service.get_order(db, order_id=order_id, user=user)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    order.user_tg_id = user.tg_id
    return order


@router.post("/{order_id}/mark-paid", response_model=OrderOut)
def mark_paid(order_id: int, payload: OrderMarkPaid, user=Depends(current_user), db: Session = Depends(get_db)):
    order = order_service.get_order(db, order_id=order_id, user=user)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    ok = order_service.mark_paid(db, order=order, actor_id=user.tg_id, comment=payload.comment)
    if not ok:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Status transition not allowed")
    db.refresh(order)
    return order


@router.post("/{order_id}/attachments", response_model=OrderOut)
def add_attachment(
    order_id: int,
    payload: OrderAttachmentIn,
    user=Depends(current_user),
    db: Session = Depends(get_db),
):
    order = order_service.get_order(db, order_id=order_id, user=user)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    order_service.add_attachment(
        db,
        order=order,
        type_=payload.type,
        storage_url=payload.storage_url,
        mime_type=payload.mime_type,
    )
    db.refresh(order)
    order.user_tg_id = user.tg_id
    return order
