from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot.i18n.catalogs import safe_lang

def admin_main_kb(lang: str = "uk") -> InlineKeyboardMarkup:
    lang = safe_lang(lang)
    if lang == "uk":
        btn_new = "🆕 Нові заявки"
        btn_all = "📄 Усі заявки"
        btn_rates = "⚙️ Курс USDT"
        btn_stats = "📊 Статистика"
        btn_broadcast = "📢 Розсилка"
    else:
        btn_new = "🆕 New orders"
        btn_all = "📄 All orders"
        btn_rates = "⚙️ USDT rate"
        btn_stats = "📊 Stats"
        btn_broadcast = "📢 Broadcast"

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=btn_new, callback_data="admin:new_list"),
                InlineKeyboardButton(text=btn_all, callback_data="admin:all_list"),
            ],
            [
                InlineKeyboardButton(text=btn_rates, callback_data="admin:rate_help"),
                InlineKeyboardButton(text=btn_stats, callback_data="admin:stats"),
            ],
            [
                InlineKeyboardButton(text=btn_broadcast, callback_data="admin:broadcast"),
            ],
        ]
    )


def order_manage_kb(order_id: int, lang: str = "uk") -> InlineKeyboardMarkup:
    """
    Клавиатура управления конкретной заявкой для админа.
    Есть:
    - кнопка написать клиенту
    - кнопки смены статуса (в работе, ожидание клиента, завершено, отмена)
    - кнопки оплаты (оплата получена / не получена)
    """
    lang = safe_lang(lang)
    if lang == "uk":
        btn_reply = "💬 Написати клієнту"
        btn_inwork = "🚧 В роботі"
        btn_wait = "⏳ Очікування клієнта"
        btn_done = "✅ Завершено"
        btn_cancel = "🚫 Скасувати"
        btn_paid = "💰 Оплата отримана"
        btn_notpaid = "❗ Оплата не отримана"
    else:
        btn_reply = "💬 Message client"
        btn_inwork = "🚧 In progress"
        btn_wait = "⏳ Waiting client"
        btn_done = "✅ Completed"
        btn_cancel = "🚫 Cancel"
        btn_paid = "💰 Payment received"
        btn_notpaid = "❗ Payment not received"

    return InlineKeyboardMarkup(
        inline_keyboard=[
            # ряд 1: написать + в роботі
            [
                InlineKeyboardButton(text=btn_reply, callback_data=f"pay_msg:{order_id}"),
                InlineKeyboardButton(text=btn_inwork, callback_data=f"st_inwork:{order_id}"),
            ],
            # ряд 2: очікування клієнта + оплата отримана
            [
                InlineKeyboardButton(text=btn_wait, callback_data=f"st_wait:{order_id}"),
                InlineKeyboardButton(text=btn_paid, callback_data=f"pay_ok:{order_id}"),
            ],
            # ряд 3: завершено + скасувати
            [
                InlineKeyboardButton(text=btn_done, callback_data=f"st_done:{order_id}"),
                InlineKeyboardButton(text=btn_cancel, callback_data=f"st_cancel:{order_id}"),
            ],
            # ряд 4: оплата не отримана (одиночная, щоб випадково не натиснути)
            [
                InlineKeyboardButton(text=btn_notpaid, callback_data=f"pay_no:{order_id}"),
            ],
        ]
    )
