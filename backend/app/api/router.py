"""API router configuration."""
from fastapi import APIRouter
from app.api import stocks, watchlist, market_data, analysis, health, settings, reports, alerts

api_router = APIRouter()

api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(stocks.router, prefix="/stocks", tags=["stocks"])
api_router.include_router(watchlist.router, prefix="/watchlist", tags=["watchlist"])
api_router.include_router(market_data.router, prefix="/stocks", tags=["market_data"])
api_router.include_router(analysis.router, prefix="/stocks", tags=["analysis"])
api_router.include_router(reports.router, prefix="/stocks", tags=["reports"])
api_router.include_router(alerts.router, prefix="/alerts", tags=["alerts"])
api_router.include_router(settings.router, prefix="/settings", tags=["settings"])
