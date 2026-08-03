import os
import sys
import time
import json
import shutil
import math
import struct
import wave
import subprocess
import httpx

API_BASE = "http://127.0.0.1:8000"

def generate_synthetic_audio_wav(output_path: str, duration_sec: float = 3.0, sample_rate: int = 16000) -> str:
    """
    Generates a deterministic 16kHz mono PCM WAV file using pure Python wave module.
    Simulates speech-like frequency modulations (150Hz-800Hz formants).
    """
    num_samples = int(duration_sec * sample_rate)
    with wave.open(output_path, "wb") as wf:
        wf.setnchannels(1)  # mono
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(sample_rate)
        
        frames = bytearray()
        for i in range(num_samples):
            t = float(i) / sample_rate
            # Harmonic speech formant modulation
            mod = 0.5 * math.sin(2.0 * math.pi * 5.0 * t) + 0.5
            val = (
                0.5 * math.sin(2.0 * math.pi * 220.0 * t) +
                0.3 * math.sin(2.0 * math.pi * 440.0 * t) +
                0.2 * math.sin(2.0 * math.pi * 880.0 * t)
            ) * mod
            sample_val = int(val * 16384)
            frames.extend(struct.pack("<h", max(-32768, min(32767, sample_val))))
        
        wf.writeframes(frames)
    return output_path

def ensure_test_audio_fixture(filename: str = "test_speech.wav") -> str:
    """
    Ensures a valid test audio file exists.
    Checks root, checks backend/tests/fixtures, or synthesizes deterministically.
    """
    # 1. Check local root file
    if os.path.exists(filename) and os.path.getsize(filename) > 1000:
        return filename

    # 2. Check test fixtures directory
    fixture_path = os.path.join(os.path.dirname(__file__), "backend", "tests", "fixtures", filename)
    if os.path.exists(fixture_path) and os.path.getsize(fixture_path) > 1000:
        shutil.copyfile(fixture_path, filename)
        return filename

    # 3. If macOS 'say' command is available, generate real speech sample
    if shutil.which("say") and shutil.which("ffmpeg"):
        try:
            temp_aiff = "test_temp.aiff"
            text_prompt = "We had a productive project sync. Sarah will finalize the backend API architecture by next Wednesday, and David is going to implement the React UI components by Friday. Let's schedule a review meeting on Monday to test the end to end integration."
            subprocess.run(["say", "-v", "Samantha", text_prompt, "-o", temp_aiff], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(["ffmpeg", "-y", "-i", temp_aiff, "-ar", "16000", "-ac", "1", filename], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if os.path.exists(temp_aiff):
                os.remove(temp_aiff)
            if os.path.exists(filename) and os.path.getsize(filename) > 1000:
                return filename
        except Exception:
            pass

    # 4. Fallback: Pure Python deterministic synthetic PCM WAV
    print("      [Notice] Synthesizing deterministic audio fixture via python wave module...")
    return generate_synthetic_audio_wav(filename, duration_sec=3.0)

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

        # 2. Ensure audio fixture exists and upload
        audio_path = ensure_test_audio_fixture("test_speech.wav")
        print(f"\n[2/5] Uploading verified audio fixture '{audio_path}' ({os.path.getsize(audio_path)} bytes)...")
        with open(audio_path, "rb") as f:
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
