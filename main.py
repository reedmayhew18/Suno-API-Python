#!/usr/bin/env python3
"""
Entry point for the Python version of Suno-API.
Sets up FastAPI application, middleware, routers, and background services.
"""
import uvicorn
from fastapi import FastAPI

from app.config import settings
from app.logger import init_logger
from app.database import init_db, close_db
from app.routers.ping import router as ping_router
from app.routers.suno import router as suno_router
from app.routers.chat import router as chat_router
from app.services.account import start_account_keepalive
from app.services.tasks import start_task_worker


def create_app() -> FastAPI:
    # Initialize logger
    init_logger()

    app = FastAPI(
        title="Suno API",
        version=settings.version,
        openapi_url="/swagger.json",
        docs_url="/docs",
    )

    # Include routers
    app.include_router(ping_router)
    app.include_router(suno_router, prefix="/suno")
    app.include_router(chat_router, prefix="/v1/chat")

    # Startup and shutdown events
    # Middleware: CORS
    from fastapi.middleware.cors import CORSMiddleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    # Middleware: Request ID
    from uuid import uuid4
    @app.middleware("http")
    async def add_request_id(request, call_next):
        rid = uuid4().hex
        request.state.request_id = rid
        response = await call_next(request)
        response.headers["X-Request-ID"] = rid
        return response

    @app.on_event("startup")
    async def on_startup():
        init_db()
        # Load templates
        from app.utils.templates import load_templates
        load_templates()
        # Start background services
        start_account_keepalive()
        start_task_worker()

    @app.on_event("shutdown")
    async def on_shutdown():
        close_db()

    return app


app = create_app()

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )