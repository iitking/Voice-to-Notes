from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response, PlainTextResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timezone
from app.database.session import get_db
from app.models.entities import Note, Transcript, ActionItem, AudioFile
from app.schemas.notes import (
    NoteResponse,
    NoteUpdate,
    GenerateNotesRequest,
    ActionItemResponse,
    ActionItemUpdate,
)
from app.services.notes_service import notes_service, NotesServiceError

router = APIRouter(prefix="/api/v1", tags=["notes"])

@router.get("/notes", response_model=List[NoteResponse])
def list_notes(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    search: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Lists saved structured notes with optional search filtering."""
    query = db.query(Note).order_by(Note.created_at.desc())
    if search:
        search_filter = f"%{search.strip()}%"
        query = query.filter(
            (Note.title.ilike(search_filter)) | (Note.summary.ilike(search_filter))
        )
    return query.offset(skip).limit(limit).all()

@router.get("/notes/{note_id}", response_model=NoteResponse)
def get_note(note_id: str, db: Session = Depends(get_db)):
    """Retrieves a single note and its action items."""
    note = db.query(Note).filter(Note.id == note_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return note

@router.patch("/notes/{note_id}", response_model=NoteResponse)
def update_note(note_id: str, payload: NoteUpdate, db: Session = Depends(get_db)):
    """Edits note title, summary, or structured JSON content."""
    from sqlalchemy.orm.attributes import flag_modified
    note = db.query(Note).filter(Note.id == note_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    if payload.title is not None:
        note.title = payload.title
    if payload.summary is not None:
        note.summary = payload.summary
    if payload.content_json is not None:
        note.content_json = payload.content_json
        flag_modified(note, "content_json")

    note.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(note)
    return note

@router.delete("/notes/{note_id}")
def delete_note(note_id: str, db: Session = Depends(get_db)):
    """Deletes a note and cleans up associated audio storage and records."""
    import os
    note = db.query(Note).filter(Note.id == note_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    audio_file = note.transcript.audio_file if note.transcript else None
    if audio_file:
        if audio_file.storage_path and os.path.exists(audio_file.storage_path):
            try:
                os.remove(audio_file.storage_path)
            except OSError:
                pass
        db.delete(audio_file)
    else:
        db.delete(note)

    db.commit()
    return {"status": "success", "message": f"Note {note_id} deleted"}

@router.patch("/notes/{note_id}/action-items/{item_id}", response_model=ActionItemResponse)
def update_action_item(
    note_id: str,
    item_id: str,
    payload: ActionItemUpdate,
    db: Session = Depends(get_db),
):
    """Updates or toggles completion status of an action item."""
    item = db.query(ActionItem).filter(
        ActionItem.id == item_id, ActionItem.note_id == note_id
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Action item not found")

    if payload.completed is not None:
        item.completed = payload.completed
    if payload.task is not None:
        item.task = payload.task
    if payload.owner is not None:
        item.owner = payload.owner
    if payload.deadline_text is not None:
        item.deadline_text = payload.deadline_text

    db.commit()
    db.refresh(item)
    return item

@router.post("/notes/generate", response_model=NoteResponse)
def generate_notes_from_transcript(
    payload: GenerateNotesRequest,
    db: Session = Depends(get_db),
):
    """Regenerates or updates structured notes from an existing transcript."""
    transcript = db.query(Transcript).filter(Transcript.id == payload.transcript_id).first()
    if not transcript:
        raise HTTPException(status_code=404, detail="Transcript not found")

    try:
        llm_out = notes_service.generate_notes(
            transcript_text=transcript.full_text,
            custom_instructions=payload.custom_instructions,
        )

        # Check if note already exists
        note = db.query(Note).filter(Note.transcript_id == transcript.id).first()
        if not note:
            note = Note(
                transcript_id=transcript.id,
                title=llm_out.title,
                summary=llm_out.summary,
                content_json={
                    "title": llm_out.title,
                    "summary": llm_out.summary,
                    "key_points": llm_out.key_points,
                    "keywords": llm_out.keywords,
                },
            )
            db.add(note)
            db.flush()
        else:
            note.title = llm_out.title
            note.summary = llm_out.summary
            note.content_json = {
                "title": llm_out.title,
                "summary": llm_out.summary,
                "key_points": llm_out.key_points,
                "keywords": llm_out.keywords,
            }
            note.updated_at = datetime.now(timezone.utc)
            # Clear existing action items to replace
            db.query(ActionItem).filter(ActionItem.note_id == note.id).delete()

        for act in llm_out.action_items:
            db.add(
                ActionItem(
                    note_id=note.id,
                    task=act.task,
                    owner=act.owner,
                    deadline_text=act.deadline_text,
                    completed=False,
                )
            )

        db.commit()
        db.refresh(note)
        return note

    except NotesServiceError as e:
        raise HTTPException(status_code=500, detail={"code": e.code, "message": e.message})

@router.get("/notes/{note_id}/export")
def export_note(
    note_id: str,
    format: str = Query("md", pattern="^(md|txt)$"),
    db: Session = Depends(get_db),
):
    """Exports structured note as clean Markdown (.md) or Plain Text (.txt)."""
    note = db.query(Note).filter(Note.id == note_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    content_data = note.content_json or {}
    key_points = content_data.get("key_points", [])
    keywords = content_data.get("keywords", [])
    transcript_text = note.transcript.full_text if note.transcript else ""

    if format == "md":
        lines = [
            f"# {note.title}",
            "",
            f"**Generated:** {note.created_at.strftime('%Y-%m-%d %H:%M UTC')}",
            "",
            "## Summary",
            note.summary,
            "",
            "## Key Points",
        ]
        for kp in key_points:
            lines.append(f"- {kp}")

        lines.append("")
        lines.append("## Action Items")
        if note.action_items:
            for item in note.action_items:
                status_box = "[x]" if item.completed else "[ ]"
                meta_info = []
                if item.owner:
                    meta_info.append(f"Owner: @{item.owner}")
                if item.deadline_text:
                    meta_info.append(f"Due: {item.deadline_text}")
                meta_str = f" ({', '.join(meta_info)})" if meta_info else ""
                lines.append(f"- {status_box} {item.task}{meta_str}")
        else:
            lines.append("*None*")

        if keywords:
            lines.append("")
            lines.append("## Keywords")
            lines.append(", ".join(f"`{k}`" for k in keywords))

        if transcript_text:
            lines.append("")
            lines.append("---")
            lines.append("## Original Transcript")
            lines.append(transcript_text)

        content = "\n".join(lines)
        filename = f"{note.title.lower().replace(' ', '_')[:40]}.md"
        return Response(
            content=content,
            media_type="text/markdown",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    else:  # txt format
        lines = [
            f"TITLE: {note.title}",
            f"DATE: {note.created_at.strftime('%Y-%m-%d %H:%M UTC')}",
            "=" * 50,
            "",
            "SUMMARY:",
            note.summary,
            "",
            "KEY POINTS:",
        ]
        for kp in key_points:
            lines.append(f"• {kp}")

        lines.append("")
        lines.append("ACTION ITEMS:")
        if note.action_items:
            for item in note.action_items:
                box = "[DONE]" if item.completed else "[TODO]"
                meta = ""
                if item.owner or item.deadline_text:
                    parts = [p for p in [item.owner, item.deadline_text] if p]
                    meta = f" - ({', '.join(parts)})"
                lines.append(f"{box} {item.task}{meta}")
        else:
            lines.append("None")

        if keywords:
            lines.append("")
            lines.append(f"KEYWORDS: {', '.join(keywords)}")

        if transcript_text:
            lines.append("")
            lines.append("-" * 50)
            lines.append("ORIGINAL TRANSCRIPT:")
            lines.append(transcript_text)

        content = "\n".join(lines)
        filename = f"{note.title.lower().replace(' ', '_')[:40]}.txt"
        return Response(
            content=content,
            media_type="text/plain",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
