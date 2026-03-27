from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton

from bot.i18n.catalogs import LANGS, t
from bot.services.user_profile import get_user_lang
from core.db import get_session
from core.models import User

router = Router()


def lang_kb():
    buttons = []
    for code, name in LANGS.items():
        buttons.append([KeyboardButton(text=f"{name} ({code})")])
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


@router.message(F.text == "/lang")
async def cmd_lang(msg: Message):
    lang = get_user_lang(msg.from_user.id)
    await msg.answer(t(lang, "lang.prompt"), reply_markup=lang_kb())


# ✅ обработка кнопки "Мова" / "Language" из главного меню
@router.message(F.text.in_(["Мова", "Language"]))
async def lang_button(msg: Message):
    lang = get_user_lang(msg.from_user.id)
    await msg.answer(t(lang, "lang.prompt"), reply_markup=lang_kb())


# выбор нового языка по кнопке вида "Українська (uk)" / "English (en)"
@router.message(F.text.regexp(r".*\((uk|en)\)$"))
async def set_lang(msg: Message):
    code = msg.text.strip()[-3:-1]  # достаем uk/en из скобочек
    code = "uk" if code == "uk" else "en"

    with get_session() as db:
        u = db.query(User).filter(User.tg_id == msg.from_user.id).one_or_none()
        if not u:
            u = User(tg_id=msg.from_user.id, lang=code)
            db.add(u)
        else:
            u.lang = code
        db.commit()
        lang_name = LANGS.get(code, code)

    await msg.answer(t(code, "lang.set", lang_name=lang_name))
