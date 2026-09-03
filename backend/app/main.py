from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import get_settings
from app.core.db import Base, engine
from app.routers import artwork, catalog, episodes, health, publish, shows

settings = get_settings()

app = FastAPI(title=settings.APP_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    # Simple create_all for this exercise instead of Alembic migrations
    # -- noted as a scoping trade-off in the README.
    Base.metadata.create_all(bind=engine)
    if settings.STORAGE_BACKEND == "local":
        import os
        os.makedirs(settings.STORAGE_ROOT, exist_ok=True)
        app.mount("/static", StaticFiles(directory=settings.STORAGE_ROOT), name="static")


app.include_router(health.router)
app.include_router(shows.router)
app.include_router(episodes.router)
app.include_router(artwork.router)
app.include_router(publish.router)
app.include_router(catalog.router)
