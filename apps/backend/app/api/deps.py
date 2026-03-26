from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_session
from app.models import User
from app.services.users import get_or_create_user


def get_db():
    with get_session() as session:
        yield session


def service_auth(x_service_token: str | None = Header(default=None)) -> None:
    if settings.bot_internal_token and x_service_token != settings.bot_internal_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid service token")


def admin_auth(x_admin_token: str | None = Header(default=None)) -> None:
    if settings.admin_api_token and x_admin_token != settings.admin_api_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid admin token")


def current_user(
    telegram_id: int | None = Header(default=None, alias="X-Telegram-Id"),
    db: Session = Depends(get_db),
) -> User:
    if telegram_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="X-Telegram-Id header is required")
    user = get_or_create_user(db, tg_id=telegram_id, username=None, lang=None)
    return user
