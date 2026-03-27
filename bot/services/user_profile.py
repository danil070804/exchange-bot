from core.db import get_session
from core.models import User


def get_user_lang(tg_id: int) -> str:
    try:
        with get_session() as db:
            user = db.query(User).filter(User.tg_id == tg_id).one_or_none()
            return user.lang if user and user.lang else "uk"
    except RuntimeError:
        return "uk"