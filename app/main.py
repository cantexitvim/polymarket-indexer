from fastapi import FastAPI

from app.api import router
from app.core.settings import settings

app = FastAPI(
    title="polymarket-indexer",
    docs_url="/docs" if settings.show_docs else None,
    redoc_url="/redoc" if settings.show_docs else None,
    openapi_url="/openapi.json" if settings.show_docs else None,
    debug=settings.debug,
)

app.include_router(router)
