import hashlib
import hmac
import json
import time
from dataclasses import dataclass
from urllib.parse import parse_qsl


class TelegramInitDataError(ValueError):
    pass


@dataclass(slots=True)
class TelegramInitData:
    tg_id: int
    username: str | None
    lang: str | None
    auth_date: int
    start_param: str | None
    raw_user: dict


def validate_init_data(init_data: str, bot_token: str, max_age_seconds: int = 86400) -> TelegramInitData:
    pairs = dict(parse_qsl(init_data, keep_blank_values=True))
    received_hash = pairs.pop("hash", None)
    if not received_hash:
        raise TelegramInitDataError("Telegram initData hash is missing")

    data_check_string = "\n".join(f"{key}={value}" for key, value in sorted(pairs.items()))
    secret_key = hmac.new(b"WebAppData", bot_token.encode("utf-8"), hashlib.sha256).digest()
    calculated_hash = hmac.new(secret_key, data_check_string.encode("utf-8"), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(calculated_hash, received_hash):
        raise TelegramInitDataError("Telegram initData signature is invalid")

    try:
        auth_date = int(pairs["auth_date"])
    except (KeyError, ValueError) as exc:
        raise TelegramInitDataError("Telegram auth_date is invalid") from exc

    now = int(time.time())
    if auth_date > now + 30:
        raise TelegramInitDataError("Telegram initData auth_date is in the future")
    if now - auth_date > max_age_seconds:
        raise TelegramInitDataError("Telegram initData has expired")

    raw_user = json.loads(pairs.get("user", "{}"))
    tg_id = raw_user.get("id")
    if not tg_id:
        raise TelegramInitDataError("Telegram user payload is missing")

    return TelegramInitData(
        tg_id=int(tg_id),
        username=raw_user.get("username"),
        lang=raw_user.get("language_code"),
        auth_date=auth_date,
        start_param=pairs.get("start_param"),
        raw_user=raw_user,
    )