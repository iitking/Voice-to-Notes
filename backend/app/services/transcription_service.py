import logging
from typing import Dict, Any, List, Optional
from app.core.config import settings

logger = logging.getLogger(__name__)

class TranscriptionServiceError(Exception):
    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(message)

class TranscriptionService:
    def __init__(self):
        self._model = None
        self.model_name = settings.WHISPER_MODEL
        self.device = settings.WHISPER_DEVICE
        self.compute_type = settings.WHISPER_COMPUTE_TYPE

    def _get_model(self):
        if self._model is None:
            try:
                from faster_whisper import WhisperModel
                logger.info(f"Loading faster-whisper model '{self.model_name}' on {self.device} ({self.compute_type})...")
                self._model = WhisperModel(
                    self.model_name,
                    device=self.device,
                    compute_type=self.compute_type,
                )
                logger.info("faster-whisper model loaded successfully.")
            except Exception as e:
                logger.error(f"Failed to initialize faster-whisper model: {e}")
                raise TranscriptionServiceError(
                    "MODEL_INIT_FAILED",
                    f"Could not load faster-whisper speech recognition model: {str(e)}"
                )
        return self._model

    def transcribe(
        self,
        audio_path: str,
        language: Optional[str] = None
    ) -> Dict[str, Any]:
        """Runs local speech-to-text inference with faster-whisper."""
        model = self._get_model()

        # Language selection: None triggers automatic detection
        target_lang = None
        if language and language.lower() not in ["auto", ""]:
            target_lang = language.strip().lower()

        try:
            logger.info(f"Starting transcription of {audio_path} (target language: {target_lang or 'auto'})...")
            segments_generator, info = model.transcribe(
                audio_path,
                language=target_lang,
                vad_filter=True,
                vad_parameters=dict(min_silence_duration_ms=500),
            )

            segments: List[Dict[str, Any]] = []
            segment_texts: List[str] = []

            for seg in segments_generator:
                cleaned_text = seg.text.strip()
                if cleaned_text:
                    segments.append({
                        "start_seconds": round(float(seg.start), 2),
                        "end_seconds": round(float(seg.end), 2),
                        "text": cleaned_text,
                    })
                    segment_texts.append(cleaned_text)

            full_text = " ".join(segment_texts).strip()

            if not full_text:
                full_text = "(No audible speech detected in recording)"

            return {
                "full_text": full_text,
                "language": info.language,
                "language_probability": round(float(info.language_probability), 4) if info.language_probability else None,
                "duration_seconds": round(float(info.duration), 2) if info.duration else None,
                "segments": segments,
            }

        except TranscriptionServiceError:
            raise
        except Exception as e:
            logger.error(f"faster-whisper transcription error: {e}")
            raise TranscriptionServiceError(
                "TRANSCRIPTION_FAILED",
                f"Local speech-to-text transcription failed: {str(e)}"
            )

transcription_service = TranscriptionService()
