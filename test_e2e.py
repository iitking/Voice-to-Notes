import time
import json
import httpx

API_BASE = "http://127.0.0.1:8000"

def run_end_to_end_test():
    print("=== STARTING REAL END-TO-END VERIFICATION ===")

    # 1. Health check
    with httpx.Client(timeout=10.0) as client:
        health_res = client.get(f"{API_BASE}/health")
        assert health_res.status_code == 200, f"Health check failed: {health_res.text}"
        health_data = health_res.json()
        print("[1/5] Health Check PASSED:")
        print(f"      - Database: {health_data.get('database')}")
        print(f"      - Ollama: {health_data.get('ollama', {}).get('status')} ({health_data.get('ollama', {}).get('configured_model')})")
        print(f"      - Whisper: {health_data.get('whisper', {}).get('model')}")

        # 2. Upload actual audio file
        print("\n[2/5] Uploading real audio file 'test_speech.wav'...")
        with open("test_speech.wav", "rb") as f:
            audio_bytes = f.read()

        files = {"file": ("test_speech.wav", audio_bytes, "audio/wav")}
        data = {"language": "en"}
        upload_res = client.post(f"{API_BASE}/api/v1/audio", files=files, data=data)
        assert upload_res.status_code == 200, f"Upload failed: {upload_res.text}"
        upload_data = upload_res.json()
        job_id = upload_data["job_id"]
        print(f"      - Upload successful! Job ID: {job_id}, Status: {upload_data['status']}")

        # 3. Poll job status
        print("\n[3/5] Polling job status until completion...")
        max_attempts = 60
        job_info = None
        for i in range(max_attempts):
            poll_res = client.get(f"{API_BASE}/api/v1/jobs/{job_id}")
            assert poll_res.status_code == 200, f"Job poll failed: {poll_res.text}"
            job_info = poll_res.json()
            status = job_info["status"]
            stage = job_info.get("stage_message", "")
            print(f"      Attempt {i+1}: Status = {status} | Stage = {stage}")

            if status == "completed":
                print("      - Pipeline COMPLETED successfully!")
                break
            elif status == "failed":
                raise RuntimeError(f"Job failed: [{job_info.get('error_code')}] {job_info.get('error_message')}")

            time.sleep(2)
        else:
            raise TimeoutError("Job did not complete within the timeout period.")

        transcript_id = job_info["transcript_id"]
        note_id = job_info["note_id"]
        assert transcript_id, "Missing transcript_id on completed job"
        assert note_id, "Missing note_id on completed job"

        # 4. Fetch transcript and structured note
        print("\n[4/5] Verifying Transcript & Note retrieval...")
        tr_res = client.get(f"{API_BASE}/api/v1/transcripts/{transcript_id}")
        assert tr_res.status_code == 200
        tr_data = tr_res.json()
        print(f"      - Transcript ({tr_data.get('language')}): \"{tr_data.get('full_text')[:100]}...\"")
        print(f"      - Total Segments: {len(tr_data.get('segments', []))}")

        note_res = client.get(f"{API_BASE}/api/v1/notes/{note_id}")
        assert note_res.status_code == 200
        note_data = note_res.json()
        print(f"      - Note Title: \"{note_data.get('title')}\"")
        print(f"      - Summary: \"{note_data.get('summary')[:120]}...\"")
        print(f"      - Key Points Count: {len(note_data.get('content_json', {}).get('key_points', []))}")
        print(f"      - Action Items Count: {len(note_data.get('action_items', []))}")

        # 5. Export Markdown verification
        print("\n[5/5] Verifying Markdown export...")
        export_res = client.get(f"{API_BASE}/api/v1/notes/{note_id}/export?format=md")
        assert export_res.status_code == 200
        assert "Content-Disposition" in export_res.headers
        md_text = export_res.text
        print("      - Markdown export generated successfully:")
        print("--------------------------------------------------")
        print("\n".join(md_text.splitlines()[:16]))
        print("--------------------------------------------------")

    print("\n=== ALL REAL END-TO-END CHECKS PASSED (NO MOCKS) ===")

if __name__ == "__main__":
    run_end_to_end_test()
