import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.main import app
from app.database.session import Base, get_db
from app.models.entities import AudioFile, Note, ActionItem, Transcript

# Isolated in-memory SQLite database for unit tests
TEST_DB_URL = "sqlite:///:memory:"
test_engine = create_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
Base.metadata.create_all(bind=test_engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["database"] == "ok"
    assert "whisper" in data
    assert "ollama" in data

def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert data["architecture"] == "single-user-local"

def test_notes_list_and_search():
    response = client.get("/api/v1/notes")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

    search_res = client.get("/api/v1/notes?search=nonexistenttermxyz")
    assert search_res.status_code == 200
    assert isinstance(search_res.json(), list)

def test_job_not_found():
    response = client.get("/api/v1/jobs/non-existent-id")
    assert response.status_code == 404

def test_upload_unsupported_format():
    files = {"file": ("malicious.exe", b"fake binary content", "application/octet-stream")}
    response = client.post("/api/v1/audio", files=files)
    assert response.status_code == 400
    detail = response.json()["detail"]
    assert detail["code"] == "UNSUPPORTED_FORMAT"

def test_upload_empty_file():
    files = {"file": ("empty.wav", b"", "audio/wav")}
    response = client.post("/api/v1/audio", files=files)
    assert response.status_code == 400
    detail = response.json()["detail"]
    assert detail["code"] == "EMPTY_FILE"

def test_note_lifecycle_crud():
    # Insert a test note
    db = TestingSessionLocal()
    audio = AudioFile(
        original_filename="test_meeting.wav",
        storage_path="/tmp/test_meeting.wav",
        file_size_bytes=1024,
    )
    db.add(audio)
    db.flush()

    transcript = Transcript(
        audio_file_id=audio.id,
        language="en",
        full_text="Discussion about architectural roadmap.",
        duration_seconds=30.0,
    )
    db.add(transcript)
    db.flush()

    note = Note(
        transcript_id=transcript.id,
        title="Engineering Roadmap",
        summary="Roadmap discussion for backend scaling.",
        content_json={"key_points": ["Refactor streaming uploads", "Add Alembic migrations"], "keywords": ["fastapi", "whisper"]},
    )
    db.add(note)
    db.flush()

    action_item = ActionItem(
        note_id=note.id,
        task="Implement streaming uploads",
        owner="Backend Engineer",
        completed=False,
    )
    db.add(action_item)
    db.commit()

    note_id = note.id
    action_item_id = action_item.id
    db.close()

    # 1. Get single note
    single_res = client.get(f"/api/v1/notes/{note_id}")
    assert single_res.status_code == 200
    assert single_res.json()["id"] == note_id
    assert single_res.json()["title"] == "Engineering Roadmap"

    # 2. Patch note title
    patch_res = client.patch(f"/api/v1/notes/{note_id}", json={"title": "Updated Roadmap"})
    assert patch_res.status_code == 200
    assert patch_res.json()["title"] == "Updated Roadmap"

    # 3. Toggle action item
    toggle_res = client.patch(
        f"/api/v1/notes/{note_id}/action-items/{action_item_id}",
        json={"completed": True}
    )
    assert toggle_res.status_code == 200
    assert toggle_res.json()["completed"] is True

    # 4. Export Markdown
    export_md = client.get(f"/api/v1/notes/{note_id}/export?format=md")
    assert export_md.status_code == 200
    assert "text/markdown" in export_md.headers["content-type"]
    assert "Updated Roadmap" in export_md.text

    # 5. Export TXT
    export_txt = client.get(f"/api/v1/notes/{note_id}/export?format=txt")
    assert export_txt.status_code == 200
    assert "text/plain" in export_txt.headers["content-type"]
