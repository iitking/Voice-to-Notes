"""Initial database schema migration

Revision ID: 0001_initial_schema
Revises: 
Create Date: 2026-08-01 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. audio_files
    op.create_table(
        "audio_files",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("storage_path", sa.String(length=500), nullable=False),
        sa.Column("mime_type", sa.String(length=100), nullable=True),
        sa.Column("file_size_bytes", sa.BigInteger(), nullable=True),
        sa.Column("duration_seconds", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    # 2. processing_jobs
    op.create_table(
        "processing_jobs",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("audio_file_id", sa.String(length=36), sa.ForeignKey("audio_files.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="queued"),
        sa.Column("stage_message", sa.String(length=255), nullable=True),
        sa.Column("error_code", sa.String(length=50), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )

    # 3. transcripts
    op.create_table(
        "transcripts",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("audio_file_id", sa.String(length=36), sa.ForeignKey("audio_files.id", ondelete="CASCADE"), nullable=False),
        sa.Column("language", sa.String(length=10), nullable=True),
        sa.Column("language_probability", sa.Float(), nullable=True),
        sa.Column("full_text", sa.Text(), nullable=False),
        sa.Column("duration_seconds", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    # 4. transcript_segments
    op.create_table(
        "transcript_segments",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("transcript_id", sa.String(length=36), sa.ForeignKey("transcripts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("start_seconds", sa.Float(), nullable=False),
        sa.Column("end_seconds", sa.Float(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
    )

    # 5. notes
    op.create_table(
        "notes",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("transcript_id", sa.String(length=36), sa.ForeignKey("transcripts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("content_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    # 6. action_items
    op.create_table(
        "action_items",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("note_id", sa.String(length=36), sa.ForeignKey("notes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("task", sa.Text(), nullable=False),
        sa.Column("owner", sa.String(length=100), nullable=True),
        sa.Column("deadline_text", sa.String(length=100), nullable=True),
        sa.Column("completed", sa.Boolean(), default=False, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("action_items")
    op.drop_table("notes")
    op.drop_table("transcript_segments")
    op.drop_table("transcripts")
    op.drop_table("processing_jobs")
    op.drop_table("audio_files")
