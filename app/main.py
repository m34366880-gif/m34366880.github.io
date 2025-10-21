from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates

from .config import settings
from .database import Base, engine
from .routers.public import router as public_router
from .routers.admin import router as admin_router
from .routers.telegram_api import router as telegram_router


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_title)

    # Static files
    app.mount("/static", StaticFiles(directory=settings.static_dir), name="static")

    # CORS (relaxed, can be tightened for production)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Routers
    app.include_router(public_router)
    app.include_router(admin_router)
    app.include_router(telegram_router)

    @app.on_event("startup")
    def on_startup():
        Base.metadata.create_all(bind=engine)

    @app.get("/healthz")
    def healthz():
        return {"ok": True}

    return app


app = create_app()
