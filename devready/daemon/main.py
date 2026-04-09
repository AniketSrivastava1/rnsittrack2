"""Main FastAPI application for DevReady Daemon."""
from __future__ import annotations

import asyncio
import logging
import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from devready.daemon.api import analytics, drift, fixes, scan, snapshots, system, team, visualization
from devready.daemon.api.websocket import router as ws_router
from devready.lens.router import router as lens_router
from devready.daemon.config import load_config
from devready.daemon.database import close_engine, init_db
from devready.daemon.logging_config import setup_logging
from devready.daemon.middleware.rate_limit import RateLimitMiddleware
from devready.daemon.middleware.security import SecurityMiddleware
from devready.daemon.services.metrics_collector import MetricsCollector

logger = logging.getLogger(__name__)

_metrics = MetricsCollector()


async def _cleanup_loop(db_path: str, retention_days: int) -> None:
    """Run snapshot cleanup once a day."""
    while True:
        await asyncio.sleep(86400)  # 24 hours
        try:
            from devready.daemon.database import get_engine
            from sqlalchemy.ext.asyncio import AsyncSession
            from devready.daemon.services.snapshot_service import SnapshotService
            async with AsyncSession(get_engine(db_path), expire_on_commit=False) as session:
                deleted = await SnapshotService().cleanup_old_snapshots(session, retention_days)
                logger.info("Cleanup: removed %d snapshots older than %d days", deleted, retention_days)
        except Exception as exc:
            logger.warning("Snapshot cleanup failed: %s", exc)


def create_app(config_path: str | None = None) -> FastAPI:
    cfg = load_config(config_path)

    setup_logging(
        cfg.logging.file,
        level=cfg.logging.level,
        max_size_mb=cfg.logging.max_size_mb,
        backup_count=cfg.logging.backup_count,
    )

    app = FastAPI(
        title="DevReady Daemon API",
        version="1.0.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
    )

    # CORS - localhost only
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost", "http://127.0.0.1"],
        allow_origin_regex=r"http://(localhost|127\.0\.0\.1)(:\d+)?",
        allow_methods=["GET", "POST", "DELETE"],
        allow_headers=["*"],
    )
    app.add_middleware(RateLimitMiddleware, max_requests=cfg.performance.rate_limit_per_minute)
    app.add_middleware(SecurityMiddleware)

    # Inject metrics collector into system and scan modules
    system._metrics_collector = _metrics
    scan._metrics_collector = _metrics

    # Routers — analytics/lens must be registered before snapshots to avoid
    # /snapshots/history being shadowed by /snapshots/{snapshot_id}
    app.include_router(scan.router)
    app.include_router(analytics.router)
    app.include_router(lens_router)
    app.include_router(snapshots.router)
    app.include_router(drift.router)
    app.include_router(fixes.router)
    app.include_router(system.router)
    app.include_router(team.router)
    app.include_router(visualization.router)
    app.include_router(ws_router)

    # Request logging middleware
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        start = time.time()
        response = await call_next(request)
        duration = time.time() - start
        logger.info("%s %s %s %.3f", request.method, request.url.path, response.status_code, duration)
        return response

    # Exception handlers
    @app.exception_handler(ValidationError)
    async def validation_handler(request: Request, exc: ValidationError):
        return JSONResponse(
            status_code=422,
            content={"error_code": "VALIDATION_ERROR", "message": "Invalid request data", "details": exc.errors(), "api_version": "v1"},
        )

    @app.exception_handler(Exception)
    async def generic_handler(request: Request, exc: Exception):
        logger.error("Unhandled exception: %s", exc, exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error_code": "INTERNAL_ERROR", "message": "An internal error occurred", "details": {}, "api_version": "v1"},
        )

    @app.exception_handler(404)
    async def not_found_handler(request: Request, exc):
        if hasattr(exc, "detail") and exc.detail:
            if isinstance(exc.detail, dict):
                return JSONResponse(status_code=404, content=exc.detail)
            return JSONResponse(status_code=404, content={"detail": exc.detail})
        return JSONResponse(
            status_code=404,
            content={"error_code": "NOT_FOUND", "message": f"Endpoint {request.url.path} not found", "details": {}, "api_version": "v1"},
        )

    @app.on_event("startup")
    async def startup():
        await init_db(cfg.database.path)
        _metrics.start()
        asyncio.create_task(_cleanup_loop(cfg.database.path, cfg.database.retention_days))
        logger.info("DevReady Daemon started on %s:%d", cfg.daemon.host, cfg.daemon.port)

    @app.on_event("shutdown")
    async def shutdown():
        await _metrics.stop()
        await close_engine()
        logger.info("DevReady Daemon shut down")

    return app


app = create_app()
