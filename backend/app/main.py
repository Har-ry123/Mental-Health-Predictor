from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .db import create_db_and_tables
from .routers.chat import router as chat_router
from .routers.mood import router as mood_router
from .routers.journal import router as journal_router
from .routers.resources import router as resources_router
from .routers.eeg import router as eeg_router


def create_app() -> FastAPI:
    app = FastAPI(title="Mindful Companion", version="0.1.0")

    # CORS for local dev and simple hosting
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # API Routers under /api
    app.include_router(chat_router, prefix="/api")
    app.include_router(mood_router, prefix="/api")
    app.include_router(journal_router, prefix="/api")
    app.include_router(resources_router, prefix="/api")
    app.include_router(eeg_router, prefix="/api")

    # Static frontend
    static_dir = Path(__file__).resolve().parent.parent / "frontend"
    if not static_dir.exists():
        static_dir.mkdir(parents=True, exist_ok=True)
    app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")

    @app.on_event("startup")
    def on_startup() -> None:  # pragma: no cover - side effect
        create_db_and_tables()

    return app


app = create_app()


