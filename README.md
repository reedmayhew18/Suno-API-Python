# Suno API (Python Version)

This is a Python/FastAPI port of the original Suno API (previously implemented in Go). It provides endpoints to submit and fetch Suno music/lyrics generation tasks, as well as a chat-completion interface using OpenAI tools with Server-Sent Events (SSE) support.

## Features
- FastAPI web framework
- SQLAlchemy (SQLite/PostgreSQL/MySQL) with Alembic migrations
- Background task queue for polling Suno task status
- HTTP client using httpx with default Suno headers
- SSE streaming for chat completions via `sse-starlette`
- Pydantic-based request/response schemas
- Configuration via `.env` and `python-dotenv`
- Logging with loguru
- Integrated tests using pytest

## Quickstart

### 1. Clone & Install Dependencies
```bash
git clone <repo_url>
cd suno-api-python
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 2. Configure Environment
Copy `.env` (provided) and set your values:
```ini
# .env
PORT=8000
DEBUG=false
SECRET_TOKEN=your_secret_token  # optional
SESSION_ID=...                  # your Suno session ID
COOKIE=...                      # your Suno cookie string
DATABASE_URL=sqlite:///./api.db # or any SQLAlchemy URL
BASE_URL=https://studio-api.suno.ai
EXCHANGE_TOKEN_URL=https://clerk.suno.com/v1/client/sessions/{}/tokens?_clerk_js_version=4.73.2
CHAT_OPENAI_MODEL=gpt-4o
CHAT_OPENAI_BASE=https://api.openai.com
CHAT_OPENAI_KEY=sk-...
CHAT_TEMPLATE_DIR=./template
CHAT_TIME_OUT=600
PROXY=                          # optional HTTP proxy
LOG_DIR=./logs
ROTATE_LOGS=false
```

### 3. Initialize the Database
By default the app uses SQLite (`api.db`). To create/migrate tables:
```bash
# Apply Alembic migrations (recommended)
alembic upgrade head
# Or let FastAPI auto-create tables on startup (init_db())
```

### 4. Run the Server
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

#### Endpoints
- `GET /ping` &rarr; Health check
- `POST /suno/submit/{music|lyrics}` &rarr; Submit task
- `GET /suno/fetch/{id}` &rarr; Fetch single task
- `POST /suno/fetch` &rarr; Fetch multiple tasks
- `GET /suno/account` &rarr; Account & billing info
- `POST /v1/chat/completions` &rarr; Chat-completion with SSE streaming (uses OpenAI + Suno tool)

Authentication: If `SECRET_TOKEN` is set, requests must send `Authorization: Bearer <SECRET_TOKEN>` header.

### 5. Running Tests
```bash
pytest
```

## Project Structure
```
.
├── app/
│   ├── config.py         # env vars loader
│   ├── database.py       # SQLAlchemy setup
   ├── logger.py         # loguru setup
   ├── models/           # SQLAlchemy models
   ├── routers/          # FastAPI routers
   ├── schemas/          # Pydantic schemas
   ├── services/         # business logic (Suno, account, tasks)
   └── utils/            # HTTP client, templates, auth
├── alembic/             # Alembic migrations
├── requirements.txt
├── main.py              # app entrypoint
└── README_python.md     # this file
```

## License
This project is released under the same license as the original Suno API.
