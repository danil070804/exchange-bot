from fastapi import FastAPI
from api.routers import admin, orders, users, webhooks
from core.config import settings
from core.db import init_engine, Base
from sqlalchemy import text

app = FastAPI(title="Exchange Admin API")

# Init DB and create tables on startup
engine = init_engine(settings.DB_DSN)
Base.metadata.create_all(bind=engine)

app.include_router(admin.router, prefix="/admin")
app.include_router(orders.router, prefix="/orders")
app.include_router(users.router, prefix="/users")
app.include_router(webhooks.router, prefix="/webhooks")

@app.get("/health")
def health():
    return {"status": "ok", "tz": settings.TIMEZONE}
