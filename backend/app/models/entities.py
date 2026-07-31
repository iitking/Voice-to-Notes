import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    String,
    Float,
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Text,
    JSON,
)
from sqlalchemy.orm import relationship
from app.database.session import Base

def generate_uuid():
    return str(uuid.uuid4())

def utc_now():
    return datetime.now(timezone.utc)

class AudioFile(Base):
    __tablename__ = "audio_files"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    original_filename = Column(String(255), nullable=False)
    storage_path = Column(String(500), nullable=False)
    mime_type = Column(String(100), nullable=True)
    file_size_bytes = Column(BigInteger, nullable=True)
    duration_seconds = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Relationships
    jobs = relationship("ProcessingJob", back_populates="audio_file", cascade="all, delete-orphan")
    transcript = relationship("Transcript", back_populates="audio_file", uselist=False, cascade="all, delete-orphan")


class ProcessingJob(Base):
    __tablename__ = "processing_jobs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    audio_file_id = Column(String(36), ForeignKey("audio_files.id", ondelete="CASCADE"), nullable=False)
    status = Column(String(50), default="queued", nullable=False)  # queued, validating, transcribing, generating_notes, completed, failed
    stage_message = Column(String(255), nullable=True)
    error_code = Column(String(50), nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    audio_file = relationship("AudioFile", back_populates="jobs")


class Transcript(Base):
    __tablename__ = "transcripts"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    audio_file_id = Column(String(36), ForeignKey("audio_files.id", ondelete="CASCADE"), nullable=False)
    language = Column(String(10), nullable=True)
    language_probability = Column(Float, nullable=True)
    full_text = Column(Text, nullable=False)
    duration_seconds = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Relationships
    audio_file = relationship("AudioFile", back_populates="transcript")
    segments = relationship("TranscriptSegment", back_populates="transcript", cascade="all, delete-orphan", order_by="TranscriptSegment.start_seconds")
    note = relationship("Note", back_populates="transcript", uselist=False, cascade="all, delete-orphan")


class TranscriptSegment(Base):
    __tablename__ = "transcript_segments"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    transcript_id = Column(String(36), ForeignKey("transcripts.id", ondelete="CASCADE"), nullable=False)
    start_seconds = Column(Float, nullable=False)
    end_seconds = Column(Float, nullable=False)
    text = Column(Text, nullable=False)

    # Relationships
    transcript = relationship("Transcript", back_populates="segments")


class Note(Base):
    __tablename__ = "notes"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    transcript_id = Column(String(36), ForeignKey("transcripts.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    summary = Column(Text, nullable=False)
    content_json = Column(JSON, nullable=False)  # holds key_points, action_items, keywords, raw llm details
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    transcript = relationship("Transcript", back_populates="note")
    action_items = relationship("ActionItem", back_populates="note", cascade="all, delete-orphan")


class ActionItem(Base):
    __tablename__ = "action_items"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    note_id = Column(String(36), ForeignKey("notes.id", ondelete="CASCADE"), nullable=False)
    task = Column(Text, nullable=False)
    owner = Column(String(100), nullable=True)
    deadline_text = Column(String(100), nullable=True)
    completed = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Relationships
    note = relationship("Note", back_populates="action_items")
