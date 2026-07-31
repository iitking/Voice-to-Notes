import json
import logging
import re
import httpx
from typing import Dict, Any, Optional
from app.core.config import settings
from app.schemas.notes import LLMStructuredOutput

logger = logging.getLogger(__name__)

class NotesServiceError(Exception):
    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(message)

SYSTEM_PROMPT = """You are an expert executive assistant and note taker.
Your job is to convert spoken voice transcripts into faithful, clear, and well-structured notes.

CRITICAL RULES:
1. Base your notes ONLY on what was actually spoken in the transcript.
2. DO NOT hallucinate, invent, or assume any facts, names, decisions, or deadlines that were not explicitly stated.
3. If an action item does not specify an owner or a deadline, set owner or deadline_text to null.
4. Output STRICTLY valid JSON matching the following schema without any extra conversational filler:
{
  "title": "Clear concise descriptive title",
  "summary": "Cohesive, informative summary (2-4 sentences) summarizing the main topic and conclusions",
  "key_points": [
    "Key point 1",
    "Key point 2"
  ],
  "action_items": [
    {
      "task": "Description of the concrete action or task",
      "owner": "Person name or null",
      "deadline_text": "Mentioned deadline or date or null"
    }
  ],
  "keywords": ["topic", "concept", "tag"]
}"""

class NotesService:
    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL.rstrip("/")
        self.model = settings.OLLAMA_MODEL
        self.timeout = settings.OLLAMA_TIMEOUT_SECONDS

    def check_health(self) -> Dict[str, Any]:
        """Checks if local Ollama daemon is reachable and lists available models."""
        try:
            with httpx.Client(timeout=5.0) as client:
                res = client.get(f"{self.base_url}/api/tags")
                if res.status_code == 200:
                    models = [m.get("name") for m in res.json().get("models", [])]
                    return {"status": "ok", "models": models, "configured_model": self.model}
                return {"status": "error", "error": f"Ollama returned HTTP {res.status_code}"}
        except Exception as e:
            return {"status": "unreachable", "error": str(e)}

    def generate_notes(
        self,
        transcript_text: str,
        custom_instructions: Optional[str] = None
    ) -> LLMStructuredOutput:
        """Calls local Ollama instance to generate structured notes from transcript."""
        if not transcript_text or transcript_text.strip() == "":
            raise NotesServiceError("EMPTY_TRANSCRIPT", "Cannot generate notes from empty transcript.")

        user_content = f"TRANSCRIPT:\n\"\"\"\n{transcript_text}\n\"\"\"\n\nPlease generate the structured notes JSON according to the required format."
        if custom_instructions:
            user_content += f"\n\nADDITIONAL INSTRUCTIONS: {custom_instructions}"

        payload = {
            "model": self.model,
            "stream": False,
            "format": "json",
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_content}
            ],
            "options": {
                "temperature": 0.2,
                "top_p": 0.9,
            }
        }

        try:
            logger.info(f"Sending prompt to Ollama ({self.model}) at {self.base_url}/api/chat...")
            with httpx.Client(timeout=float(self.timeout)) as client:
                resp = client.post(
                    f"{self.base_url}/api/chat",
                    json=payload,
                )
        except httpx.ConnectError:
            logger.error("Could not connect to Ollama server.")
            raise NotesServiceError(
                "OLLAMA_UNREACHABLE",
                f"Could not connect to Ollama at {self.base_url}. Ensure 'ollama serve' is running."
            )
        except httpx.TimeoutException:
            logger.error(f"Ollama request timed out after {self.timeout} seconds.")
            raise NotesServiceError(
                "OLLAMA_TIMEOUT",
                f"Local LLM generation timed out after {self.timeout}s. Consider using a smaller model or reducing audio length."
            )
        except Exception as e:
            logger.error(f"Ollama HTTP error: {e}")
            raise NotesServiceError("OLLAMA_ERROR", f"Error communicating with Ollama: {str(e)}")

        if resp.status_code != 200:
            logger.error(f"Ollama returned status code {resp.status_code}: {resp.text}")
            raise NotesServiceError(
                "OLLAMA_ERROR",
                f"Ollama returned HTTP {resp.status_code}: {resp.text[:300]}"
            )

        try:
            data = resp.json()
            message_content = data.get("message", {}).get("content", "").strip()
            
            # Clean markdown JSON fences if present
            cleaned_json = re.sub(r"^```(?:json)?\s*", "", message_content, flags=re.MULTILINE)
            cleaned_json = re.sub(r"\s*```$", "", cleaned_json, flags=re.MULTILINE).strip()
            
            raw_dict = json.loads(cleaned_json)
        except Exception as e:
            logger.error(f"Failed to parse LLM JSON response: {e}, raw: {resp.text[:200]}")
            raise NotesServiceError(
                "INVALID_LLM_OUTPUT",
                f"Ollama did not return valid JSON: {str(e)}"
            )

        # Validate with Pydantic
        try:
            validated_output = LLMStructuredOutput(**raw_dict)
            return validated_output
        except Exception as e:
            logger.error(f"Pydantic validation failed for LLM output: {e}")
            raise NotesServiceError(
                "SCHEMA_VALIDATION_ERROR",
                f"Model response did not conform to required notes schema: {str(e)}"
            )

notes_service = NotesService()
