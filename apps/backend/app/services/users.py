from sqlalchemy.orm import Session

from app.domain.enums import UserRole
from app.models import User


def get_or_create_user(session: Session, *, tg_id: int, username: str | None, lang: str | None) -> User:
    user = session.query(User).filter(User.tg_id == tg_id).one_or_none()
    if user:
        updated = False
        if username and user.username != username:
            user.username = username
            updated = True
        if lang and user.lang != lang:
            user.lang = lang
            updated = True
        if updated:
            session.add(user)
        return user

    user = User(tg_id=tg_id, username=username, lang=lang, role=UserRole.client)
    session.add(user)
    session.flush()
    return user
