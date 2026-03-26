from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db, service_auth
from app.schemas.users import UserCreate, UserOut
from app.services.users import get_or_create_user

router = APIRouter(prefix="/auth/telegram")


@router.post("/init", response_model=UserOut, dependencies=[Depends(service_auth)])
def telegram_init(payload: UserCreate, db: Session = Depends(get_db)):
    # TODO: validate Telegram initData signature for Mini App
    user = get_or_create_user(db, tg_id=payload.tg_id, username=payload.username, lang=payload.lang)
    return user
