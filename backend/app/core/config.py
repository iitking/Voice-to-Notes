from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from typing import List

class Settings(BaseSettings):
    """
    Application configuration settings.
    Designed for local-first, privacy-focused single-user deployment.
    """
    APP_ENV: str = "development"
    APP_NAME: str = "Voice to Notes AI"
    API_V1_PREFIX: str = "/api/v1"
    
    # Database (PostgreSQL 16)
    DATABASE_URL: str = "postgresql+psycopg://voice_notes:change-this-password@localhost:5432/voice_notes"
    
    # Local Ollama LLM
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen2.5:3b"
    OLLAMA_TIMEOUT_SECONDS: int = 180
    
    # Local Faster-Whisper STT
    WHISPER_MODEL: str = "base"
    WHISPER_DEVICE: str = "cpu"
    WHISPER_COMPUTE_TYPE: str = "int8"
    WHISPER_DEFAULT_LANGUAGE: str = "auto"
    
    # Audio Upload Limits & Local Storage
    MAX_UPLOAD_SIZE_MB: int = 100
    MAX_AUDIO_DURATION_SECONDS: int = 3600
    AUDIO_STORAGE_DIR: str = "./storage/audio"
    
    # CORS: Comma-separated list of allowed web frontend origins
    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000"
    
    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    model_config = ConfigDict(env_file=".env", extra="allow")

settings = Settings()
