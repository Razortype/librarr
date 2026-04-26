from __future__ import annotations

import importlib.metadata

from fastapi import FastAPI

from app.api.v1 import system
from app.core.logging import configure_logging


def create_app() -> FastAPI:
    configure_logging()

    application = FastAPI(title="librarr", version=importlib.metadata.version("librarr"))
    application.include_router(system.router, prefix="/api/v1/system")

    return application


app = create_app()
