from aiogram import Router, F
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from bot.keyboards.common import main_menu_kb
from bot.keyboards.admin import order_manage_kb
from bot.services.limits import check_limits
from bot.i18n.catalogs import t
from core.config import settings
from bot.services.pricing import get_market_rate
from bot.services.backend_client import backend_client

router = Router()





class OrderFSM(StatesGroup):
    choose_direction = State()
    input_amount = State()
    input_wallet = State()
    input_card = State()
    input_iban = State()

class ClientReplyFSM(StatesGroup):
    waiting_for_text = State()






def user_lang(tg_id: int) -> str:
    # Language is stored in backend; default to Ukrainian until profile API is added
    return "uk"


def detect_direction_code(text: str) -> str | None:
    """
    Определяем направление по тексту кнопки/сообщения.

    Поддерживаем:
    - Карта → Crypto (USDT)
    - Crypto (USDT) → Карта
    - Готівка / Cash / Наличка → Crypto (USDT)
    - Crypto (USDT) → Готівка / Cash / Наличка
    - IBAN → Crypto (USDT)
    - Crypto (USDT) → IBAN
    """
    t_strip = (text or "").strip().lower()
    t_low = t_strip

    # IBAN -> Crypto
    if t_strip.startswith("iban"):
        return "IBAN_UAH_TO_CRYPTO_USDT"

    # Crypto -> IBAN
    if t_strip.startswith("crypto") and "iban" in t_low:
        return "CRYPTO_USDT_TO_IBAN_UAH"

    # наличка / cash -> crypto (клиент отдаёт кэш, хочет получить крипту)
    if (
        t_strip.startswith("готівка")
        or t_strip.startswith("cash")
        or t_strip.startswith("наличка")
        or t_strip.startswith("нал ")
    ):
        return "CASH_UAH_TO_CRYPTO_USDT"

    # кнопки, начинающиеся с "crypto"
    if t_strip.startswith("crypto"):
        # crypto -> cash / наличка
        if any(w in t_low for w in ["готівка", "cash", "наличка", "нал "]):
            return "CRYPTO_USDT_TO_CASH_UAH"
        # crypto -> card
        if "карта" in t_low or "card" in t_low:
            return "CRYPTO_USDT_TO_CARD_UAH"
        # crypto -> iban
        if "iban" in t_low:
            return "CRYPTO_USDT_TO_IBAN_UAH"
        # по умолчанию считаем, что crypto -> card
        return "CRYPTO_USDT_TO_CARD_UAH"

    # карта -> crypto
    if t_strip.startswith("карта") or t_strip.startswith("card"):
        return "CARD_UAH_TO_CRYPTO_USDT"

    # общие случаи, когда текст может быть "перемешан"
    if any(w in t_low for w in ["готівка", "cash", "наличка", "нал "]) and "crypto" in t_low:
        return "CRYPTO_USDT_TO_CASH_UAH"

    if ("карта" in t_low or "card" in t_low) and "crypto" in t_low:
        card_pos_candidates = [t_low.find("карта"), t_low.find("card")]
        card_pos_candidates = [p for p in card_pos_candidates if p != -1]
        i_card = min(card_pos_candidates) if card_pos_candidates else -1
        i_crypto = t_low.find("crypto")
        if i_card != -1 and i_crypto != -1:
            return "CARD_UAH_TO_CRYPTO_USDT" if i_card < i_crypto else "CRYPTO_USDT_TO_CARD_UAH"

    if "iban" in t_low and "crypto" in t_low:
        i_iban = t_low.find("iban")
        i_crypto = t_low.find("crypto")
        return "IBAN_UAH_TO_CRYPTO_USDT" if i_iban < i_crypto else "CRYPTO_USDT_TO_IBAN_UAH"

    return None


def parse_amount_and_currencies(direction_code: str, text: str):
    """
    Клиент ВЕЗДЕ вводит сумму только в гривне (UAH), независимо от направления.
    amount — це завжди UAH, які клієнт хоче оплатити або отримати.
    В базу зберігаємо:
    - base_currency = "UAH"
    - quote_currency = "USDT"
    """
    parts = text.replace(",", ".").split()
    amount = float(parts[0])

    base = "UAH"
    quote = "USDT"

    return amount, base, quote


