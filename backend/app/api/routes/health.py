from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database.session import get_db
from app.services.notes_service import notes_service
from app.services.transcription_service import transcription_service

router = APIRouter()

@router.get("/health")
def health_check(db: Session = Depends(get_db)):
    # 1. DB check
    db_status = "ok"
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"error: {str(e)}"

    # 2. Ollama check
    ollama_info = notes_service.check_health()

    # 3. Whisper check
    whisper_info = {
        "model": transcription_service.model_name,
        "device": transcription_service.device,
        "compute_type": transcription_service.compute_type,
    }

    is_ready = db_status == "ok" and ollama_info.get("status") == "ok"

    return {
        "status": "healthy" if is_ready else "degraded",
        "database": db_status,
        "ollama": ollama_info,
        "whisper": whisper_info,
    }
