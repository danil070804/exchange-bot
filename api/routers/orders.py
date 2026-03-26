from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from core.db import get_session
from core.models import Order
from typing import List

router = APIRouter()

def session_dep():
    with get_session() as s:
        yield s

@router.get("/", response_model=list[dict])
def list_orders(session: Session = Depends(session_dep)):
    rows = session.query(Order).order_by(Order.id.desc()).limit(100).all()
    return [{
        "id": o.id, "user_id": o.user_id, "direction": o.direction,
        "status": o.status, "amount_base": str(o.amount_base), "rate": str(o.rate)
    } for o in rows]
