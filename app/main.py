from __future__ import annotations

import importlib.metadata

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import app.models  # noqa: F401  # register all SQLAlchemy mappers at import time
from app.api.errors import register_error_handlers
from app.api.v1 import author as author_router
from app.api.v1 import book as book_router
from app.api.v1 import command as command_router
from app.api.v1 import integrations as integrations_router
from app.api.v1 import system
from app.core.config import settings
from app.core.logging import configure_logging


def create_app() -> FastAPI:
    configure_logging()

    application = FastAPI(title="librarr", version=importlib.metadata.version("librarr"))

    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    application.include_router(system.router, prefix="/api/v1/system")
    application.include_router(book_router.router, prefix="/api/v1/book", tags=["book"])
    application.include_router(author_router.router, prefix="/api/v1/author", tags=["author"])
    application.include_router(command_router.router, prefix="/api/v1/command", tags=["command"])
    application.include_router(
        integrations_router.router, prefix="/api/v1/integrations", tags=["integrations"]
    )

    register_error_handlers(application)

    return application


app = create_app()
