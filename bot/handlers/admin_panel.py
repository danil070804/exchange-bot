from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext

from bot.keyboards.admin import admin_main_kb, order_manage_kb
from bot.services.user_profile import get_user_lang
from core.config import settings
from bot.i18n.catalogs import t
from bot.services.backend_client import backend_client

router = Router()


async def send_client_message_with_reply(bot, user_tg_id: int, order_id: int | None, text: str):
    """
    Отправляем клиенту сообщение от бота с кнопкой 'Відповісти менеджеру',
    чтобы клієнт міг почати діалог.
    """
    keyboard = None
    if order_id:
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="💬 Відповісти менеджеру",
                        callback_data=f"cl_reply:{order_id}",
                    )
                ]
            ]
        )
    await bot.send_message(chat_id=user_tg_id, text=text, reply_markup=keyboard)



class AdminReplyFSM(StatesGroup):
    waiting_for_text = State()




def is_admin(user_id: int) -> bool:
    if not settings.ADMIN_IDS:
        return False
    try:
        admin_ids = {int(x) for x in settings.ADMIN_IDS.split(",") if x.strip()}
    except Exception:
        return False
    return user_id in admin_ids


def format_order_line(o: dict) -> str:
    direction_human = {
        "CARD_UAH_TO_CRYPTO_USDT": "Карта → Crypto (USDT)",
        "CRYPTO_USDT_TO_CARD_UAH": "Crypto (USDT) → Карта",
        "CASH_UAH_TO_CRYPTO_USDT": "Готівка → Crypto (USDT)",
        "CRYPTO_USDT_TO_CASH_UAH": "Crypto (USDT) → Готівка",
        "IBAN_UAH_TO_CRYPTO_USDT": "IBAN → Crypto (USDT)",
        "CRYPTO_USDT_TO_IBAN_UAH": "Crypto (USDT) → IBAN",
    }.get(o["direction"], o["direction"])
    return (
        f"#{o['id']} • {direction_human} • {o['status']}\n"
        f"👤 {o.get('user_tg_id', '?')}\n"
        f"💰 {o.get('amount_from', 0)} {o.get('base_currency')}\n"
    )


async def admin_fetch_orders(status: list[str] | None = None, limit: int = 20) -> list[dict]:
    try:
        data = await backend_client.admin_list_orders(limit=limit, status=status)
        return data.get("items", [])
    except Exception:
        return []


async def admin_fetch_order(order_id: int) -> dict | None:
    try:
        return await backend_client.admin_get_order(order_id)
    except Exception:
        return None


@router.message(F.text == "/admin")
async def admin_entry(msg: Message):
    if not is_admin(msg.from_user.id):
        return await msg.answer("⛔ Доступ заборонено / Access denied.")
    lang = get_user_lang(msg.from_user.id)
    text_uk = "Адмін-панель. Оберіть дію:"
    text_en = "Admin panel. Choose an action:"
    text = text_uk if lang == "uk" else text_en
    await msg.answer(text, reply_markup=admin_main_kb(lang))

@router.message(F.text.in_(["Адмінка", "Админка", "Admin", "Admin panel"]))
async def admin_entry_button(msg: Message):
    """Обработка нажатия кнопки 'Адмінка' / 'Admin' — ведёт в ту же админ-панель, что и /admin."""
    return await admin_entry(msg)


