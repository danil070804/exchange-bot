from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from core.db import get_session
from core.models import User

router = APIRouter()

def session_dep():
    with get_session() as s:
        yield s

@router.get("/")
def list_users(session: Session = Depends(session_dep)):
    users = session.query(User).order_by(User.id.desc()).limit(100).all()
    return [{"id": u.id, "tg_id": u.tg_id, "kyc_level": u.kyc_level, "kyc_status": u.kyc_status} for u in users]
