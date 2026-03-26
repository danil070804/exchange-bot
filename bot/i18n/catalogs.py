from __future__ import annotations

LANGS = {
    "uk": "Українська",
    "en": "English",
}

CATALOG = {
    "uk": {
        "cmd_start.welcome": "Вітаю! Я бот для обміну між банківською карткою та криптовалютою. Оберіть дію нижче.",
        "menu.direction.card_to_crypto": "Карта → Crypto (USDT)",
        "menu.direction.crypto_to_card": "Crypto (USDT) → Карта",
        "menu.direction.cash_to_crypto": "Готівка → Crypto (USDT)",
        "menu.direction.crypto_to_cash": "Crypto (USDT) → Готівка",
        "menu.direction.iban_to_crypto": "IBAN → Crypto (USDT)",
        "menu.direction.crypto_to_iban": "Crypto (USDT) → IBAN",
        "menu.my_orders": "Мої заявки",
        "menu.lang": "Мова",

        "order.choose_direction": "Оберіть напрямок:",
        "order.input_amount": "Вкажіть суму (наприклад: 15000 або 100):",
        "order.limit_exceeded": "Ліміт перевищено: {reason}",
        "order.created": "Заявку #{order_id} створено. Адміністратор напише вам у цьому чаті з актуальним курсом та реквізитами.",

        "orders.none": "Ви ще не створювали заявки.",
        "orders.empty": "Заявок немає.",
        "orders.item": "#{id} • {direction} • {status} • сума {amount} {base}",

        "lang.prompt": "Оберіть мову інтерфейсу:",
        "lang.set": "Мову змінено на: {lang_name}",
    },

    "en": {
        "cmd_start.welcome": "Hi! I am a card ↔ crypto exchange bot. Choose an action below.",
        "menu.direction.card_to_crypto": "Card → Crypto (USDT)",
        "menu.direction.crypto_to_card": "Crypto (USDT) → Card",
        "menu.direction.cash_to_crypto": "Cash → Crypto (USDT)",
        "menu.direction.crypto_to_cash": "Crypto (USDT) → Cash",
        "menu.direction.iban_to_crypto": "IBAN → Crypto (USDT)",
        "menu.direction.crypto_to_iban": "Crypto (USDT) → IBAN",
        "menu.my_orders": "My orders",
        "menu.lang": "Language",

        "order.choose_direction": "Choose direction:",
        "order.input_amount": "Enter amount (e.g. 15000 or 100):",
        "order.limit_exceeded": "Limit exceeded: {reason}",
        "order.created": "Order #{order_id} created. Admin will contact you in this chat with actual rate and payment details.",

        "orders.none": "You haven’t created any orders yet.",
        "orders.empty": "No orders found.",
        "orders.item": "#{id} • {direction} • {status} • amount {amount} {base}",

        "lang.prompt": "Choose interface language:",
        "lang.set": "Language switched to: {lang_name}",
    },
}


def t(lang: str, key: str, **kwargs) -> str:
    lang = lang if lang in CATALOG else "uk"
    msg = CATALOG.get(lang, {}).get(key, key)
    try:
        return msg.format(**kwargs)
    except Exception:
        return msg


def safe_lang(lang: str | None) -> str:
    return lang if lang in LANGS else "uk"
