import os
from pathlib import Path

# Находим корень проекта (папка, где лежит .env, bot/, core/ и т.д.)
BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"

# Простой загрузчик .env (без сторонних библиотек)
if ENV_PATH.exists():
    with ENV_PATH.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            # пропускаем пустые строки и комментарии
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            # не затираем уже существующие переменные окружения
            os.environ.setdefault(key, value)


class Settings:
    TG_TOKEN: str = os.getenv("TG_TOKEN", "")
    MINI_APP_URL: str | None = os.getenv("MINI_APP_URL")
    # Prefer DATABASE_URL, keep DB_DSN for backward compatibility
    DB_DSN: str = os.getenv("DATABASE_URL") or os.getenv("DB_DSN", "sqlite:///./exchange.db")
    ADMIN_CHAT_ID: int | None = int(os.getenv("ADMIN_CHAT_ID")) if os.getenv("ADMIN_CHAT_ID") else None
    ADMIN_IDS: str | None = os.getenv("ADMIN_IDS")
    TIMEZONE: str = os.getenv("TIMEZONE", "Europe/Kyiv")

    # Backend API settings
    BACKEND_API_URL: str = os.getenv("BACKEND_API_URL", "http://localhost:8000")
    BACKEND_BOT_TOKEN: str | None = os.getenv("BACKEND_BOT_TOKEN")
    ADMIN_API_TOKEN: str | None = os.getenv("ADMIN_API_TOKEN")

    # Новые поля: реквизиты из .env
    CARD_NUMBER: str | None = os.getenv("CARD_NUMBER")
    USDT_TRC20_ADDRESS: str | None = os.getenv("USDT_TRC20_ADDRESS")


settings = Settings()
