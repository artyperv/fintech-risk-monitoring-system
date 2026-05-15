from fastapi import FastAPI

from app.api.main import api_router
from app.core.config import settings

app = FastAPI(
    title="Fintech Risk Monitoring API",
    openapi_url=f"{settings.API_PREFIX}/openapi.json" if settings.DEBUG else None,
    docs_url=f"{settings.API_PREFIX}/docs" if settings.DEBUG else None,
    redoc_url=f"{settings.API_PREFIX}/redoc" if settings.DEBUG else None,
)

app.include_router(api_router, prefix=settings.API_PREFIX)


@app.get("/health", tags=["health"])
async def health() -> dict[str, str]:
    return {"status": "ok"}