async def create_order_record(
    *,
    msg: Message,
    direction_code: str,
    amount: float,
    base: str,
    quote: str,
    network: str | None = None,
    payment_details: dict | None = None,
) -> dict | None:
    try:
        return await backend_client.create_order(
            telegram_id=msg.from_user.id,
            username=msg.from_user.username,
            lang=msg.from_user.language_code,
            direction=direction_code,
            base_currency=base,
            quote_currency=quote,
            amount_from=amount,
            network=network,
            payment_details=payment_details,
        )
    except Exception:
        await msg.answer("Тимчасова помилка бекенду. Спробуйте ще раз за хвилину.")
        return None


async def notify_admins_new_order(
    user_tg_id: int,
    user_username: str | None,
    order_id: int,
    direction_code: str,
    amount: float,
    base: str,
    quote: str,
    bot,
    extra: str | None = None,
):
    """Отправляем инфу о новой заявке всем админам.

    extra — произвольная строка с реквизитами (кошелек, карта и т.п.),
    которая будет добавлена в текст уведомления.
    """
    direction_human = {
        "CARD_UAH_TO_CRYPTO_USDT": "Карта (UAH) → Crypto (USDT)",
        "CRYPTO_USDT_TO_CARD_UAH": "Crypto (USDT) → Карта (UAH)",
        "CASH_UAH_TO_CRYPTO_USDT": "Готівка (UAH) → Crypto (USDT)",
        "CRYPTO_USDT_TO_CASH_UAH": "Crypto (USDT) → Готівка (UAH)",
        "IBAN_UAH_TO_CRYPTO_USDT": "IBAN (UAH) → Crypto (USDT)",
        "CRYPTO_USDT_TO_IBAN_UAH": "Crypto (USDT) → IBAN (UAH)",
}.get(direction_code, direction_code)

    # Рекомендованный курс (если админ задавал его через /setrate)
    # Для зручності завжди показуємо як 1 USDT = X UAH
    rate_info = ""
    try:
        market_rate = await get_market_rate("USDT", "UAH")
        rate_info = f"\nРекомендованный курс: 1 USDT = {market_rate:.6f} UAH"
    except Exception:
        pass

    text = (
        f"🆕 Новая заявка #{order_id}\n"
        f"Направление: {direction_human}\n"
        f"Сумма: {amount} {base}\n"
        f"Клиент: {user_tg_id}"
    )
    if user_username:
        text += f" (@{user_username})"

    if extra:
        text += f"\n{extra}"

    # Краткое пояснение для админа
    text += (
        "\n\nДля керування заявкою використовуйте кнопки нижче."
    )
    if rate_info:
        text += rate_info


    # Основное уведомление в ADMIN_CHAT_ID (если задан)
    if settings.ADMIN_CHAT_ID:
        try:
            await bot.send_message(
                chat_id=settings.ADMIN_CHAT_ID,
                text=text,
                reply_markup=order_manage_kb(order_id),
            )
        except Exception:
            pass

    # Дублируем личным админам из ADMIN_IDS
    if settings.ADMIN_IDS:
        try:
            ids = {int(x) for x in settings.ADMIN_IDS.split(",") if x.strip()}
        except Exception:
            ids = set()
        for admin_id in ids:
            try:
                await bot.send_message(
                    chat_id=admin_id,
                    text=text,
                    reply_markup=order_manage_kb(order_id),
                )
            except Exception:
                pass


@router.message(F.text == "/order")
async def start_order(msg: Message, state: FSMContext):
    lang = user_lang(msg.from_user.id)
    await state.set_state(OrderFSM.choose_direction)
    await msg.answer(t(lang, "order.choose_direction"), reply_markup=main_menu_kb(lang))


@router.message(F.text.func(lambda s: "Crypto (USDT)" in s or "Crypto" in s))
async def start_order_by_button(msg: Message, state: FSMContext):
    lang = user_lang(msg.from_user.id)
    direction_code = detect_direction_code(msg.text)
    if not direction_code:
        await start_order(msg, state)
        return
    await state.update_data(direction_code=direction_code)
    await state.set_state(OrderFSM.input_amount)
    await msg.answer(t(lang, "order.input_amount"))


