from aiogram import Router, F
from aiogram.types import Message

from bot.keyboards.common import main_menu_kb, main_menu_kb_admin
from bot.i18n.catalogs import t
from core.db import get_session
from core.models import User
from core.config import settings

router = Router()


def get_user_lang(tg_id: int) -> str:
    with get_session() as db:
        u = db.query(User).filter(User.tg_id == tg_id).one_or_none()
        return (u.lang if u and u.lang else "uk")


def is_admin_user(user_id: int) -> bool:
    """Проверяем, является ли пользователь админом по ADMIN_IDS из .env."""
    if not settings.ADMIN_IDS:
        return False
    try:
        admin_ids = {int(x) for x in settings.ADMIN_IDS.split(",") if x.strip()}
    except Exception:
        return False
    return user_id in admin_ids


@router.message(F.text == "/start")
async def cmd_start(msg: Message):
    lang = get_user_lang(msg.from_user.id)
    # по умолчанию — обычное меню
    kb = main_menu_kb(lang)
    # если пользователь — админ, показываем меню с кнопкой "Адмінка"/"Admin"
    if is_admin_user(msg.from_user.id):
        kb = main_menu_kb_admin(lang)
    await msg.answer(t(lang, "cmd_start.welcome"), reply_markup=kb)
