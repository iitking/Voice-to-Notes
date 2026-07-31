# Voice to Notes AI

An end-to-end, local-first voice-to-notes web application. Record audio in the browser or upload an audio file, transcribe it with **faster-whisper running locally**, and turn the transcript into structured notes with a **local LLM served by Ollama**.

> **Project status:** Architecture and implementation plan. This README describes the intended real application and its verification process; it does not claim that the application, integrations, or tests have already been implemented or passed. Update the status and evidence after running the project on your machine.

## Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Technology stack](#technology-stack)
- [Requirements](#requirements)
- [Quick start](#quick-start)
- [Configuration](#configuration)
- [Application workflow](#application-workflow)
- [API contract](#api-contract)
- [AI pipeline](#ai-pipeline)
- [Database design](#database-design)
- [Repository structure](#repository-structure)
- [Testing and verification](#testing-and-verification)
- [Security and privacy](#security-and-privacy)
- [Troubleshooting](#troubleshooting)
- [Roadmap](#roadmap)
- [Limitations](#limitations)
- [License](#license)

## Overview

Voice to Notes AI converts spoken content into editable, searchable notes:

1. Record audio in the browser or upload an audio file.
2. The backend validates the file and creates a processing job.
3. FFmpeg normalizes supported audio when required.
4. faster-whisper transcribes the audio locally.
5. Ollama runs a local language model to generate structured notes.
6. The application saves the transcript and notes in PostgreSQL.
7. The user can review, edit, search, and export the result.

The initial release is designed for personal notes, lectures, interviews, and meeting recordings. It should not be described as a real-time transcription system unless streaming transcription is implemented separately.

## Features

### MVP

- Browser audio recording using the MediaRecorder API.
- Audio file upload.
- File type, size, and duration validation.
- Local speech recognition using faster-whisper.
- Automatic language detection, with an optional language override.
- Transcript with timestamps where available.
- Local LLM note generation through Ollama.
- Structured output: title, summary, key points, action items, and keywords.
- Editable transcript and notes.
- Processing status and useful error messages.
- Persistent history in PostgreSQL.
- Markdown and TXT export.

### Planned enhancements

- Speaker diarization using a separately configured diarization model.
- Ask questions about a transcript.
- Automatic topic chapters.
- PDF export.
- User accounts and multi-user access.
- Background job queue for long recordings.
- Optional translation between supported languages.

Features in this section are planned, not implied to be implemented.

## Architecture

```mermaid
flowchart TD
    U[User] --> FE[React + Vite frontend]
    FE -->|REST API| API[FastAPI backend]
    API --> VAL[File validation]
    VAL --> STORE[Local audio storage]
    VAL --> JOB[Processing job]
    JOB --> FF[FFmpeg normalization]
    FF --> STT[faster-whisper local transcription]
    STT --> TR[Transcript]
    TR --> LLM[Ollama local LLM]
    LLM --> NOTES[Structured notes]
    TR --> DB[(PostgreSQL)]
    NOTES --> DB
    JOB --> DB
    DB --> API
    API --> FE
    FE --> EXP[Markdown / TXT export]
```

### Component responsibilities

| Component | Responsibility |
|---|---|
| React + Vite | Recording, upload, transcript review, notes editor, history |
| FastAPI | API validation, orchestration, persistence, status reporting |
| faster-whisper | Local speech-to-text inference |
| FFmpeg | Audio inspection and conversion |
| Ollama | Local LLM inference for note generation |
| PostgreSQL | Users, audio metadata, jobs, transcripts, notes |
| SQLAlchemy + Alembic | Database access and schema migrations |
| Pytest | Backend unit and integration tests |
| Docker Compose | Reproducible application services |

### Processing model

For the first milestone, FastAPI can run the processing pipeline in a background task and expose a job-status endpoint. This is suitable for a local single-user MVP, but it is not a durable distributed queue. For production or multiple concurrent users, move long-running jobs to Celery or another queue backed by Redis, and store audio in durable object storage.

## Technology stack

| Layer | Technology |
|---|---|
| Frontend | React, Vite, JavaScript or TypeScript |
| Styling | Tailwind CSS |
| Audio capture | Browser MediaRecorder API |
| Backend | Python, FastAPI, Pydantic |
| Speech recognition | faster-whisper, CTranslate2 |
| Audio conversion | FFmpeg |
| Local LLM runtime | Ollama |
| Example local model | `qwen2.5:3b` (hardware-dependent) |
| Database | PostgreSQL |
| ORM / migrations | SQLAlchemy, Alembic |
| Background jobs (scale-up) | Celery, Redis |
| Backend tests | pytest, httpx |
| Frontend tests | Vitest, React Testing Library |
| Browser tests (optional) | Playwright |
| Containers | Docker, Docker Compose |

Model names and hardware requirements change. Check the model's current Ollama library page and faster-whisper documentation before choosing a production model.

## Requirements

- Python 3.10 or newer (use a version supported by the selected faster-whisper release).
- Node.js LTS and npm.
- Git.
- FFmpeg installed and available on `PATH`.
- Ollama installed and running locally.
- PostgreSQL 15 or newer, locally or through Docker.
- Enough RAM and disk space for the selected speech and language models.

### Hardware notes

- CPU inference is possible but may be slow for long recordings.
- A compatible NVIDIA GPU can accelerate faster-whisper when the correct CUDA/cuDNN dependencies are installed.
- Ollama model performance depends on available RAM/VRAM and quantization.
- Start with short test recordings before processing long files.
- Do not promise a fixed transcription speed or accuracy across machines.

## Quick start

The commands below are a setup template. They become executable as written once the matching backend and frontend files have been implemented in the repository.

### 1. Clone the repository

```bash
git clone https://github.com/<YOUR_GITHUB_USERNAME>/voice-to-notes-ai.git
cd voice-to-notes-ai
```

### 2. Install system dependencies

Install FFmpeg and Ollama using the official instructions for your operating system.

Verify:

```bash
ffmpeg -version
ollama --version
```

Start Ollama:

```bash
ollama serve
```

In a second terminal, download a small local model:

```bash
ollama pull qwen2.5:3b
ollama list
```

A smaller model is easier to run on modest hardware but may produce weaker summaries. You can choose another model and set its name in the environment file.

### 3. Configure PostgreSQL

Create a database and user, or use the included Docker Compose setup after it has been added:

```sql
CREATE USER voice_notes WITH PASSWORD 'change-this-password';
CREATE DATABASE voice_notes OWNER voice_notes;
```

Never use the example password in a public or shared environment.

### 4. Set up the backend

```bash
cd backend
python -m venv .venv
```

Activate the environment:

**macOS / Linux**
```bash
source .venv/bin/activate
```

**Windows PowerShell**
```powershell
.venv\Scripts\Activate.ps1
```

Install dependencies after `backend/requirements.txt` has been created:

```bash
pip install -r requirements.txt
```

Create `backend/.env` using the configuration example below, then apply database migrations:

```bash
alembic upgrade head
```

Start the API:

```bash
uvicorn app.main:app --reload
```

Expected local API address: `http://127.0.0.1:8000`

FastAPI interactive documentation: `http://127.0.0.1:8000/docs`

### 5. Set up the frontend

Open a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Expected Vite development address: `http://localhost:5173`

### 6. Verify local services

```bash
# Ollama model availability
ollama list

# Ollama API health
curl http://127.0.0.1:11434/api/tags

# FastAPI health (once implemented)
curl http://127.0.0.1:8000/health
```

The application should not report a successful transcription or note generation until the relevant local model call has actually completed and its result has been validated.

## Configuration

Create `backend/.env` (do not commit it):

```dotenv
APP_ENV=development
APP_NAME=Voice to Notes AI
API_V1_PREFIX=/api/v1

DATABASE_URL=postgresql+psycopg://voice_notes:change-this-password@localhost:5432/voice_notes

OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:3b
OLLAMA_TIMEOUT_SECONDS=180

WHISPER_MODEL=small
WHISPER_DEVICE=cpu
WHISPER_COMPUTE_TYPE=int8
WHISPER_DEFAULT_LANGUAGE=auto

MAX_UPLOAD_SIZE_MB=100
MAX_AUDIO_DURATION_SECONDS=3600
AUDIO_STORAGE_DIR=./storage/audio

CORS_ORIGINS=http://localhost:5173
```

Configuration notes:

- `WHISPER_MODEL`: choose a supported faster-whisper model such as `tiny`, `base`, `small`, `medium`, or `large-v3`. Larger models generally need more compute and memory.
- `WHISPER_DEVICE=cpu` is a conservative CPU setup. GPU settings must match the installed CUDA/cuDNN/CTranslate2 environment.
- `WHISPER_COMPUTE_TYPE=int8` is a common CPU choice; supported values depend on device and hardware.
- `WHISPER_DEFAULT_LANGUAGE=auto` means let the model detect the language. For a known language, use a supported language code such as `en` or `hi`.
- `MAX_UPLOAD_SIZE_MB` and maximum duration must be enforced by the backend, not only by the browser.
- Use a strong database password and a secret-management solution outside local development.
- If Ollama runs in a different container, `localhost` will refer to that container, not the host. Configure the service hostname or host gateway correctly.

## Application workflow

### Audio ingestion

1. The browser records audio as a Blob or submits an uploaded file.
2. The frontend sends it as multipart form data.
3. The backend checks the file size, extension, MIME type, and actual media metadata.
4. The backend generates a random storage name; it must not trust the uploaded filename.
5. The backend creates a job with a `queued` or `processing` state.

The server must inspect the actual media content. A filename extension or browser MIME type alone is not sufficient validation.

### Audio preprocessing

- Use FFmpeg/ffprobe to inspect the media.
- Convert unsupported inputs into a consistent format when needed.
- Preserve the original upload only if required by the product's retention policy.
- Handle corrupt, silent, empty, and excessively long audio.
- Do not normalize or denoise automatically unless the chosen processing has been tested; aggressive processing can reduce recognition quality.

### Transcription

Example faster-whisper usage:

```python
from faster_whisper import WhisperModel

model = WhisperModel(
    "small",
    device="cpu",
    compute_type="int8",
)

segments, info = model.transcribe(
    "storage/audio/example.wav",
    language=None,           # automatic language detection
    vad_filter=True,
)

transcript_segments = []
for segment in segments:
    transcript_segments.append({
        "start": segment.start,
        "end": segment.end,
        "text": segment.text.strip(),
    })

transcript_text = " ".join(
    item["text"] for item in transcript_segments
)
```

This is a usage example, not a complete production service. In the application, load the model once per worker rather than once per request, handle exceptions, enforce limits, and persist segment metadata.

### Local LLM note generation

Ollama exposes a local HTTP API. Example request:

```bash
curl http://localhost:11434/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen2.5:3b",
    "stream": false,
    "format": "json",
    "messages": [
      {
        "role": "system",
        "content": "Create faithful structured notes from the transcript. Do not invent facts, decisions, names, or deadlines. If information is missing, return an empty value or mark it as not specified. Return valid JSON only."
      },
      {
        "role": "user",
        "content": "Create a title, summary, key_points, action_items, and keywords from this transcript: We discussed the project timeline. The team will review the prototype next Friday."
      }
    ]
  }'
```

Validate the returned JSON against a Pydantic schema before saving it. Treat model output as untrusted input. The LLM must not invent action owners or deadlines that are not present in the transcript.

Suggested note schema:

```json
{
  "title": "Project timeline discussion",
  "summary": "The team discussed the project timeline and planned a prototype review.",
  "key_points": [
    "The project timeline was discussed.",
    "The prototype will be reviewed next Friday."
  ],
  "action_items": [
    {
      "task": "Review the prototype",
      "owner": null,
      "deadline_text": "next Friday"
    }
  ],
  "keywords": ["project", "timeline", "prototype"]
}
```

The example above illustrates the expected structure; it is not a result from a live model run.

For long transcripts, split text into overlapping chunks, summarize each chunk, and then consolidate the summaries. Preserve source timestamps or segment references so users can trace notes back to the recording.

## API contract

The following is the recommended initial API contract. Implement and document actual request/response schemas in FastAPI before treating this table as a live API.

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/health` | Application health |
| `POST` | `/api/v1/audio` | Upload audio and create a job |
| `GET` | `/api/v1/jobs/{job_id}` | Read processing status |
| `GET` | `/api/v1/transcripts/{transcript_id}` | Read transcript and segments |
| `POST` | `/api/v1/notes/generate` | Generate notes from a transcript |
| `GET` | `/api/v1/notes` | List saved notes |
| `GET` | `/api/v1/notes/{note_id}` | Read a note |
| `PATCH` | `/api/v1/notes/{note_id}` | Edit a note |
| `DELETE` | `/api/v1/notes/{note_id}` | Delete a note |
| `GET` | `/api/v1/notes/{note_id}/export?format=md` | Export Markdown or TXT |

### Job states

Use explicit states such as:

- `queued`
- `validating`
- `transcribing`
- `generating_notes`
- `completed`
- `failed`

Store a safe error code and a user-readable message. Do not expose stack traces, local file paths, credentials, or raw internal exceptions to the browser.

## Database design

Recommended initial entities:

| Table | Example fields |
|---|---|
| `users` | `id`, `email`, `password_hash`, `created_at` |
| `audio_files` | `id`, `user_id`, `storage_key`, `duration_seconds`, `mime_type` |
| `processing_jobs` | `id`, `audio_file_id`, `status`, `error_code`, `created_at`, `completed_at` |
| `transcripts` | `id`, `audio_file_id`, `language`, `full_text`, `created_at` |
| `transcript_segments` | `id`, `transcript_id`, `start_seconds`, `end_seconds`, `text` |
| `notes` | `id`, `user_id`, `transcript_id`, `title`, `summary`, `content_json`, `updated_at` |
| `action_items` | `id`, `note_id`, `task`, `owner`, `deadline_text`, `completed` |

Use UUIDs or other non-guessable identifiers. Add foreign keys, indexes, timestamps, and ownership checks. A user must only be able to access their own records.

## Repository structure

```text
voice-to-notes-ai/
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── hooks/
│   │   ├── services/
│   │   └── App.jsx
│   ├── package.json
│   └── vite.config.js
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── routes/
│   │   ├── core/
│   │   ├── database/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   │   ├── audio_service.py
│   │   │   ├── transcription_service.py
│   │   │   └── notes_service.py
│   │   ├── workers/
│   │   └── main.py
│   ├── tests/
│   ├── alembic/
│   └── requirements.txt
│
├── storage/
│   └── .gitkeep
├── docs/
│   ├── architecture.md
│   └── screenshots/
├── .env.example
├── .gitignore
├── docker-compose.yml
├── README.md
└── LICENSE
```

Do not commit uploaded audio, model weights, database files, `.env`, virtual environments, or generated user notes.

## Testing and verification

A project is not verified merely because the server starts. Test each real integration and record the results from the machine used.

### Backend test plan

Use pytest for:

- Health endpoint.
- Upload validation: valid file, unsupported extension, invalid media, oversized file.
- Empty and silent audio handling.
- Transcription service with a short real audio fixture.
- Language selection and automatic detection.
- Ollama unavailable / timeout handling.
- Ollama response with invalid JSON.
- Pydantic validation of generated notes.
- Database persistence and retrieval.
- User ownership and authorization checks.
- Export content and file format.
- Job status transitions and failure handling.

Example commands once tests exist:

```bash
cd backend
pytest -q
pytest --cov=app --cov-report=term-missing
```

### Frontend test plan

Test:

- Record, stop, and upload interactions.
- Permission denied and microphone unavailable states.
- Upload progress and processing status.
- Failed transcription and failed note generation states.
- Transcript editing and note editing.
- History, search, and export.
- Responsive layout and keyboard accessibility.

Example commands once scripts exist:

```bash
cd frontend
npm test
npm run build
```

### Real end-to-end verification

Before claiming the project works end to end, run this manual test:

1. Start PostgreSQL, Ollama, and the backend.
2. Confirm the configured Ollama model is present with `ollama list`.
3. Start the frontend.
4. Record a 20–60 second speech sample with a clear sentence and a stated task/date.
5. Upload the recording and wait for the job to finish.
6. Confirm that the transcript contains the spoken content.
7. Confirm that the notes are generated by the configured local Ollama model.
8. Check that the note is saved in PostgreSQL and remains available after a page refresh.
9. Edit the note, save it, and verify the change persists.
10. Export Markdown/TXT and inspect the downloaded file.
11. Repeat with a Hindi or Hinglish sample if those languages are in scope.
12. Stop Ollama and repeat a request; the UI should show a clear failure, not fabricated output.

Keep a verification record in the repository:

| Check | Result | Evidence |
|---|---|---|
| Backend tests | Not run | Add CI run link |
| Frontend tests | Not run | Add CI run link |
| Production build | Not run | Add build log |
| Local Whisper transcription | Not run | Add sample/test record |
| Local Ollama generation | Not run | Add model and test record |
| PostgreSQL persistence | Not run | Add integration test |
| End-to-end flow | Not run | Add screenshot or test report |

Replace `Not run` only after actually running each check. Do not publish fabricated accuracy scores, screenshots, benchmarks, or passing-test badges.

### Suggested CI checks

A GitHub Actions workflow should run backend unit tests, frontend tests, linting, and frontend production build on each pull request. Keep model-dependent integration tests separate unless the CI runner is deliberately provisioned with FFmpeg, Ollama, the selected model, and adequate resources.

## Security and privacy

- Audio and transcripts can contain sensitive personal information. Obtain consent before recording other people.
- Keep Ollama bound to localhost for a single-machine setup unless remote access is deliberately secured.
- Never expose Ollama or the database directly to the public internet.
- Validate uploads server-side; limit size, duration, and allowed media formats.
- Generate random storage filenames and prevent path traversal.
- Do not trust transcript text or LLM output as executable instructions.
- Store password hashes using a modern password-hashing algorithm; never store plaintext passwords.
- Enforce authorization on every record read, update, export, and delete.
- Configure CORS narrowly.
- Keep secrets out of Git and logs.
- Define retention and deletion behavior for original audio and derived transcripts.
- Use HTTPS and secure cookies when deployed.
- Add rate limits and resource limits before allowing public uploads.

## Troubleshooting

| Problem | Things to check |
|---|---|
| `ffmpeg` not found | Install FFmpeg and verify it is on `PATH` |
| Ollama connection refused | Start `ollama serve`; verify the base URL |
| Model not found | Run `ollama pull <model-name>` and check `ollama list` |
| Transcription is slow | Try a smaller Whisper model or supported GPU configuration |
| Out-of-memory error | Reduce model size, concurrency, or audio duration |
| Unsupported audio | Inspect with `ffprobe` and convert with FFmpeg |
| CORS error | Check the frontend origin against backend CORS settings |
| Database connection failed | Verify PostgreSQL is running and `DATABASE_URL` is correct |
| Long request times out | Use background jobs and poll the job-status endpoint |

## Roadmap

- [ ] Repository and development environment
- [ ] React recording and upload interface
- [ ] FastAPI upload and validation endpoint
- [ ] FFmpeg audio inspection/conversion
- [ ] faster-whisper local transcription
- [ ] Ollama structured note generation
- [ ] PostgreSQL persistence and migrations
- [ ] Job status and error handling
- [ ] Transcript and notes editor
- [ ] Markdown and TXT export
- [ ] Backend and frontend automated tests
- [ ] Real end-to-end verification
- [ ] Docker Compose development environment
- [ ] Authentication and per-user authorization
- [ ] Speaker diarization
- [ ] Ask questions about a transcript
- [ ] Deployment and CI

## Limitations

- Transcription accuracy varies with accent, language, recording quality, background noise, and model choice.
- Hinglish and code-switching may be less accurate than clear single-language speech.
- Local inference can be slow on CPU-only hardware.
- Small local LLMs may omit details or produce imperfect summaries. Always review generated notes.
- Speaker diarization is not included in the MVP and requires additional model setup.
- This project is an assistant for organizing spoken information, not a source of guaranteed factual or legal records.

## License

Choose a license before publishing. MIT is a common option for open-source projects; add a `LICENSE` file only after deciding which license you want to use.