@router.message(OrderFSM.choose_direction)
async def choose_direction(msg: Message, state: FSMContext):
    lang = user_lang(msg.from_user.id)
    direction_code = detect_direction_code(msg.text)
    if not direction_code:
        await msg.answer(t(lang, "order.choose_direction"), reply_markup=main_menu_kb(lang))
        return
    await state.update_data(direction_code=direction_code)
    await state.set_state(OrderFSM.input_amount)
    await msg.answer(t(lang, "order.input_amount"))


@router.message(OrderFSM.input_amount)
async def input_amount(msg: Message, state: FSMContext):
    """Шаг ввода суммы. После валидации переходим к вводу реквизитов
    (кошелька / карты / IBAN в зависимости от направления).
    """
    lang = user_lang(msg.from_user.id)
    data = await state.get_data()
    direction_code = data["direction_code"]

    # парсим сумму
    try:
        amount, base, quote = parse_amount_and_currencies(direction_code, msg.text)
    except Exception:
        return await msg.answer(t(lang, "order.input_amount"))

    # простая проверка лимитов
    ok, reason = await check_limits(msg.from_user.id, amount, direction_code)
    if not ok:
        return await msg.answer(t(lang, "order.limit_exceeded", reason=reason))

    # сохраняем сумму и валюты в FSM
    await state.update_data(amount=amount, base=base, quote=quote)

    # 1) Карта → Crypto та IBAN → Crypto: просим адрес кошелька
    if direction_code in ("CARD_UAH_TO_CRYPTO_USDT", "IBAN_UAH_TO_CRYPTO_USDT"):
        if lang == "uk":
            text = "Будь ласка, надішліть адресу вашого USDT (TRC20) гаманця, куди потрібно надіслати криптовалюту."
        else:
            text = "Please send your USDT (TRC20) wallet address where you want to receive crypto."
        await state.set_state(OrderFSM.input_wallet)
        return await msg.answer(text)

    # 2) Crypto → Карта: просим номер картки
    if direction_code == "CRYPTO_USDT_TO_CARD_UAH":
        if lang == "uk":
            text = "Будь ласка, надішліть номер картки UAH, на яку потрібно надіслати гроші."
        else:
            text = "Please send the UAH card number where you want to receive the money."
        await state.set_state(OrderFSM.input_card)
        return await msg.answer(text)

    # 3) Crypto → IBAN: просим IBAN
    if direction_code == "CRYPTO_USDT_TO_IBAN_UAH":
        if lang == "uk":
            text = "Будь ласка, надішліть ваш IBAN для зарахування гривні (за прикладом, як надсилає менеджер)."
        else:
            text = "Please send your IBAN where you want to receive UAH."
        await state.set_state(OrderFSM.input_iban)
        return await msg.answer(text)

    # 4) Нал ↔ Crypto: создаём заявку сразу, без реквизитов, менеджер все уточнит в чате
    order = await create_order_record(
        msg=msg,
        direction_code=direction_code,
        amount=amount,
        base=base,
        quote=quote,
    )
    if not order:
        return
    order_id = order["id"]
    user_tg_id = msg.from_user.id
    user_username = msg.from_user.username

    await state.clear()
    await msg.answer(
        t(lang, "order.created", order_id=order_id),
        reply_markup=main_menu_kb(lang),
    )

    if direction_code == "CASH_UAH_TO_CRYPTO_USDT":
        extra = "Клієнт хоче обмін Готівка (UAH) → Crypto (USDT). Домовтеся про адресу зустрічі."
    elif direction_code == "CRYPTO_USDT_TO_CASH_UAH":
        extra = "Клієнт хоче обмін Crypto (USDT) → Готівка (UAH). Домовтеся про адресу зустрічі."
    else:
        extra = None

    await notify_admins_new_order(
        user_tg_id=user_tg_id,
        user_username=user_username,
        order_id=order_id,
        direction_code=direction_code,
        amount=amount,
        base=base,
        quote=quote,
        bot=msg.bot,
        extra=extra,
    )
    return


