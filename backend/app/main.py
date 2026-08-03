import os
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.database.session import Base, engine, SessionLocal
from app.models.entities import ProcessingJob
from app.api.routes import health, audio, notes

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

# Ensure audio storage folder exists
os.makedirs(settings.AUDIO_STORAGE_DIR, exist_ok=True)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler.
    1. Initializes database tables if not already created.
    2. Recovers interrupted in-flight jobs from prior crashes/restarts.
    """
    logger.info("Initializing database schema...")
    Base.metadata.create_all(bind=engine)

    # Startup recovery for interrupted background jobs
    db = SessionLocal()
    try:
        interrupted_jobs = db.query(ProcessingJob).filter(
            ProcessingJob.status.in_(["queued", "validating", "transcribing", "generating_notes"])
        ).all()
        if interrupted_jobs:
            logger.warning(
                f"Found {len(interrupted_jobs)} in-flight job(s) from prior session. "
                "Marking as failed (SERVER_INTERRUPTED)."
            )
            for job in interrupted_jobs:
                job.status = "failed"
                job.error_code = "SERVER_INTERRUPTED"
                job.error_message = "Background processing interrupted by backend server restart. Please re-submit."
                job.completed_at = datetime.now(timezone.utc)
            db.commit()
    except Exception as e:
        logger.error(f"Error checking dangling jobs on startup: {e}")
        db.rollback()
    finally:
        db.close()

    yield
    logger.info("Shutting down Voice to Notes backend.")

app = FastAPI(
    title=settings.APP_NAME,
    description=(
        "End-to-end local-first voice-to-notes AI powered by faster-whisper, Ollama, and PostgreSQL.\n\n"
        "🔒 Architecture Note: Designed specifically as a privacy-centric, single-user workstation tool. "
        "Audio and notes remain 100% on localhost with zero external telemetry or cloud dependencies. "
        "Does not implement multi-user RBAC. For remote exposure, place behind an authenticating reverse proxy."
    ),
    version="1.1.0",
    lifespan=lifespan,
)

# CORS configuration - dynamically loaded from configured settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routes
app.include_router(health.router)
app.include_router(audio.router)
app.include_router(notes.router)

@app.get("/")
def root():
    return {
        "name": settings.APP_NAME,
        "version": "1.1.0",
        "status": "online",
        "architecture": "single-user-local",
        "docs": "/docs",
        "health": "/health"
    }
