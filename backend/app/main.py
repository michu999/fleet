"""
Fleet Management SaaS - Backend Application
FastAPI entry point with CORS, middleware, and router configuration.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Startup and shutdown events go here.
    """
    # Startup
    yield
    # Shutdown


app = FastAPI(
    title="Fleet Management API",
    description="B2B SaaS for vehicle fleet management",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

# CORS configuration for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint.
    Returns OK status for load balancers and monitoring.
    """
    return {"status": "ok", "environment": settings.ENVIRONMENT}


# Router includes placeholder
# Uncomment as modules are implemented:
# from app.modules.auth.router import router as auth_router
# from app.modules.fleet.router import router as fleet_router
# from app.modules.orders.router import router as orders_router
# from app.modules.reports.router import router as reports_router
# from app.modules.notifications.router import router as notifications_router
#
# app.include_router(auth_router, prefix="/api/v1/auth", tags=["Auth"])
# app.include_router(fleet_router, prefix="/api/v1/fleet", tags=["Fleet"])
# app.include_router(orders_router, prefix="/api/v1/orders", tags=["Orders"])
# app.include_router(reports_router, prefix="/api/v1/reports", tags=["Reports"])
# app.include_router(notifications_router, prefix="/api/v1/notifications", tags=["Notifications"])

