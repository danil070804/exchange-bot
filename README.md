# Telegram Card ⇄ Crypto Exchange Bot (UA/EN) — v2

Этот бот сделан под заказ как P2P-обменник:
- направление 1: КАРТА (UAH) → CRYPTO (USDT)
- направление 2: CRYPTO (USDT) → КАРТА (UAH)

Ключевые фичи:
- Мульти-язык: Украинский / English (выбор через /lang).
- Клиент создаёт заявку через кнопки (без ввода команд).
- Заявка сразу улетает админам.
- Админ вручную отвечает клиенту по заявке (курс, карта/кошелёк).
- KYC / верификация полностью убраны из UX.
- Простая админка в боте: /admin
  - новые заявки,
  - все заявки,
  - управление рекомендованным курсом /setrate.

## Быстрый старт (обновлено: backend + PostgreSQL)

1. Установи зависимости:

    pip install -r requirements.txt

2. Скопируй `.env.example` в `.env` и заполни:
   - TG_TOKEN — токен Telegram-бота
   - BACKEND_API_URL — адрес FastAPI backend (по умолчанию http://localhost:8000)
   - BACKEND_BOT_TOKEN — сервисный токен, который бот передает в backend
   - ADMIN_API_TOKEN — токен для админских endpoint'ов
   - DATABASE_URL — DSN PostgreSQL (например `postgresql+psycopg2://exchange:exchange@localhost:5432/exchange`)
   - ADMIN_IDS / ADMIN_CHAT_ID — список админов для уведомлений
   - TIMEZONE — таймзона (по умолчанию Europe/Kyiv)

3. Запуск backend (dev):

    cd apps/backend
    uvicorn app.main:app --reload

4. Запуск бота:

    python -m bot.main

По умолчанию бот работает через backend API и не использует локальную SQLite.

## Railway / Docker

Используй `docker/docker-compose.yml` для локального стенда: Postgres, Redis, backend, bot.

### Миграции

- Создать миграцию: `cd apps/backend && alembic revision --autogenerate -m "change"`
- Применить: `cd apps/backend && alembic upgrade head`

### Railway deploy (monorepo)
- Backend сервис: Build context `.`; Dockerfile `docker/Dockerfile.backend`; Start команду не нужно менять (в Dockerfile запускаются миграции и uvicorn).
- Bot сервис: Build context `.`; Dockerfile `docker/Dockerfile.bot`; Start `python -m bot.main`.
- Переменные окружения (оба сервиса):
  - `DATABASE_URL` — из Railway Postgres.
  - `TG_TOKEN` — токен бота (нужен только боту).
  - `BACKEND_API_URL` — для бота: `http://backend:8000`.
  - `BACKEND_BOT_TOKEN` — сервисный токен (совпадает в боте и backend).
  - `ADMIN_API_TOKEN` — токен для админских endpoint'ов.
  - `TIMEZONE`, `REDIS_URL` (опционально).
- Healthcheck: `/api/v1/healthz` на порту 8000 (backend).
- Автоматическая загрузка переменных в Railway: `python scripts/push_env_to_railway.py --service backend --service bot` (нужны установленный `railway` CLI и заполненный локальный `.env`).
