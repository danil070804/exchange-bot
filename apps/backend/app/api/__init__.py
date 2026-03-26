from fastapi import APIRouter

from app.api.routes import auth, orders, admin, reference, rates, health

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth.router, tags=["auth"])
api_router.include_router(reference.router, tags=["reference"])
api_router.include_router(rates.router, tags=["rates"])
api_router.include_router(orders.router, tags=["orders"])
api_router.include_router(admin.router, tags=["admin"])
api_router.include_router(health.router, tags=["health"])
