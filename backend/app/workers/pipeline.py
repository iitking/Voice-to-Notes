import os
import logging
from datetime import datetime, timezone
from typing import Optional
from app.database.session import SessionLocal
from app.models.entities import ProcessingJob, AudioFile, Transcript, TranscriptSegment, Note, ActionItem
from app.services.audio_service import audio_service, AudioServiceError
from app.services.transcription_service import transcription_service, TranscriptionServiceError
from app.services.notes_service import notes_service, NotesServiceError

logger = logging.getLogger(__name__)

def run_audio_pipeline(job_id: str, audio_file_id: str, language: Optional[str] = None):
    """Executes the full voice-to-notes processing pipeline in the background."""
    db = SessionLocal()
    normalized_path = None
    try:
        job = db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
        audio = db.query(AudioFile).filter(AudioFile.id == audio_file_id).first()
        if not job or not audio:
            logger.error(f"Pipeline error: Job {job_id} or Audio {audio_file_id} not found.")
            return

        # 1. Validation & Preprocessing
        job.status = "validating"
        job.stage_message = "Inspecting and normalizing audio format..."
        db.commit()

        probe_info = audio_service.inspect_audio(audio.storage_path)
        audio.duration_seconds = probe_info["duration"]
        db.commit()

        normalized_path = audio_service.convert_to_wav16k(audio.storage_path)

        # 2. Local Transcription with faster-whisper
        job.status = "transcribing"
        job.stage_message = f"Transcribing audio with local faster-whisper ({transcription_service.model_name})..."
        db.commit()

        transcription_result = transcription_service.transcribe(
            audio_path=normalized_path,
            language=language
        )

        transcript = Transcript(
            audio_file_id=audio.id,
            language=transcription_result.get("language"),
            language_probability=transcription_result.get("language_probability"),
            full_text=transcription_result.get("full_text"),
            duration_seconds=transcription_result.get("duration_seconds") or audio.duration_seconds,
        )
        db.add(transcript)
        db.flush()

        for seg in transcription_result.get("segments", []):
            segment_record = TranscriptSegment(
                transcript_id=transcript.id,
                start_seconds=seg["start_seconds"],
                end_seconds=seg["end_seconds"],
                text=seg["text"],
            )
            db.add(segment_record)
        db.commit()

        # 3. Local LLM Note Generation with Ollama
        job.status = "generating_notes"
        job.stage_message = f"Generating structured notes with local Ollama ({notes_service.model})..."
        db.commit()

        llm_output = notes_service.generate_notes(transcript_text=transcript.full_text)

        note = Note(
            transcript_id=transcript.id,
            title=llm_output.title,
            summary=llm_output.summary,
            content_json={
                "title": llm_output.title,
                "summary": llm_output.summary,
                "key_points": llm_output.key_points,
                "keywords": llm_output.keywords,
            }
        )
        db.add(note)
        db.flush()

        for action in llm_output.action_items:
            action_record = ActionItem(
                note_id=note.id,
                task=action.task,
                owner=action.owner,
                deadline_text=action.deadline_text,
                completed=False,
            )
            db.add(action_record)
        db.commit()

        # 4. Completion
        job.status = "completed"
        job.stage_message = "Audio transcribed and notes generated successfully."
        job.completed_at = datetime.now(timezone.utc)
        db.commit()
        logger.info(f"Pipeline job {job_id} completed successfully.")

    except (AudioServiceError, TranscriptionServiceError, NotesServiceError) as e:
        logger.error(f"Pipeline service error in job {job_id}: [{e.code}] {e.message}")
        if job:
            job.status = "failed"
            job.error_code = e.code
            job.error_message = e.message
            job.completed_at = datetime.now(timezone.utc)
            db.commit()
    except Exception as e:
        logger.exception(f"Unexpected pipeline error in job {job_id}: {e}")
        if job:
            job.status = "failed"
            job.error_code = "INTERNAL_ERROR"
            job.error_message = f"An unexpected error occurred during processing: {str(e)}"
            job.completed_at = datetime.now(timezone.utc)
            db.commit()
    finally:
        # Clean up temporary converted wav if distinct from original
        if normalized_path and os.path.exists(normalized_path) and normalized_path != audio.storage_path:
            try:
                os.remove(normalized_path)
            except OSError:
                pass
        db.close()