@router.message(OrderFSM.input_wallet)
async def input_wallet(msg: Message, state: FSMContext):
    """Получаем адрес крипто-кошелька клиента (UAH -> USDT)."""
    lang = user_lang(msg.from_user.id)
    wallet = (msg.text or "").strip()

    if not wallet or len(wallet) < 8:
        if lang == "uk":
            return await msg.answer("Адреса гаманця виглядає некоректною. Будь ласка, надішліть правильну адресу USDT (TRC20).")
        else:
            return await msg.answer("Wallet address looks invalid. Please send a correct USDT (TRC20) address.")

    data = await state.get_data()
    direction_code = data.get("direction_code")
    amount = data.get("amount")
    base = data.get("base")
    quote = data.get("quote")

    order = await create_order_record(
        msg=msg,
        direction_code=direction_code,
        amount=amount,
        base=base,
        quote=quote,
        payment_details={"payout_wallet": wallet},
    )
    if not order:
        return
    order_id = order["id"]
    user_tg_id = msg.from_user.id
    user_username = msg.from_user.username

    # очищаем состояние
    await state.clear()
    await msg.answer(
        t(lang, "order.created", order_id=order_id),
        reply_markup=main_menu_kb(lang),
    )

    # уведомляем админов, добавляем реквизиты
    extra = f"Крипто-кошелек клієнта: {wallet}"
    await notify_admins_new_order(
        user_tg_id=user_tg_id,
        user_username=user_username,
        order_id=order_id,
        direction_code=direction_code,
        amount=amount,
        base=base,
        quote=quote,
        bot=msg.bot,
        extra=extra,
    )


@router.message(OrderFSM.input_card)
async def input_card(msg: Message, state: FSMContext):
    """Получаем номер карты клиента (USDT -> UAH)."""
    lang = user_lang(msg.from_user.id)
    card = (msg.text or "").replace(" ", "").strip()

    if not card or len(card) < 8:
        if lang == "uk":
            return await msg.answer("Номер картки виглядає некоректним. Будь ласка, надішліть правильний номер картки UAH.")
        else:
            return await msg.answer("Card number looks invalid. Please send a correct UAH card number.")

    data = await state.get_data()
    direction_code = data.get("direction_code")
    amount = data.get("amount")
    base = data.get("base")
    quote = data.get("quote")

    order = await create_order_record(
        msg=msg,
        direction_code=direction_code,
        amount=amount,
        base=base,
        quote=quote,
        payment_details={"payout_card_masked": card},
    )
    if not order:
        return
    order_id = order["id"]
    user_tg_id = msg.from_user.id
    user_username = msg.from_user.username

    # очищаем состояние
    await state.clear()
    await msg.answer(
        t(lang, "order.created", order_id=order_id),
        reply_markup=main_menu_kb(lang),
    )

    # уведомляем админов, добавляем реквизиты
    extra = f"Банківська картка клієнта (UAH): {card}"
    await notify_admins_new_order(
        user_tg_id=user_tg_id,
        user_username=user_username,
        order_id=order_id,
        direction_code=direction_code,
        amount=amount,
        base=base,
        quote=quote,
        bot=msg.bot,
        extra=extra,
    )



@router.message(OrderFSM.input_iban)
async def input_iban(msg: Message, state: FSMContext):
    """Отримуємо IBAN клієнта (USDT -> IBAN)."""
    lang = user_lang(msg.from_user.id)
    iban_text = (msg.text or "").strip()

    # Дуже м'яка перевірка — просто щоб не було порожнього тексту
    if not iban_text or len(iban_text) < 10:
        if lang == "uk":
            return await msg.answer(
                "IBAN виглядає некоректним. Будь ласка, надішліть повні реквізити IBAN, як у прикладі від менеджера."
            )
        else:
            return await msg.answer("IBAN looks invalid. Please send full IBAN details.")

    data = await state.get_data()
    direction_code = data.get("direction_code")
    amount = data.get("amount")
    base = data.get("base")
    quote = data.get("quote")

    order = await create_order_record(
        msg=msg,
        direction_code=direction_code,
        amount=amount,
        base=base,
        quote=quote,
        payment_details={"payout_card_masked": iban_text},
    )
    if not order:
        return
    order_id = order["id"]
    user_tg_id = msg.from_user.id
    user_username = msg.from_user.username

    # очищаємо стан
    await state.clear()
    await msg.answer(
        t(lang, "order.created", order_id=order_id),
        reply_markup=main_menu_kb(lang),
    )

    # сповіщаємо адмінів, додаємо IBAN в текст
    extra = f"IBAN клієнта:\n{iban_text}"
    await notify_admins_new_order(
        user_tg_id=user_tg_id,
        user_username=user_username,
        order_id=order_id,
        direction_code=direction_code,
        amount=amount,
        base=base,
        quote=quote,
        bot=msg.bot,
        extra=extra,
    )