@router.callback_query(F.data == "admin:new_list")
async def admin_new_list(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return await call.answer("Access denied", show_alert=True)
    lang = get_user_lang(call.from_user.id)
    rows = await admin_fetch_orders(status=["pending_payment"], limit=20)
    if not rows:
        txt = "Немає нових заявок." if lang == "uk" else "No new orders."
        await call.message.answer(txt)
        return await call.answer()
    for o in rows:
        txt = format_order_line(o)
        await call.message.answer(txt, reply_markup=order_manage_kb(o["id"], lang))
    await call.answer()


@router.callback_query(F.data == "admin:all_list")
async def admin_all_list(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return await call.answer("Access denied", show_alert=True)
    lang = get_user_lang(call.from_user.id)
    rows = await admin_fetch_orders(limit=20)
    if not rows:
        txt = "Заявок поки немає." if lang == "uk" else "No orders yet."
        await call.message.answer(txt)
        return await call.answer()
    for o in rows:
        txt = format_order_line(o)
        await call.message.answer(txt, reply_markup=order_manage_kb(o["id"], lang))
    await call.answer()


@router.callback_query(F.data == "admin:rate_help")
async def admin_rate_help(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return await call.answer("Access denied", show_alert=True)
    lang = get_user_lang(call.from_user.id)
    current = "backend"

    if lang == "uk":
        text = (
            "Поточний курс зберігається у backend. "
            "Щоб змінити, надішліть команду:\n"
            "/setrate 41.5"
        )
    else:
        text = (
            "Base rate is stored in backend. "
            "To change it, send:\n"
            "/setrate 41.5"
        )
    await call.message.answer(text)
    await call.answer()


@router.message(F.text.startswith("/setrate"))
async def admin_set_rate(msg: Message):
    if not is_admin(msg.from_user.id):
        return await msg.answer("Access denied")

    lang = get_user_lang(msg.from_user.id)
    parts = msg.text.split()

    if len(parts) != 2:
        if lang == "uk":
            return await msg.answer("Формат: /setrate 41.5 (1 USDT = 41.5 UAH)")
        else:
            return await msg.answer("Format: /setrate 41.5 (1 USDT = 41.5 UAH)")

    try:
        usdt_uah = float(parts[1])
        if usdt_uah <= 0:
            raise ValueError
    except Exception:
        if lang == "uk":
            return await msg.answer("Невірне число. Приклад: /setrate 41.5")
        else:
            return await msg.answer("Invalid number. Example: /setrate 41.5")

    uah_usdt = 1.0 / usdt_uah

    try:
        await backend_client.admin_set_rate_pair(
            base_currency="USDT",
            quote_currency="UAH",
            buy_rate=usdt_uah,
            sell_rate=usdt_uah,
            source="manual",
        )
    except Exception:
        if lang == "uk":
            return await msg.answer("Не вдалося оновити курс у backend.")
        else:
            return await msg.answer("Failed to update rate in backend.")

    if lang == "uk":
        txt = f"✅ Курс оновлено: 1 USDT = {usdt_uah:.4f} UAH (1 UAH = {uah_usdt:.6f} USDT)"
    else:
        txt = f"✅ Rate updated: 1 USDT = {usdt_uah:.4f} UAH (1 UAH = {uah_usdt:.6f} USDT)"

    await msg.answer(txt)


@router.message(F.text.startswith("/quote"))
async def admin_quote(msg: Message):
    """
    Авто-расчёт по заявке и отправка клиенту.

    Формат:
    /quote ID КУРС

    Пример:
    /quote 12 41.5   (1 USDT = 41.5 UAH)
    """
    if not is_admin(msg.from_user.id):
        return await msg.answer("Access denied")

    parts = msg.text.split()
    if len(parts) != 3:
        return await msg.answer("Формат: /quote ID КУРС  (наприклад /quote 12 41.5)")

    try:
        order_id = int(parts[1])
        rate = float(parts[2])
    except ValueError:
        return await msg.answer("Невірний формат. Приклад: /quote 12 41.5")

    if rate <= 0:
        return await msg.answer("Курс повинен бути > 0")

    order = await admin_fetch_order(order_id)
    if not order:
        return await msg.answer("Заявка не знайдена")

    client_lang = "uk"
    amount_base = float(order.get("amount_from") or 0.0)

    # Реквизити берем из .env (з fallback-ом на дефолт, если вдруг не задано)
    card_number = settings.CARD_NUMBER or "НЕ ЗАДАНА КАРТА В .env"
    usdt_trc_address = settings.USDT_TRC20_ADDRESS or "TJo6qC7Dzdm3KdzQySZy9PkYWnnpThVMuJ"

    # Формируем текст клиенту в зависимости от направления
    if order["direction"] == "CARD_UAH_TO_CRYPTO_USDT":
        # Клиент платит UAH, получает USDT
        amount_uah = amount_base
        amount_usdt = amount_uah / rate if rate else 0.0

        if client_lang == "uk":
            text_to_client = (
                "🔹 <b>Обмін Карта → Crypto (USDT)</b>\n\n"
                f"Номер заявки: <b>#{order_id}</b>\n"
                f"Сума до оплати: <b>{amount_uah:.2f} UAH</b>\n"
                f"Курс: <b>1 USDT = {rate:.4f} UAH</b> (комісія включена)\n\n"
                f"Ви отримаєте ≈ <b>{amount_usdt:.2f} USDT</b>.\n\n"
                "Реквізити для оплати карткою:\n"
                f"<code>{card_number}</code>\n"
                f"Призначення: ORDER #{order_id}\n\n"
                "Після оплати, будь ласка, надішліть чек у цей чат."
            )
        else:
            text_to_client = (
                "🔹 <b>Exchange Card → Crypto (USDT)</b>\n\n"
                f"Order ID: <b>#{order_id}</b>\n"
                f"Amount to pay: <b>{amount_uah:.2f} UAH</b>\n"
                f"Rate: <b>1 USDT = {rate:.4f} UAH</b> (fee included)\n\n"
                f"You will receive ≈ <b>{amount_usdt:.2f} USDT</b>.\n\n"
                "Card payment details:\n"
                f"<code>{card_number}</code>\n"
                f"Payment reference: ORDER #{order_id}\n\n"
                "After the payment, please send the receipt in this chat."
            )

    elif order["direction"] == "CRYPTO_USDT_TO_CARD_UAH":
        # Клієнт хоче отримати UAH на картку, а платить USDT.
        # У заявці amount_base ми зберігаємо суму саме в UAH.
        amount_uah = amount_base
        amount_usdt = amount_uah / rate if rate else 0.0

        if client_lang == "uk":
            text_to_client = (
                "🔹 <b>Обмін Crypto (USDT) → Карта UAH</b>\n\n"
                f"Номер заявки: <b>#{order_id}</b>\n"
                f"Сума до отримання: <b>{amount_uah:.2f} UAH</b>\n"
                f"Курс: <b>1 USDT = {rate:.4f} UAH</b> (комісія включена)\n\n"
                f"Для цього вам потрібно відправити ≈ <b>{amount_usdt:.2f} USDT</b>.\n\n"
                "Надішліть USDT у мережі <b>TRC20</b> на адресу:\n"
                f"<code>{usdt_trc_address}</code>\n\n"
                "Після відправки, будь ласка, надішліть TXID/хеш транзакції у цей чат."
            )
        else:
            text_to_client = (
                "🔹 <b>Exchange Crypto (USDT) → UAH card</b>\n\n"
                f"Order ID: <b>#{order_id}</b>\n"
                f"Amount to receive: <b>{amount_uah:.2f} UAH</b>\n"
                f"Rate: <b>1 USDT = {rate:.4f} UAH</b> (fee included)\n\n"
                f"To get this amount you need to send ≈ <b>{amount_usdt:.2f} USDT</b>.\n\n"
                "Send USDT via <b>TRC20</b> network to:\n"
                f"<code>{usdt_trc_address}</code>\n\n"
                "After sending, please provide TXID / transaction hash in this chat."
            )
    else:
        # На всякий случай fallback
        text_to_client = "Щось пішло не так з напрямком заявки. Зверніться до оператора."

    # отправляем клиенту сообщение
    try:
        await msg.bot.send_message(chat_id=order.get("user_tg_id"), text=text_to_client)
    except Exception:
        return await msg.answer("Не вдалося надіслати повідомлення клієнту")

    # сохраняем рассчитанный курс в backend
    try:
        await backend_client.admin_update_quote(order_id=order_id, rate=rate, amount_to=amount_usdt)
    except Exception:
        pass

    await msg.answer("Повідомлення з курсом та сумою надіслано клієнту.")


@router.message(AdminReplyFSM.waiting_for_text)
async def admin_reply_text(msg: Message, state: FSMContext):
    """Адмін вводить текст, ми відправляємо його клієнту по потрібній заявці."""
    if not is_admin(msg.from_user.id):
        return

    data = await state.get_data()
    order_id = data.get("order_id")
    if not order_id:
        await state.clear()
        return await msg.answer("Не знайдена заявка для відповіді.")

    order = await admin_fetch_order(order_id)
    if not order:
        await state.clear()
        return await msg.answer("Заявка не знайдена.")
    user_tg = order.get("user_tg_id")
    if not user_tg:
        await state.clear()
        return await msg.answer("Користувач не знайдений.")

    text_to_client = msg.text or ""
    if not text_to_client.strip():
        return await msg.answer("Повідомлення порожнє. Напишіть текст для клієнта.")

    try:
        await send_client_message_with_reply(msg.bot, user_tg, order_id, text_to_client)
    except Exception:
        await state.clear()
        return await msg.answer("Не вдалося надіслати повідомлення клієнту")

    await state.clear()
    await msg.answer("Повідомлення клієнту надіслано.")


@router.message(F.text.startswith("/reply"))
async def admin_reply(msg: Message):
    """
    Ручна відповідь клієнту по заявці.

    Формат:
    /reply ID текст для клієнта
    """
    if not is_admin(msg.from_user.id):
        return await msg.answer("Access denied")

    parts = msg.text.split(maxsplit=2)
    if len(parts) < 3:
        return await msg.answer("Формат: /reply ID текст")

    try:
        order_id = int(parts[1])
    except ValueError:
        return await msg.answer("Невірний ID заявки")

    text_to_client = parts[2]

    order = await admin_fetch_order(order_id)
    if not order:
        return await msg.answer("Заявка не знайдена")
    user_tg = order.get("user_tg_id")
    if not user_tg:
        return await msg.answer("Користувач не знайдений")

    try:
        await send_client_message_with_reply(msg.bot, user_tg, order_id, text_to_client)
    except Exception:
        return await msg.answer("Не вдалося надіслати повідомлення клієнту")

    await msg.answer("Повідомлення клієнту надіслано.")


@router.message(F.text.startswith("/paid"))
async def admin_paid(msg: Message):
    """Быстрое сообщение клиенту: оплата получена, попросить телефон."""
    if not is_admin(msg.from_user.id):
        return await msg.answer("Access denied")

    parts = msg.text.split(maxsplit=2)
    if len(parts) < 2:
        return await msg.answer("Формат: /paid ID [доп. текст]")

    try:
        order_id = int(parts[1])
    except ValueError:
        return await msg.answer("Невірний ID заявки")

    extra_text = parts[2] if len(parts) >= 3 else None

    order = await admin_fetch_order(order_id)
    if not order:
        return await msg.answer("Заявка не знайдена")
    user_tg = order.get("user_tg_id")
    if not user_tg:
        return await msg.answer("Користувач не знайдений")
    client_lang = "uk"

    try:
        await backend_client.admin_set_status(order_id=order_id, status_value="payment_review")
    except Exception:
        pass

    # Текст клиенту
    if client_lang == "uk":
        text_to_client = (
            f"Ми отримали вашу оплату по заявці #{order_id}.\n"
            "Будь ласка, напишіть ваш мобільний номер телефону (у форматі +380...), "
            "щоб ми могли зателефонувати та підтвердити операцію та подальші дії."
        )
    else:
        text_to_client = (
            f"We have received your payment for order #{order_id}.\n"
            "Please send your mobile phone number (in international format), "
            "so we can call you to confirm the operation and next steps."
        )

    if extra_text:
        text_to_client += "\n\n" + extra_text

    try:
        await send_client_message_with_reply(msg.bot, user_tg, order_id, text_to_client)
    except Exception:
        return await msg.answer("Не вдалося надіслати повідомлення клієнту")

    await msg.answer("Клієнту надіслано повідомлення про отримання оплати та запит номера телефону.")


@router.message(F.text.startswith("/notpaid"))
async def admin_not_paid(msg: Message):
    """Быстрое сообщение клиенту: оплата НЕ подтверждена, попросить телефон."""
    if not is_admin(msg.from_user.id):
        return await msg.answer("Access denied")

    parts = msg.text.split(maxsplit=2)
    if len(parts) < 2:
        return await msg.answer("Формат: /notpaid ID [доп. текст]")

    try:
        order_id = int(parts[1])
    except ValueError:
        return await msg.answer("Невірний ID заявки")

    extra_text = parts[2] if len(parts) >= 3 else None

    order = await admin_fetch_order(order_id)
    if not order:
        return await msg.answer("Заявка не знайдена")
    user_tg = order.get("user_tg_id")
    if not user_tg:
        return await msg.answer("Користувач не знайдений")
    client_lang = "uk"

    try:
        await backend_client.admin_set_status(order_id=order_id, status_value="rejected")
    except Exception:
        pass

    if client_lang == "uk":
        text_to_client = (
            f"Поки що ми не бачимо надходження оплати по заявці #{order_id}.\n"
            "Якщо ви вже оплатили, будь ласка, надішліть чек / TX hash у цей чат "
            "та напишіть ваш мобільний номер телефону (у форматі +380...), "
            "щоб ми могли зателефонувати та уточнити деталі."
        )
    else:
        text_to_client = (
            f"So far we do not see your payment for order #{order_id}.\n"
            "If you already paid, please send the receipt / TX hash in this chat "
            "and write your mobile phone number, so we can call you and clarify details."
        )

    if extra_text:
        text_to_client += "\n\n" + extra_text

    try:
        await send_client_message_with_reply(msg.bot, user_tg, order_id, text_to_client)
    except Exception:
        return await msg.answer("Не вдалося надіслати повідомлення клієнту")

    await msg.answer("Клієнту надіслано повідомлення про відсутність оплати та запит номера телефону.")


@router.callback_query(F.data.startswith("pay_ok:"))
async def cb_pay_ok(call: CallbackQuery):
    """Инлайн-кнопка 'Оплата отримана' под подтверждением оплаты."""
    if not is_admin(call.from_user.id):
        return await call.answer("Access denied", show_alert=True)

    try:
        order_id = int(call.data.split(":", 1)[1])
    except (ValueError, IndexError):
        return await call.answer("Некоректний ID заявки", show_alert=True)

    order = await admin_fetch_order(order_id)
    if not order:
        return await call.answer("Заявку не знайдено", show_alert=True)
    user_tg = order.get("user_tg_id")
    if not user_tg:
        return await call.answer("Користувача не знайдено", show_alert=True)
    client_lang = "uk"

    try:
        await backend_client.admin_set_status(order_id=order_id, status_value="payment_review")
    except Exception:
        pass

    if client_lang == "uk":
        text_to_client = (
            f"Ми отримали вашу оплату по заявці #{order_id}.\n"
            "Будь ласка, напишіть ваш мобільний номер телефону (у форматі +380...), "
            "щоб ми могли зателефонувати та підтвердити операцію та подальші дії."
        )
    else:
        text_to_client = (
            f"We have received your payment for order #{order_id}.\n"
            "Please send your mobile phone number (in international format), "
            "so we can call you to confirm the operation and next steps."
        )

    try:
        await send_client_message_with_reply(call.message.bot, user_tg, order_id, text_to_client)
    except Exception:
        return await call.answer("Не вдалося надіслати повідомлення клієнту", show_alert=True)

    await call.answer("Клієнта повідомлено про отримання оплати.", show_alert=False)


@router.callback_query(F.data.startswith("pay_no:"))
async def cb_pay_no(call: CallbackQuery):
    """Инлайн-кнопка 'Оплата не отримана' под подтверждением оплаты."""
    if not is_admin(call.from_user.id):
        return await call.answer("Access denied", show_alert=True)

    try:
        order_id = int(call.data.split(":", 1)[1])
    except (ValueError, IndexError):
        return await call.answer("Некоректний ID заявки", show_alert=True)

    order = await admin_fetch_order(order_id)
    if not order:
        return await call.answer("Заявку не знайдено", show_alert=True)
    user_tg = order.get("user_tg_id")
    if not user_tg:
        return await call.answer("Користувача не знайдено", show_alert=True)
    client_lang = "uk"

    try:
        await backend_client.admin_set_status(order_id=order_id, status_value="rejected")
    except Exception:
        pass

    if client_lang == "uk":
        text_to_client = (
            f"Поки що ми не бачимо надходження оплати по заявці #{order_id}.\n"
            "Якщо ви вже оплатили, будь ласка, надішліть чек / TX hash у цей чат "
            "та напишіть ваш мобільний номер телефону (у форматі +380...), "
            "щоб ми могли зателефонувати та уточнити деталі."
        )
    else:
        text_to_client = (
            f"So far we do not see your payment for order #{order_id}.\n"
            "If you already paid, please send the receipt / TX hash in this chat "
            "and write your mobile phone number, so we can call you and clarify details."
        )

    try:
        await send_client_message_with_reply(call.message.bot, user_tg, order_id, text_to_client)
    except Exception:
        return await call.answer("Не вдалося надіслати повідомлення клієнту", show_alert=True)

    await call.answer("Клієнта повідомлено про відсутність оплати.", show_alert=False)




@router.callback_query(F.data.startswith("pay_msg:"))
async def cb_pay_msg(call: CallbackQuery, state: FSMContext):
    """Инлайн-кнопка 'Написати клієнту' / 'Відповісти' — включає режим набору повідомлення клієнту."""
    if not is_admin(call.from_user.id):
        return await call.answer("Access denied", show_alert=True)

    try:
        order_id = int(call.data.split(":", 1)[1])
    except (ValueError, IndexError):
        return await call.answer("Некоректний ID заявки", show_alert=True)

    # зберігаємо, до якої заявки відповідає адмін
    await state.set_state(AdminReplyFSM.waiting_for_text)
    await state.update_data(order_id=order_id)

    lang = get_user_lang(call.from_user.id)
    if lang == "uk":
        text = (
            f"Напишіть повідомлення для клієнта по заявці #{order_id}.\n\n"
            "Це повідомлення буде відправлено від імені бота одразу після вашого вводу."
        )
    else:
        text = (
            f"Type a message for the client for order #{order_id}.\n\n"
            "It will be sent to the client right after you send it."
        )

    await call.message.answer(text)
    await call.answer()


@router.callback_query(F.data.startswith("st_inwork:"))
async def cb_status_inwork(call: CallbackQuery):
    """Кнопка 'В роботі' / 'In progress' — помечаем заявку как in_progress."""
    if not is_admin(call.from_user.id):
        return await call.answer("Access denied", show_alert=True)

    try:
        order_id = int(call.data.split(":", 1)[1])
    except (ValueError, IndexError):
        return await call.answer("Некоректний ID заявки", show_alert=True)

    try:
        await backend_client.admin_set_status(order_id=order_id, status_value="processing")
    except Exception:
        return await call.answer("Не вдалося оновити статус", show_alert=True)

    order = await admin_fetch_order(order_id)
    if order:
        try:
            lang = get_user_lang(call.from_user.id)
            text = format_order_line(order)
            await call.message.edit_text(text, reply_markup=order_manage_kb(order_id, lang))
        except Exception:
            pass

    lang = get_user_lang(call.from_user.id)
    if lang == "uk":
        note = "Статус заявки змінено на 'в роботі'."
    else:
        note = "Order status set to 'in progress'."
    await call.answer(note, show_alert=False)


@router.callback_query(F.data.startswith("st_wait:"))
async def cb_status_wait(call: CallbackQuery):
    """Кнопка 'Очікування клієнта' / 'Waiting client'."""
    if not is_admin(call.from_user.id):
        return await call.answer("Access denied", show_alert=True)

    try:
        order_id = int(call.data.split(":", 1)[1])
    except (ValueError, IndexError):
        return await call.answer("Некоректний ID заявки", show_alert=True)

    try:
        await backend_client.admin_set_status(order_id=order_id, status_value="payment_review")
    except Exception:
        return await call.answer("Не вдалося оновити статус", show_alert=True)

    order = await admin_fetch_order(order_id)
    if order:
        try:
            lang = get_user_lang(call.from_user.id)
            text = format_order_line(order)
            await call.message.edit_text(text, reply_markup=order_manage_kb(order_id, lang))
        except Exception:
            pass

    lang = get_user_lang(call.from_user.id)
    if lang == "uk":
        note = "Статус заявки змінено на 'очікування клієнта'."
    else:
        note = "Order status set to 'waiting for client'."
    await call.answer(note, show_alert=False)


@router.callback_query(F.data.startswith("st_done:"))
async def cb_status_done(call: CallbackQuery):
    """Кнопка 'Завершено' / 'Completed'."""
    if not is_admin(call.from_user.id):
        return await call.answer("Access denied", show_alert=True)

    try:
        order_id = int(call.data.split(":", 1)[1])
    except (ValueError, IndexError):
        return await call.answer("Некоректний ID заявки", show_alert=True)

    try:
        await backend_client.admin_set_status(order_id=order_id, status_value="completed")
    except Exception:
        return await call.answer("Не вдалося оновити статус", show_alert=True)

    order = await admin_fetch_order(order_id)
    if order:
        try:
            lang = get_user_lang(call.from_user.id)
            text = format_order_line(order)
            await call.message.edit_text(text, reply_markup=order_manage_kb(order_id, lang))
        except Exception:
            pass

    lang = get_user_lang(call.from_user.id)
    if lang == "uk":
        note = "Статус заявки змінено на 'завершено'."
    else:
        note = "Order status set to 'completed'."
    await call.answer(note, show_alert=False)


@router.callback_query(F.data.startswith("st_cancel:"))
async def cb_status_cancel(call: CallbackQuery):
    """Кнопка 'Скасувати' / 'Cancel' — помечаем заявку как rejected без текста про оплату."""
    if not is_admin(call.from_user.id):
        return await call.answer("Access denied", show_alert=True)

    try:
        order_id = int(call.data.split(":", 1)[1])
    except (ValueError, IndexError):
        return await call.answer("Некоректний ID заявки", show_alert=True)

    try:
        await backend_client.admin_set_status(order_id=order_id, status_value="cancelled")
    except Exception:
        return await call.answer("Не вдалося оновити статус", show_alert=True)

    order = await admin_fetch_order(order_id)
    if order:
        try:
            lang = get_user_lang(call.from_user.id)
            text = format_order_line(order)
            await call.message.edit_text(text, reply_markup=order_manage_kb(order_id, lang))
        except Exception:
            pass

    lang = get_user_lang(call.from_user.id)
    if lang == "uk":
        note = "Заявку скасовано."
    else:
        note = "Order has been cancelled."
    await call.answer(note, show_alert=False)


@router.callback_query(F.data == "admin:stats")
async def admin_stats(call: CallbackQuery):
    """Показати просту статистику по клієнтам та заявкам."""
    if not is_admin(call.from_user.id):
        return await call.answer("Access denied", show_alert=True)

    lang = get_user_lang(call.from_user.id)
    text = "📊 Статистика буде доступна в адмін-UI backend." if lang == "uk" else "📊 Stats will be available in backend admin UI."

    try:
        await call.message.edit_text(text, parse_mode="HTML", reply_markup=admin_main_kb(lang))
    except Exception:
        # если не можем отредактировать — просто отправим новое сообщение
        await call.message.answer(text, parse_mode="HTML", reply_markup=admin_main_kb(lang))
    await call.answer()


@router.callback_query(F.data == "admin:broadcast")
async def admin_broadcast_info(call: CallbackQuery):
    """Поясняем админу, как сделать рассылку через /broadcast."""
    if not is_admin(call.from_user.id):
        return await call.answer("Access denied", show_alert=True)

    lang = get_user_lang(call.from_user.id)
    if lang == "uk":
        text = (
            "📢 <b>Розсилка</b>\n\n"
            "Щоб надіслати розсилку всім клієнтам, використайте команду:\n"
            "<code>/broadcast ТЕКСТ_РОЗСИЛКИ</code>"
        )
    else:
        text = (
            "📢 <b>Broadcast</b>\n\n"
            "To send a broadcast to all clients, use:\n"
            "<code>/broadcast YOUR_MESSAGE</code>"
        )

    try:
        await call.message.edit_text(text, parse_mode="HTML", reply_markup=admin_main_kb(lang))
    except Exception:
        await call.message.answer(text, parse_mode="HTML", reply_markup=admin_main_kb(lang))
    await call.answer()


@router.message(F.text.startswith("/broadcast"))
async def admin_broadcast(msg: Message):
    """Проста розсилка: /broadcast ТЕКСТ — надсилаємо всім клієнтам."""
    if not is_admin(msg.from_user.id):
        return await msg.answer("Access denied")

    parts = msg.text.split(maxsplit=1)
    if len(parts) < 2:
        return await msg.answer("Формат: /broadcast ТЕКСТ_РОЗСИЛКИ")

    await msg.answer("Розсилка недоступна у цій версії. Використайте backend/admin UI.")
