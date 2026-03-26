from sqlalchemy.orm import Session
from core.models import User

class UsersRepo:
    def __init__(self, db: Session):
        self.db = db

    def get_or_create(self, tg_id: int, username: str | None = None) -> User:
        u = self.db.query(User).filter(User.tg_id == tg_id).one_or_none()
        if u:
            return u
        u = User(tg_id=tg_id, username=username)
        self.db.add(u)
        self.db.commit()
        self.db.refresh(u)
        return u