@router.callback_query(F.data.startswith("cl_reply:"))
async def cb_client_reply(call: CallbackQuery, state: FSMContext):
    """Кнопка клієнта 'Відповісти менеджеру' під повідомленням від адміна."""
    lang = user_lang(call.from_user.id)
    try:
        order_id = int(call.data.split(":", 1)[1])
    except (ValueError, IndexError):
        await call.answer("Некоректний ID заявки", show_alert=True)
        return

    await state.set_state(ClientReplyFSM.waiting_for_text)
    await state.update_data(order_id=order_id)

    if lang == "uk":
        text_prompt = (
            f"Напишіть повідомлення менеджеру по заявці #{order_id}.\\n\\n"
            "Ваше повідомлення буде надіслане оператору одразу після вводу."
        )
    else:
        text_prompt = (
            f"Type a message to manager for order #{order_id}.\\n\\n"
            "Your message will be sent to the operator right after you send it."
        )

    await call.message.answer(text_prompt)
    await call.answer()


@router.message(ClientReplyFSM.waiting_for_text)
async def client_reply_text(msg: Message, state: FSMContext):
    """Клієнт пише відповідь менеджеру — пересилаємо її адмінам з кнопкою 'Відповісти'."""
    lang = user_lang(msg.from_user.id)
    data = await state.get_data()
    order_id = data.get("order_id")

    if not order_id:
        await state.clear()
        if lang == "uk":
            return await msg.answer("Не знайдено заявку для відповіді.")
        else:
            return await msg.answer("Order for reply not found.")

    text_to_manager = msg.text or ""
    if not text_to_manager.strip():
        if lang == "uk":
            return await msg.answer("Повідомлення порожнє. Напишіть текст для менеджера.")
        else:
            return await msg.answer("Message is empty. Please type something for the manager.")

    # формуємо текст для адмінів
    header = f"💬 Повідомлення від клієнта по заявці #{order_id}"
    header += f"\nКлієнт: {msg.from_user.id}"
    if msg.from_user.username:
        header += f" (@{msg.from_user.username})"

    full_text = header + "\n\n" + text_to_manager

    from core.config import settings
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="💬 Відповісти",
                    callback_data=f"pay_msg:{order_id}",
                )
            ]
        ]
    )

    async def send_to_admin(chat_id: int):
        if not chat_id:
            return
        try:
            await msg.bot.send_message(chat_id=chat_id, text=full_text, reply_markup=keyboard)
        except Exception:
            pass

    # основний адмін-чат
    if settings.ADMIN_CHAT_ID:
        await send_to_admin(settings.ADMIN_CHAT_ID)

    # особисті адміни
    if settings.ADMIN_IDS:
        try:
            ids = {int(x) for x in settings.ADMIN_IDS.split(",") if x.strip()}
        except Exception:
            ids = set()
        for admin_id in ids:
            await send_to_admin(admin_id)

    await state.clear()
    if lang == "uk":
        await msg.answer("Повідомлення надіслано менеджеру.")
    else:
        await msg.answer("Your message has been sent to the manager.")


# =======================
# Подтверждение оплаты от клиента (чек / скрин / TX hash)
# =======================

