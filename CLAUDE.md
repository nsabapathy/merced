# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A simplified, multi-user AI chat application built with **SvelteKit (frontend)** and **FastAPI (backend)**. Inspired by Open WebUI but with focused scope: Azure cloud only, SQLite, local auth, OpenAI-compatible LLMs, RAG with Chroma, and RBAC.

**Detailed architecture**: See `/Users/naveenS/.claude/plans/iridescent-exploring-rossum.md` for complete system design, database schema, API routes, and data flows.

---

## Tech Stack

- **Frontend**: SvelteKit (Svelte 5.x), TypeScript, Tailwind CSS, Socket.IO client
- **Backend**: Python 3.12+, FastAPI, SQLAlchemy, Alembic, python-socketio, Redis
- **Storage**: SQLite (local dev), Azure Blob Storage (files), Chroma (vectors)
- **Deployment**: Docker Compose (backend, frontend, redis, chroma)

---

## Common Commands

### Backend

```bash
# Development setup
cd backend
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt -r requirements-dev.txt

# Copy and configure environment
cp .env.example .env
# Edit .env with your values

# Database migrations
alembic upgrade head                              # Apply all pending migrations
alembic revision --autogenerate -m "description" # Create new migration
alembic downgrade -1                             # Roll back one step

# Run dev server (auto-reload on file changes)
uvicorn app.main:app --reload --port 8000

# Run tests
pytest                                           # All tests
pytest tests/test_auth.py -v                    # Single file
pytest -k "knowledge" -v                        # Match keyword
pytest --cov=app --cov-report=term-missing     # With coverage

# Lint and format
ruff check . --fix        # Auto-fix lint issues
ruff format .             # Format code
mypy app/                 # Type checking
```

### Frontend

```bash
# Development setup
cd frontend
npm install

# Copy and configure environment (build-time vars)
cp .env.example .env

# Development server (proxies /api to localhost:8000)
npm run dev              # Visit http://localhost:5173

# Type checking and linting
npm run check            # svelte-check + TypeScript
npm run lint             # ESLint
npm run format           # Prettier

# Production build
npm run build            # Creates optimized build in /build
npm run preview          # Preview production build locally
```

### Docker Compose (Full Stack)

```bash
# Start everything
docker compose up --build

# Start in background
docker compose up --build -d

# View logs
docker compose logs -f backend
docker compose logs -f frontend

# Stop services
docker compose down

# Clean up (destructive: removes all data)
docker compose down -v
```

### Infrastructure Only (Local Dev)

```bash
# Start just Redis and Chroma for local backend/frontend dev
docker compose up redis chroma -d
```

---

## Key Directory Structure

```
backend/
  app/
    main.py              # FastAPI app, mounts routers, Socket.IO setup
    config.py            # Pydantic settings, env vars
    dependencies.py      # FastAPI Depends: get_db, get_current_user, require_admin
    models/              # SQLAlchemy ORM models (user, chat, group, etc.)
    schemas/             # Pydantic request/response schemas
    routers/             # FastAPI APIRouter instances (thin HTTP adapters)
    services/            # All business logic (auth, chat, llm, rag, storage, etc.)
    sockets/             # Socket.IO event handlers
    utils/               # Permissions, chunking, helpers

frontend/
  src/
    lib/
      api/               # API client functions (one file per domain)
      stores/            # Svelte 5 runes ($state, $derived)
      components/        # Reusable UI components
      socket.ts          # Socket.IO client singleton
      types/             # TypeScript interfaces
    routes/              # SvelteKit file-based routing
```

---

## Architecture Patterns

**Backend**:
- **Routers**: Thin HTTP adapters that validate input, call services, return schemas
- **Services**: All business logic lives here (stateless, testable without FastAPI)
- **Dependencies**: FastAPI `Depends()` for auth, DB session, permission checks
- **Models vs Schemas**: SQLAlchemy ORM models (DB) are separate from Pydantic schemas (API)

**Frontend**:
- **API layer** (`lib/api/`): All fetch calls isolated here, never in components
- **Stores** (`lib/stores/`): Svelte 5 runes for reactive state (auth, chat, models, UI)
- **Socket.IO**: Singleton connection, typed event emitters for streaming
- **Static build**: No server-side rendering; nginx serves pre-built files

---

## Database & Migrations

- **ORM**: SQLAlchemy 2.0 with async support planned
- **Migrations**: Alembic auto-generates from model changes
- **Flow**: Modify `models/*.py` → `alembic revision --autogenerate -m "..."` → `alembic upgrade head`
- **First admin**: Set `FIRST_ADMIN_EMAIL` + `FIRST_ADMIN_PASSWORD` env vars on first startup for auto-creation

---

## Authentication & Authorization

