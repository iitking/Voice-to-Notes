import pytest
from fastapi.testclient import TestClient
from app.main import app

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
    assert response.json()["status"] == "online"

def test_notes_list_and_search():
    response = client.get("/api/v1/notes")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

    # Search query
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

def test_note_lifecycle_if_exists():
    # If notes exist in DB from e2e test, verify single get, patch, export
    notes = client.get("/api/v1/notes").json()
    if notes:
        note_id = notes[0]["id"]

        # Get single note
        single_res = client.get(f"/api/v1/notes/{note_id}")
        assert single_res.status_code == 200
        assert single_res.json()["id"] == note_id

        # Patch note
        original_title = single_res.json()["title"]
        patch_res = client.patch(f"/api/v1/notes/{note_id}", json={"title": original_title + " (Updated)"})
        assert patch_res.status_code == 200
        assert patch_res.json()["title"] == original_title + " (Updated)"

        # Revert patch
        client.patch(f"/api/v1/notes/{note_id}", json={"title": original_title})

        # Test action items if present
        action_items = single_res.json().get("action_items", [])
        if action_items:
            item_id = action_items[0]["id"]
            toggle_res = client.patch(
                f"/api/v1/notes/{note_id}/action-items/{item_id}",
                json={"completed": True}
            )
            assert toggle_res.status_code == 200
            assert toggle_res.json()["completed"] is True
            # Revert toggle
            client.patch(
                f"/api/v1/notes/{note_id}/action-items/{item_id}",
                json={"completed": False}
            )

        # Export MD
        export_md = client.get(f"/api/v1/notes/{note_id}/export?format=md")
        assert export_md.status_code == 200
        assert "text/markdown" in export_md.headers["content-type"]

        # Export TXT
        export_txt = client.get(f"/api/v1/notes/{note_id}/export?format=txt")
        assert export_txt.status_code == 200
        assert "text/plain" in export_txt.headers["content-type"]