@router.message(F.photo | F.document | F.text.regexp(r"(?i)(txid|hash|хеш|чек|оплатил|оплата)"))
async def handle_payment_proof(msg: Message):
    """Ловим чеки/скрины/хеши транзакций от клиентов и шлём уведомление админам."""
    lang = user_lang(msg.from_user.id)

    order = None
    try:
        latest = await backend_client.list_orders(msg.from_user.id, limit=1)
        items = latest.get("items", [])
        order = items[0] if items else None
    except Exception:
        order = None

    order_id = order.get("id") if order else None

    # попытаемся записать факт оплаты и вложение в backend
    if order_id:
        try:
            if msg.photo:
                storage_url = msg.photo[-1].file_id
                mime_type = "image/jpeg"
            elif msg.document:
                storage_url = msg.document.file_id
                mime_type = msg.document.mime_type
            else:
                storage_url = msg.text or "payment-confirmation"
                mime_type = "text/plain"

            await backend_client.add_attachment(
                telegram_id=msg.from_user.id,
                order_id=order_id,
                type_="payment_proof",
                storage_url=storage_url,
                mime_type=mime_type,
            )
            await backend_client.mark_paid(
                telegram_id=msg.from_user.id,
                order_id=order_id,
                comment=msg.caption if msg.caption else msg.text,
            )
        except Exception:
            pass

    # формируем общий заголовок для админа
    header = f"📩 Клієнт {msg.from_user.id}"
    if msg.from_user.username:
        header += f" (@{msg.from_user.username})"
    if order_id:
        header += f" надіслав підтвердження оплати по заявці #{order_id}"
    else:
        header += " надіслав підтвердження оплати (заявка не знайдена в БД)."

    # формируем инлайн-кнопки для админа, если есть ID заявки
    keyboard = None
    if order_id:
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="✅ Оплата отримана",
                        callback_data=f"pay_ok:{order_id}",
                    ),
                    InlineKeyboardButton(
                        text="❌ Оплата не отримана",
                        callback_data=f"pay_no:{order_id}",
                    ),
                ],
                [
                    InlineKeyboardButton(
                        text="💬 Відповісти",
                        callback_data=f"pay_msg:{order_id}",
                    )
                ],
            ]
        )

    # функция отправки в один чат
    async def send_to_admin(chat_id: int):
        if not chat_id:
            return
        try:
            if msg.photo:
                file_id = msg.photo[-1].file_id
                caption = msg.caption or ""
                full_caption = header
                if caption:
                    full_caption += "\n\n" + caption
                await msg.bot.send_photo(
                    chat_id=chat_id,
                    photo=file_id,
                    caption=full_caption,
                    reply_markup=keyboard,
                )
            elif msg.document:
                file_id = msg.document.file_id
                caption = msg.caption or msg.document.file_name or ""
                full_caption = header
                if caption:
                    full_caption += "\n\n" + caption
                await msg.bot.send_document(
                    chat_id=chat_id,
                    document=file_id,
                    caption=full_caption,
                    reply_markup=keyboard,
                )
            else:
                text = msg.text or ""
                full_text = header + "\n\n" + text
                await msg.bot.send_message(
                    chat_id=chat_id,
                    text=full_text,
                    reply_markup=keyboard,
                )
        except Exception:
            pass

    # отправляем в основной админ-чат
    if settings.ADMIN_CHAT_ID:
        await send_to_admin(settings.ADMIN_CHAT_ID)

    # и продублируем всем личным админам
    if settings.ADMIN_IDS:
        try:
            ids = {int(x) for x in settings.ADMIN_IDS.split(",") if x.strip()}
        except Exception:
            ids = set()
        for admin_id in ids:
            await send_to_admin(admin_id)

    # отвечаем клиенту
    if lang == "uk":
        text = "Ваше підтвердження оплати надіслано оператору. Очікуйте, найближчим часом з вами зв’яжуться."
    else:
        text = "Your payment confirmation has been sent to the operator. Please wait, we will contact you soon."
    await msg.answer(text)

# =======================
# Телефон клієнта після підтвердження / непідтвердження оплати
# =======================

