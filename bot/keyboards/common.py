from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from bot.i18n.catalogs import t, safe_lang


def main_menu_kb(lang: str = "uk") -> ReplyKeyboardMarkup:
    """
    Главное меню для пользователя.

    Ряды:
    1) Карта → Crypto   |  Crypto → Карта
    2) Готівка → Crypto |  Crypto → Готівка
    3) IBAN → Crypto    |  Crypto → IBAN
    4) Мої заявки | Мова
    """
    lang = safe_lang(lang)

    row1 = [
        KeyboardButton(text=t(lang, "menu.direction.card_to_crypto")),
        KeyboardButton(text=t(lang, "menu.direction.crypto_to_card")),
    ]
    row2 = [
        KeyboardButton(text=t(lang, "menu.direction.cash_to_crypto")),
        KeyboardButton(text=t(lang, "menu.direction.crypto_to_cash")),
    ]
    row3 = [
        KeyboardButton(text=t(lang, "menu.direction.iban_to_crypto")),
        KeyboardButton(text=t(lang, "menu.direction.crypto_to_iban")),
    ]
    row_bottom = [
        KeyboardButton(text=t(lang, "menu.my_orders")),
        KeyboardButton(text=t(lang, "menu.lang")),
    ]

    return ReplyKeyboardMarkup(
        keyboard=[row1, row2, row3, row_bottom],
        resize_keyboard=True,
    )


def main_menu_kb_admin(lang: str = "uk") -> ReplyKeyboardMarkup:
    """
    Главное меню для админа: то же, что и у пользователя, плюс внизу 'Адмінка' / 'Admin'.
    """
    lang = safe_lang(lang)

    row1 = [
        KeyboardButton(text=t(lang, "menu.direction.card_to_crypto")),
        KeyboardButton(text=t(lang, "menu.direction.crypto_to_card")),
    ]
    row2 = [
        KeyboardButton(text=t(lang, "menu.direction.cash_to_crypto")),
        KeyboardButton(text=t(lang, "menu.direction.crypto_to_cash")),
    ]
    row3 = [
        KeyboardButton(text=t(lang, "menu.direction.iban_to_crypto")),
        KeyboardButton(text=t(lang, "menu.direction.crypto_to_iban")),
    ]
    row_bottom = [
        KeyboardButton(text=t(lang, "menu.my_orders")),
        KeyboardButton(text=t(lang, "menu.lang")),
    ]

    admin_text = "Адмінка" if lang == "uk" else "Admin"
    admin_row = [KeyboardButton(text=admin_text)]

    return ReplyKeyboardMarkup(
        keyboard=[row1, row2, row3, row_bottom, admin_row],
        resize_keyboard=True,
    )
