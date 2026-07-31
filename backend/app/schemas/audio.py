from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime

class AudioUploadResponse(BaseModel):
    audio_file_id: str
    job_id: str
    filename: str
    status: str
    message: str

class JobStatusResponse(BaseModel):
    id: str
    audio_file_id: str
    status: str
    stage_message: Optional[str] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    transcript_id: Optional[str] = None
    note_id: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class TranscriptSegmentResponse(BaseModel):
    id: str
    start_seconds: float
    end_seconds: float
    text: str
    model_config = ConfigDict(from_attributes=True)

class TranscriptResponse(BaseModel):
    id: str
    audio_file_id: str
    language: Optional[str] = None
    language_probability: Optional[float] = None
    full_text: str
    duration_seconds: Optional[float] = None
    created_at: datetime
    segments: List[TranscriptSegmentResponse] = []
    model_config = ConfigDict(from_attributes=True)
