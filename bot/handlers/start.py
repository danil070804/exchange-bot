from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from aiogram import Router, F
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, WebAppInfo

from bot.keyboards.common import main_menu_kb, main_menu_kb_admin
from bot.i18n.catalogs import t
from bot.services.user_profile import get_user_lang
from core.config import settings

router = Router()


def is_admin_user(user_id: int) -> bool:
    """Проверяем, является ли пользователь админом по ADMIN_IDS из .env."""
    if not settings.ADMIN_IDS:
        return False
    try:
        admin_ids = {int(x) for x in settings.ADMIN_IDS.split(",") if x.strip()}
    except Exception:
        return False
    return user_id in admin_ids


def build_miniapp_url(start_param: str | None = None) -> str | None:
    if not settings.MINI_APP_URL:
        return None

    parts = urlsplit(settings.MINI_APP_URL)
    query = dict(parse_qsl(parts.query, keep_blank_values=True))
    if start_param:
        query["startapp"] = start_param
    new_query = urlencode(query)
    return urlunsplit((parts.scheme, parts.netloc, parts.path, new_query, parts.fragment))


def extract_start_param(text: str | None) -> str | None:
    if not text:
        return None
    parts = text.split(maxsplit=1)
    if len(parts) < 2:
        return None
    return parts[1].strip() or None


def miniapp_keyboard(lang: str, start_param: str | None = None) -> InlineKeyboardMarkup | None:
    url = build_miniapp_url(start_param=start_param)
    if not url:
        return None
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t(lang, "cmd_start.open_miniapp"),
                    web_app=WebAppInfo(url=url),
                )
            ]
        ]
    )


@router.message(F.text == "/start")
async def cmd_start(msg: Message):
    lang = get_user_lang(msg.from_user.id)
    start_param = extract_start_param(msg.text)
    miniapp_kb = miniapp_keyboard(lang, start_param=start_param)

    if miniapp_kb:
        await msg.answer(
            f"{t(lang, 'cmd_start.welcome')}\n\n{t(lang, 'cmd_start.miniapp_hint')}",
            reply_markup=miniapp_kb,
        )

    # по умолчанию — обычное меню
    kb = main_menu_kb(lang)
    # если пользователь — админ, показываем меню с кнопкой "Адмінка"/"Admin"
    if is_admin_user(msg.from_user.id):
        kb = main_menu_kb_admin(lang)
    await msg.answer(t(lang, "cmd_start.welcome"), reply_markup=kb)


@router.message(F.text.startswith("/app"))
async def cmd_app(msg: Message):
    lang = get_user_lang(msg.from_user.id)
    start_param = extract_start_param(msg.text)
    miniapp_kb = miniapp_keyboard(lang, start_param=start_param)
    if not miniapp_kb:
        return await msg.answer("MINI_APP_URL is not configured")

    await msg.answer(t(lang, "cmd_start.miniapp_hint"), reply_markup=miniapp_kb)