- **Access token**: JWT (15 min), stored in Svelte memory store only (no localStorage, prevents XSS)
- **Refresh token**: Opaque, HttpOnly cookie (7 days)
- **RBAC**: Admin role + user groups with permission sets
- **Permission model**: Additive allow-list (model_id=NULL = all models, etc.)
- **FastAPI guard**: `get_current_user` dependency + `require_admin` for admin-only routes

---

## Key Services

- **`auth_service.py`**: JWT creation/verification, bcrypt hashing, Redis session management
- **`llm_service.py`**: OpenAI-compatible API client with streaming support
- **`rag_service.py`**: Orchestrates embedding, Chroma vector search, context injection
- **`document_service.py`**: Extracts text (PDF/Word/txt), chunks, embeds, upserts to Chroma
- **`storage_service.py`**: Azure Blob Storage upload/download/delete
- **`chroma_service.py`**: Chroma HTTP client wrapper (collections, upsert, query)

---

## Testing

- **Test DB**: SQLite in-memory for unit tests (`conftest.py`)
- **Fixtures**: Mock users, test client, dependency overrides
- **Coverage target**: Aim for 80%+ on services (routers are thin)
- **Run tests often**: `pytest -v` during development, full suite before commits

---

## Environment Variables

Key variables for development (see `.env.example`):

```
# Database & Infrastructure
DATABASE_URL=sqlite:////data/app.db
REDIS_URL=redis://localhost:6379/0
CHROMA_URL=http://localhost:8001

# Security
SECRET_KEY=<32 random hex bytes>
ENCRYPTION_KEY=<Fernet key for API key encryption>

# Azure (only cloud storage)
AZURE_STORAGE_CONNECTION_STRING=<connection string>
AZURE_STORAGE_CONTAINER=uploads

# Auth
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# RAG
RAG_CHUNK_SIZE=512
RAG_TOP_K=5

# First-run admin (auto-creates on startup if no admin exists)
FIRST_ADMIN_EMAIL=admin@example.com
FIRST_ADMIN_PASSWORD=changeme
```

---

## Design Decisions & Trade-offs

**Why BackgroundTasks for async document indexing?**
- Simple, no extra infrastructure (no Celery, no RabbitMQ)
- Status enum (`pending`, `processing`, `indexed`, `failed`) models async state
- Scales up to moderate volume; can migrate to a job queue later without API changes

**Why Socket.IO over raw WebSockets?**
- Rooms (auto-scoped to `chat_{id}`)
- Reconnection logic built-in
- Fallback to long-polling (universal browser support)
- Redis adapter works with multiple backend instances

**Why single Uvicorn worker?**
- SQLite has write contention; safe with 1 worker
- With PostgreSQL + Redis Socket.IO adapter, horizontal scaling is enabled

**Why static SvelteKit build served by nginx?**
- No Node.js runtime overhead
- Lighter deployment container
- All API calls proxy through nginx to backend

---

## Debugging Tips

**Backend not responding?**
- Check `docker compose logs backend`
- Verify `REDIS_URL` and `CHROMA_URL` are correct
- Test `/api/health` endpoint (if implemented)

**Frontend can't reach backend API?**
- Check Vite proxy config in `vite.config.ts` points to `:8000`
- Verify nginx config forwards `/api/` to backend service
- Check browser console Network tab for 404/503

**Chroma indexing slow?**
- Batch operations in `document_service.py`
- Verify embedding API key/quota
- Check `RAG_CHUNK_SIZE` (smaller chunks = more API calls)

**Permission issues?**
- Verify user is in a group via `get_user_group_ids()` in `utils/permissions.py`
- Check `GroupPermission` rows have correct model/collection IDs
- Test with admin user first (should always have access)

---

## Commits & Code Review

- **Commit message style**: Imperative, present tense ("Add login flow", not "Added")
- **One logical change per commit**: Makes reverting and bisecting easier
- **Include tests**: Services get unit tests, routers get integration tests
- **Before pushing**: Run `pytest`, lint checks, type checking

---

## What NOT to do

- **Don't mix SQLAlchemy models with Pydantic schemas**: Separate them for clarity and to avoid lazy-loading issues
- **Don't call `fetch()` directly from components**: Isolate all HTTP in `lib/api/`
- **Don't store secrets in code or `.env` file in git**: Use env vars and `.gitignore`
- **Don't add features beyond the scope**: Refer to the plan for what's included/excluded
- **Don't skip Alembic migrations**: Always run `alembic upgrade head` after pulling schema changes

---

## Further Reading

- **Detailed architecture & data flows**: See plan file mentioned above
- **FastAPI docs**: https://fastapi.tiangolo.com/
- **SvelteKit docs**: https://kit.svelte.dev/
- **SQLAlchemy 2.0**: https://docs.sqlalchemy.org/
