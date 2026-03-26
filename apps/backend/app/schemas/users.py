from pydantic import BaseModel
from app.domain.enums import UserRole


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
