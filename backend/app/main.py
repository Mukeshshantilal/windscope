import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.accuracy import router as accuracy_router
from app.api.dashboard import router as dashboard_router
from app.api.data import router as data_router
from app.api.forecasts import router as forecasts_router
from app.api.generation import router as generation_router
from app.api.health import router as health_router
from app.core.config import get_settings
from app.db.session import init_db

logging.basicConfig(level=logging.INFO)
settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="WindScope API",
    description="UK wind generation forecast analytics for day-ahead electricity purchasing.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, prefix="/api", tags=["health"])
app.include_router(dashboard_router, prefix="/api", tags=["dashboard"])
app.include_router(generation_router, prefix="/api", tags=["generation"])
app.include_router(forecasts_router, prefix="/api", tags=["forecasts"])
app.include_router(accuracy_router, prefix="/api", tags=["accuracy"])
app.include_router(data_router, prefix="/api", tags=["data"])

_frontend = settings.frontend_dist_path()
if _frontend is not None:
    assets = _frontend / "assets"
    if assets.is_dir():
        app.mount("/assets", StaticFiles(directory=assets), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    def spa(full_path: str):
        candidate = _frontend / full_path
        if full_path and candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(_frontend / "index.html")
