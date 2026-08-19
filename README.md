# Meeting Summarizer

Transcribes meeting audio and generates action-oriented summaries — a transcript, a narrative overview, key decisions, and structured action items.

Built on Groq's free, low-latency hosting of Whisper (ASR) and Llama 3.3 (summarization), so the whole pipeline runs at $0 cost.

> **Status:** Phase 1 (backend skeleton + upload) in progress. This README will grow with each phase — setup instructions below cover what's runnable today.

## Stack

- **Backend:** FastAPI + SQLAlchemy + SQLite
- **ASR:** Groq — `whisper-large-v3`
- **LLM:** Groq — `llama-3.3-70b-versatile`
- **Frontend:** React + Vite + TypeScript (added in a later phase)

## Backend setup

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS/Linux

pip install -r requirements.txt
copy .env.example .env        # Windows: copy, macOS/Linux: cp
```

Fill in `GROQ_API_KEY` in `.env` (free key at https://console.groq.com — not required yet for Phase 1, but needed from Phase 2 onward).

Run the API:

```bash
uvicorn app.main:app --reload --app-dir .
```

Docs at http://127.0.0.1:8000/docs. `GET /api/health` should return `{"status": "ok"}`.

## API (current)

| Route | Description |
|---|---|
| `POST /api/meetings` | Upload an audio file (multipart, field `file`, optional `title`) |
| `GET /api/meetings` | List all meetings |
| `GET /api/meetings/{id}` | Fetch one meeting |

Transcription, summarization, and the frontend land in later phases.
