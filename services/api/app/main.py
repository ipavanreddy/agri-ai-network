import logging
import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app import system
from app.advisory.router import router as ai_router
from app.analytics.router import router as officer_router
from app.config import SAMPLE_DIR, settings
from app.farms.router import router as farms_router
from app.interop.router import router as interop_router
from app.localization.router import router as localization_router

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(_: FastAPI):
    system.seed_demo_data()
    # warm the integration probes in the background so the first /api/system/status call is fast
    threading.Thread(target=system.probe_integrations, daemon=True).start()
    yield


app = FastAPI(title=settings.project_name, lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",") if o.strip()],
    allow_methods=["*"],
    allow_headers=["*"],
)
for r in (system.router, farms_router, ai_router, localization_router, interop_router, officer_router):
    app.include_router(r)
app.mount("/samples", StaticFiles(directory=SAMPLE_DIR / "images"), name="samples")


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "project": settings.project_name, "model": settings.gemini_model,
            "gemini": "live" if settings.gemini_enabled else "demo"}
