from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.api.deps import admin_auth, get_db
from app.domain.enums import OrderStatus
from app.schemas.orders import OrderStatusUpdate, AdminOrderUpdateQuote, OrderDetailsOut, OrderList, OrderOut
from app.schemas.users import UserOut
from app.schemas.rates import RatePairUpsert
from app.models import RatePair, User
from app.services import orders as order_service
from app.models import Order

router = APIRouter(prefix="/admin", dependencies=[Depends(admin_auth)])


@router.get("/orders", response_model=OrderList)
def list_orders(
    status_filter: list[OrderStatus] | None = Query(default=None, alias="status"),
    limit: int = Query(default=50, le=200),
    db: Session = Depends(get_db),
):
    items, total = order_service.list_orders(db, statuses=status_filter, limit=limit)
    for item in items:
        item.user_tg_id = item.user.tg_id if item.user else None
    return {"items": items, "total": total}


@router.get("/orders/{order_id}", response_model=OrderDetailsOut)
def order_details(order_id: int, db: Session = Depends(get_db)):
    order = order_service.get_order(db, order_id=order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    order.user_tg_id = order.user.tg_id if order.user else None
    return order


@router.post("/orders/{order_id}/status", response_model=OrderDetailsOut)
def update_status(order_id: int, payload: OrderStatusUpdate, db: Session = Depends(get_db)):
    order = order_service.get_order(db, order_id=order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    ok = order_service.update_status(
        db,
        order=order,
        new_status=payload.status,
        actor_type="operator",
        actor_id=order.operator_id,
        comment=payload.comment,
    )
    if not ok:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Status transition not allowed")
    db.refresh(order)
    order.user_tg_id = order.user.tg_id if order.user else None
    return order


@router.post("/orders/{order_id}/quote", response_model=OrderDetailsOut)
def update_quote(order_id: int, payload: AdminOrderUpdateQuote, db: Session = Depends(get_db)):
    order = order_service.get_order(db, order_id=order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    order_service.update_quote(
        db,
        order=order,
        rate=payload.rate,
        amount_to=payload.amount_to,
        fee_amount=payload.fee_amount,
        actor_id=order.operator_id,
    )
    db.refresh(order)
    order.user_tg_id = order.user.tg_id if order.user else None
    return order


@router.post("/rates/pair")
def upsert_rate_pair(payload: RatePairUpsert, db: Session = Depends(get_db)):
    pair = (
        db.query(RatePair)
        .filter(
            RatePair.base_currency == payload.base_currency.upper(),
            RatePair.quote_currency == payload.quote_currency.upper(),
        )
        .one_or_none()
    )
    if not pair:
        pair = RatePair(
            base_currency=payload.base_currency.upper(),
            quote_currency=payload.quote_currency.upper(),
            buy_rate=payload.buy_rate,
            sell_rate=payload.sell_rate,
            source=payload.source,
        )
        db.add(pair)
    else:
        pair.buy_rate = payload.buy_rate
        pair.sell_rate = payload.sell_rate
        pair.source = payload.source
    db.commit()
    return {"base_currency": pair.base_currency, "quote_currency": pair.quote_currency, "buy_rate": str(pair.buy_rate), "sell_rate": str(pair.sell_rate)}


@router.get("/users", response_model=list[UserOut])
def list_users(limit: int = Query(default=100, le=500), db: Session = Depends(get_db)):
    query = select(User).order_by(User.id.desc()).limit(limit)
    return list(db.scalars(query).all())
