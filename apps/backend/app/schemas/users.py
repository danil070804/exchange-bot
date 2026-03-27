from pydantic import BaseModel
from app.domain.enums import UserRole


class TelegramInitRequest(BaseModel):
    init_data: str | None = None
    tg_id: int | None = None
    username: str | None = None
    lang: str | None = None


class UserCreate(BaseModel):
    tg_id: int
    username: str | None = None
    lang: str | None = None


class UserOut(BaseModel):
    id: int
    tg_id: int
    username: str | None
    lang: str | None
    role: UserRole
    is_blocked: bool

    class Config:
        from_attributes = True


class TelegramInitResponse(BaseModel):
    user: UserOut
    auth_date: int | None = None
    start_param: str | None = None
