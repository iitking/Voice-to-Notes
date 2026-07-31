from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional
from app.database.session import get_db
from app.models.entities import AudioFile, ProcessingJob, Transcript
from app.schemas.audio import AudioUploadResponse, JobStatusResponse, TranscriptResponse
from app.services.audio_service import audio_service, AudioServiceError
from app.workers.pipeline import run_audio_pipeline

router = APIRouter(prefix="/api/v1", tags=["audio"])

@router.post("/audio", response_model=AudioUploadResponse)
async def upload_audio(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    language: Optional[str] = Form("auto"),
    db: Session = Depends(get_db),
):
    """Uploads an audio file, persists metadata, and starts transcription & note generation."""
    try:
        content = await file.read()
        storage_filename, storage_path, file_size = audio_service.save_upload(
            original_filename=file.filename or "recording.wav",
            file_bytes=content,
        )

        audio_record = AudioFile(
            original_filename=file.filename or storage_filename,
            storage_path=storage_path,
            mime_type=file.content_type,
            file_size_bytes=file_size,
        )
        db.add(audio_record)
        db.flush()

        job_record = ProcessingJob(
            audio_file_id=audio_record.id,
            status="queued",
            stage_message="File uploaded. Queued for validation and processing.",
        )
        db.add(job_record)
        db.commit()
        db.refresh(job_record)

        # Trigger background processing pipeline
        background_tasks.add_task(
            run_audio_pipeline,
            job_id=job_record.id,
            audio_file_id=audio_record.id,
            language=language,
        )

        return AudioUploadResponse(
            audio_file_id=audio_record.id,
            job_id=job_record.id,
            filename=audio_record.original_filename,
            status=job_record.status,
            message="Audio uploaded successfully. Processing started.",
        )

    except AudioServiceError as e:
        raise HTTPException(status_code=400, detail={"code": e.code, "message": e.message})
    except Exception as e:
        raise HTTPException(status_code=500, detail={"code": "UPLOAD_FAILED", "message": str(e)})

@router.get("/jobs/{job_id}", response_model=JobStatusResponse)
def get_job_status(job_id: str, db: Session = Depends(get_db)):
    """Reads processing job status and associated IDs if completed."""
    job = db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    transcript_id = None
    note_id = None

    if job.status == "completed":
        transcript = db.query(Transcript).filter(Transcript.audio_file_id == job.audio_file_id).first()
        if transcript:
            transcript_id = transcript.id
            if transcript.note:
                note_id = transcript.note.id

    return JobStatusResponse(
        id=job.id,
        audio_file_id=job.audio_file_id,
        status=job.status,
        stage_message=job.stage_message,
        error_code=job.error_code,
        error_message=job.error_message,
        created_at=job.created_at,
        updated_at=job.updated_at,
        completed_at=job.completed_at,
        transcript_id=transcript_id,
        note_id=note_id,
    )

@router.get("/transcripts/{transcript_id}", response_model=TranscriptResponse)
def get_transcript(transcript_id: str, db: Session = Depends(get_db)):
    """Retrieves full transcript and segment timestamps."""
    transcript = db.query(Transcript).filter(Transcript.id == transcript_id).first()
    if not transcript:
        raise HTTPException(status_code=404, detail="Transcript not found")
    return transcript
