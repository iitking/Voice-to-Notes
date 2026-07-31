import os
import json
import uuid
import subprocess
import shutil
from typing import Tuple, Dict, Any, Optional
from app.core.config import settings

class AudioServiceError(Exception):
    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(message)

class AudioService:
    def __init__(self, storage_dir: str = settings.AUDIO_STORAGE_DIR):
        self.storage_dir = storage_dir
        os.makedirs(self.storage_dir, exist_ok=True)

    def save_upload(self, original_filename: str, file_bytes: bytes) -> Tuple[str, str, int]:
        """Saves uploaded raw bytes under a secure UUID filename."""
        file_size = len(file_bytes)
        max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
        if file_size > max_bytes:
            raise AudioServiceError(
                "FILE_TOO_LARGE",
                f"File size {file_size / (1024*1024):.1f}MB exceeds limit of {settings.MAX_UPLOAD_SIZE_MB}MB."
            )

        if file_size == 0:
            raise AudioServiceError("EMPTY_FILE", "Uploaded file is empty (0 bytes).")

        _, ext = os.path.splitext(original_filename)
        safe_ext = ext.lower() if ext else ""
        allowed_exts = [".wav", ".mp3", ".m4a", ".ogg", ".webm", ".aac", ".flac"]
        if safe_ext not in allowed_exts:
            raise AudioServiceError(
                "UNSUPPORTED_FORMAT",
                f"Unsupported audio file extension '{safe_ext}'. Allowed: {', '.join(allowed_exts)}"
            )

        filename = f"{uuid.uuid4()}{safe_ext}"
        storage_path = os.path.join(self.storage_dir, filename)

        with open(storage_path, "wb") as f:
            f.write(file_bytes)

        return filename, storage_path, file_size

    def inspect_audio(self, file_path: str) -> Dict[str, Any]:
        """Uses ffprobe to inspect audio stream properties and duration."""
        if not os.path.exists(file_path):
            raise AudioServiceError("FILE_NOT_FOUND", "Audio file does not exist on disk.")

        cmd = [
            "ffprobe",
            "-v", "error",
            "-show_entries", "format=duration,size,bit_rate:stream=codec_name,channels,sample_rate",
            "-of", "json",
            file_path
        ]

        try:
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
            probe_data = json.loads(result.stdout)
        except subprocess.CalledProcessError as e:
            raise AudioServiceError("INVALID_MEDIA", f"Corrupt or unreadable audio media: {e.stderr.strip()[:200]}")
        except Exception as e:
            raise AudioServiceError("PROBE_ERROR", f"Failed to probe audio file: {str(e)}")

        streams = probe_data.get("streams", [])
        if not streams:
            raise AudioServiceError("NO_AUDIO_STREAM", "No valid audio stream detected in file.")

        format_info = probe_data.get("format", {})
        try:
            duration = float(format_info.get("duration", 0.0))
        except (ValueError, TypeError):
            duration = 0.0

        if duration <= 0.1:
            raise AudioServiceError("EMPTY_AUDIO", "Audio duration is too short or empty (<0.1s).")

        if duration > settings.MAX_AUDIO_DURATION_SECONDS:
            raise AudioServiceError(
                "DURATION_EXCEEDED",
                f"Audio duration {duration:.0f}s exceeds maximum allowed {settings.MAX_AUDIO_DURATION_SECONDS}s."
            )

        return {
            "duration": duration,
            "channels": streams[0].get("channels"),
            "sample_rate": streams[0].get("sample_rate"),
            "codec": streams[0].get("codec_name"),
            "size": format_info.get("size")
        }

    def convert_to_wav16k(self, input_path: str) -> str:
        """Converts or normalizes audio into standard 16kHz mono WAV for optimal faster-whisper inference."""
        output_path = f"{os.path.splitext(input_path)[0]}_normalized.wav"
        
        cmd = [
            "ffmpeg",
            "-y",
            "-i", input_path,
            "-ar", "16000",
            "-ac", "1",
            "-c:a", "pcm_s16le",
            output_path
        ]

        try:
            subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
            if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
                raise AudioServiceError("CONVERSION_FAILED", "Normalization produced empty audio output.")
            return output_path
        except subprocess.CalledProcessError as e:
            raise AudioServiceError("CONVERSION_FAILED", f"FFmpeg normalization failed: {e.stderr.strip()[:200]}")

audio_service = AudioService()
