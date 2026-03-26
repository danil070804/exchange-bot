from sqlalchemy.orm import Session
from core.models import Order

class OrdersRepo:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        user_id: int,
        direction: str,
        base: str,
        quote: str,
        amount: float,
    ) -> int:
        o = Order(
            user_id=user_id,
            direction=direction,
            base_currency=base,
            quote_currency=quote,
            amount_base=amount,
            status="new",
        )
        self.db.add(o)
        self.db.commit()
        self.db.refresh(o)
        return o.id