@router.message(F.text.regexp(r"^\+?\d[\d\s\-\(\)]{7,}$"))
async def handle_client_phone(msg: Message):
    """Ловим номер телефону клієнта та шлемо його адмінам з прив'язкою до останньої заявки."""
    lang = user_lang(msg.from_user.id)
    phone = (msg.text or "").strip()

    order = None
    try:
        latest = await backend_client.list_orders(msg.from_user.id, limit=1)
        order = latest.get("items", [None])[0] if latest else None
    except Exception:
        order = None

    order_id = order.get("id") if order else None
    direction_code = order.get("direction") if order else None
    amount = float(order.get("amount_from")) if order and order.get("amount_from") is not None else None
    base = order.get("base_currency") if order else None
    quote = order.get("quote_currency") if order else None

    # людське відображення напрямку
    direction_human = {
        "CARD_UAH_TO_CRYPTO_USDT": "Карта (UAH) → Crypto (USDT)",
        "CRYPTO_USDT_TO_CARD_UAH": "Crypto (USDT) → Карта (UAH)",
        "CASH_UAH_TO_CRYPTO_USDT": "Готівка (UAH) → Crypto (USDT)",
        "CRYPTO_USDT_TO_CASH_UAH": "Crypto (USDT) → Готівка (UAH)",
        "IBAN_UAH_TO_CRYPTO_USDT": "IBAN (UAH) → Crypto (USDT)",
        "CRYPTO_USDT_TO_IBAN_UAH": "Crypto (USDT) → IBAN (UAH)",
}.get(direction_code, direction_code or "-")

    # формуємо текст для адміна
    header = f"📞 Клієнт {msg.from_user.id}"
    if msg.from_user.username:
        header += f" (@{msg.from_user.username})"
    header += " надіслав номер телефону"

    if order_id:
        header += f" по заявці #{order_id}"

    body_lines = [header, f"Номер телефону: {phone}"]
    if direction_human:
        body_lines.append(f"Напрямок: {direction_human}")
    if amount is not None and base:
        body_lines.append(f"Сума: {amount} {base}")

    full_text = "\n".join(body_lines)

    # функція відіслати в один чат
    async def send_phone_to_admin(chat_id: int):
        if not chat_id:
            return
        try:
            from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

            if order_id:
                keyboard = InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(
                                text="💬 Відповісти",
                                callback_data=f"pay_msg:{order_id}",
                            )
                        ]
                    ]
                )
            else:
                keyboard = None

            await msg.bot.send_message(chat_id=chat_id, text=full_text, reply_markup=keyboard)
        except Exception:
            pass

    # основний адмін-чат
    if settings.ADMIN_CHAT_ID:
        await send_phone_to_admin(settings.ADMIN_CHAT_ID)

    # дублікат усім особистим адмінам
    if settings.ADMIN_IDS:
        try:
            ids = {int(x) for x in settings.ADMIN_IDS.split(",") if x.strip()}
        except Exception:
            ids = set()
        for admin_id in ids:
            await send_phone_to_admin(admin_id)

    # відповідь клієнту
    if lang == "uk":
        reply_text = "Дякуємо! Оператор отримає ваш номер телефону та невдовзі зв’яжеться з вами."
    else:
        reply_text = "Thank you! The operator will receive your phone number and contact you soon."

    await msg.answer(reply_text)






# =======================
# Мої заявки / My orders
# =======================


@router.message(F.text == "/status")
@router.message(F.text.in_(["Мої заявки", "My orders"]))
async def my_orders(msg: Message):
    lang = user_lang(msg.from_user.id)

    try:
        data = await backend_client.list_orders(msg.from_user.id, limit=10)
        rows = data.get("items", [])
    except Exception:
        rows = []

    if not rows:
        return await msg.answer(t(lang, "orders.empty"))

    direction_map_uk = {
        "CARD_UAH_TO_CRYPTO_USDT": "Карта → Crypto (USDT)",
        "CRYPTO_USDT_TO_CARD_UAH": "Crypto (USDT) → Карта",
        "CASH_UAH_TO_CRYPTO_USDT": "Готівка → Crypto (USDT)",
        "CRYPTO_USDT_TO_CASH_UAH": "Crypto (USDT) → Готівка",
        "IBAN_UAH_TO_CRYPTO_USDT": "IBAN → Crypto (USDT)",
        "CRYPTO_USDT_TO_IBAN_UAH": "Crypto (USDT) → IBAN",
    }
    direction_map_en = {
        "CARD_UAH_TO_CRYPTO_USDT": "Card → Crypto (USDT)",
        "CRYPTO_USDT_TO_CARD_UAH": "Crypto (USDT) → Card",
        "CASH_UAH_TO_CRYPTO_USDT": "Cash → Crypto (USDT)",
        "CRYPTO_USDT_TO_CASH_UAH": "Crypto (USDT) → Cash",
        "IBAN_UAH_TO_CRYPTO_USDT": "IBAN → Crypto (USDT)",
        "CRYPTO_USDT_TO_IBAN_UAH": "Crypto (USDT) → IBAN",
    }

    lines = []
    for o in rows:
        direction_human = (
            direction_map_uk.get(o["direction"], o["direction"])
            if lang == "uk"
            else direction_map_en.get(o["direction"], o["direction"])
        )
        line = t(
            lang,
            "orders.item",
            id=o["id"],
            direction=direction_human,
            status=o["status"],
            amount=float(o.get("amount_from") or 0),
            base=o["base_currency"],
        )
        lines.append(line)

    await msg.answer("\n".join(lines))
