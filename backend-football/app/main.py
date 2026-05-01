from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import get_settings
from app.db.session import SessionLocal
from app.services.dev_seed import seed_dev_news_feed


@asynccontextmanager
async def lifespan(_: FastAPI):
    settings = get_settings()
    Path(settings.local_storage_path).mkdir(parents=True, exist_ok=True)
    if settings.app_env != "prod":
        with SessionLocal() as session:
            seed_dev_news_feed(session)
    yield


def create_application() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Football TG Publishing Tool API",
        version="0.1.0",
        debug=settings.app_debug,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router)
    return app


app = create_application()
