from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, service_auth
from app.core.config import settings
from app.schemas.users import TelegramInitRequest, TelegramInitResponse
from app.services.telegram_auth import TelegramInitDataError, validate_init_data
from app.services.users import get_or_create_user

router = APIRouter(prefix="/auth/telegram")


@router.post("/init", response_model=TelegramInitResponse)
def telegram_init(
    payload: TelegramInitRequest,
    db: Session = Depends(get_db),
    x_service_token: str | None = Header(default=None),
):
    if payload.init_data:
        if not settings.telegram_bot_token:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="TG_TOKEN is required for Telegram Mini App auth",
            )
        try:
            init_data = validate_init_data(
                payload.init_data,
                bot_token=settings.telegram_bot_token,
                max_age_seconds=settings.telegram_init_max_age_seconds,
            )
        except TelegramInitDataError as exc:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

        user = get_or_create_user(
            db,
            tg_id=init_data.tg_id,
            username=init_data.username,
            lang=init_data.lang,
        )
        return {"user": user, "auth_date": init_data.auth_date, "start_param": init_data.start_param}

    service_auth(x_service_token)
    if payload.tg_id is None:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="tg_id is required without init_data")

    user = get_or_create_user(db, tg_id=payload.tg_id, username=payload.username, lang=payload.lang)
    return {"user": user, "auth_date": None, "start_param": None}
