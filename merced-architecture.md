# Architecture Plan: Simplified AI Chat Application

## Context
Building a greenfield AI chat application inspired by Open WebUI but scoped down to a focused, maintainable feature set. The system needs to be multi-user scalable using SvelteKit + FastAPI — the same tech stack as Open WebUI — but with roughly half the complexity removed.

**Confirmed scope:**
- Azure cloud only (Blob Storage for files)
- SQLite (can migrate to Postgres later)
- Local username/password auth + JWT
- Any OpenAI-compatible LLM endpoint (Azure OpenAI, Groq, Claude, etc.)
- RAG with Chroma vector store (server mode)
- Full RBAC: admin role + user groups with permission sets
- Individual per-user chat history (no shared channels)
- Saved prompts library
- Redis for sessions + Socket.IO scaling
- Docker Compose deployment

**Explicitly excluded:** Ollama, image gen, audio, skills/tools/pipelines, notes, model evaluations, analytics, web search, LDAP/OAuth/SCIM, S3/GCS.

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Docker Compose Network                       │
│                                                                      │
│  ┌──────────────┐    HTTP/WS    ┌────────────────────────────────┐  │
│  │  Frontend    │◄────────────►│         Backend                 │  │
│  │ (nginx:80)   │               │  (uvicorn:8000)                 │  │
│  │              │               │  ├── /api/auth                  │  │
│  │ SvelteKit    │               │  ├── /api/users                 │  │
│  │ static build │               │  ├── /api/groups                │  │
│  │              │               │  ├── /api/chats                 │  │
│  │ Socket.IO ───┼──── WS ──────►│  ├── /api/models               │  │
│  │ client       │               │  ├── /api/knowledge             │  │
│  └──────────────┘               │  ├── /api/files                 │  │
│                                 │  ├── /api/prompts               │  │
│                                 │  └── Socket.IO server           │  │
│                                 └────────────┬───────────────────┘  │
│                                              │                       │
│               ┌──────────────────────────────┼──────────────┐       │
│               ▼                              ▼              ▼       │
│  ┌─────────────────┐         ┌───────────────────┐  ┌────────────┐ │
│  │   SQLite file   │         │  Redis (6379)      │  │  Chroma    │ │
│  │  (volume mount) │         │  Sessions + WS     │  │  (8001)    │ │
│  │                 │         │  adapter           │  │  Vector DB │ │
│  └─────────────────┘         └───────────────────┘  └────────────┘ │
│                                                                      │
│                    ┌───────────────────────────────┐               │
│                    │  Azure Blob Storage (external) │               │
│                    │  Raw file / document storage   │               │
│                    └───────────────────────────────┘               │
│                                                                      │
│              ┌──────────────────────────────────────┐              │
│              │  External LLM APIs (internet)         │              │
│              │  Any OpenAI-compatible endpoint        │              │
│              └──────────────────────────────────────┘              │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Backend Directory Structure

```
backend/
├── alembic/
│   ├── env.py                   # Alembic config, imports Base
│   └── versions/                # Auto-generated migration files
│       └── 0001_initial.py
│
├── app/
│   ├── main.py                  # FastAPI app factory, startup hooks, router mounts
│   ├── config.py                # Pydantic BaseSettings (all env vars)
│   ├── dependencies.py          # get_db, get_current_user, require_admin
│   │
│   ├── db/
│   │   ├── session.py           # SQLAlchemy engine + SessionLocal
│   │   └── base.py              # Imports all models (Alembic visibility)
│   │
│   ├── models/                  # SQLAlchemy ORM models
│   │   ├── user.py              # User, Role enum
│   │   ├── group.py             # Group, GroupMembership, GroupPermission
│   │   ├── chat.py              # Chat, Message
│   │   ├── model_config.py      # ModelConfig
│   │   ├── file.py              # File
│   │   ├── knowledge.py         # KnowledgeCollection, KnowledgeDocument
│   │   └── prompt.py            # Prompt
│   │
│   ├── schemas/                 # Pydantic request/response schemas
│   │   ├── auth.py              # LoginRequest, TokenResponse
│   │   ├── user.py              # UserCreate, UserRead, UserUpdate
│   │   ├── group.py             # GroupCreate, GroupRead, PermissionSet
│   │   ├── chat.py              # ChatCreate, MessageCreate, MessageRead
│   │   ├── model_config.py      # ModelConfigCreate, ModelConfigRead
│   │   ├── knowledge.py         # CollectionCreate, DocumentRead
│   │   └── prompt.py            # PromptCreate, PromptRead
│   │
│   ├── routers/                 # Thin HTTP adapters (call services, return schemas)
│   │   ├── auth.py              # /login, /refresh, /logout
│   │   ├── users.py             # /users, /users/me
│   │   ├── groups.py            # /groups, /groups/{id}/members, /permissions
│   │   ├── chats.py             # /chats CRUD, /chats/{id}/messages POST
│   │   ├── models.py            # /models CRUD
│   │   ├── knowledge.py         # /knowledge CRUD + /documents
│   │   ├── files.py             # /files upload/download/delete
│   │   └── prompts.py           # /prompts CRUD
│   │
│   ├── services/                # All business logic lives here
│   │   ├── auth_service.py      # bcrypt, JWT create/verify, Redis sessions
│   │   ├── user_service.py      # User CRUD, group membership queries
│   │   ├── chat_service.py      # Persist messages, build context window
│   │   ├── llm_service.py       # OpenAI-compatible client, streaming
│   │   ├── rag_service.py       # Embed query → Chroma search → inject context
│   │   ├── document_service.py  # Extract (PDF/Word/txt), chunk, embed, upsert to Chroma
│   │   ├── storage_service.py   # Azure Blob upload/download/delete
│   │   └── chroma_service.py    # Chroma HTTP client wrapper
│   │
│   ├── sockets/
│   │   └── chat_socket.py       # Socket.IO event handlers for streaming
│   │
│   └── utils/
│       ├── chunking.py          # Text splitting (512 tokens, 50 overlap)
│       └── permissions.py       # RBAC evaluation helpers
│
├── tests/
│   ├── conftest.py              # pytest fixtures: test DB, test client, mock users
│   ├── test_auth.py
│   ├── test_chats.py
│   ├── test_knowledge.py
│   └── test_rag.py
│
├── alembic.ini
├── Dockerfile
├── requirements.txt
├── requirements-dev.txt         # pytest, httpx, ruff, mypy
└── .env.example
```

---

## Frontend Directory Structure

```
frontend/
├── src/
│   ├── app.html
│   ├── app.css                  # Tailwind base import
│   │
│   ├── lib/
│   │   ├── api/                 # One file per domain; all fetch calls here
│   │   │   ├── index.ts         # Base fetch wrapper with Bearer token injection
│   │   │   ├── auth.ts          # login(), logout(), refreshToken()
│   │   │   ├── chats.ts         # listChats(), createChat(), getMessages()
│   │   │   ├── models.ts        # listModels(), createModelConfig()
│   │   │   ├── knowledge.ts     # listCollections(), addDocument()
│   │   │   ├── files.ts         # uploadFile(), deleteFile()
│   │   │   ├── users.ts         # listUsers(), createUser()
│   │   │   ├── groups.ts        # listGroups(), updatePermissions()
│   │   │   └── prompts.ts       # listPrompts(), createPrompt()
│   │   │
│   │   ├── stores/              # Svelte 5 runes ($state, $derived)
│   │   │   ├── auth.svelte.ts   # currentUser, accessToken, isAdmin
│   │   │   ├── chat.svelte.ts   # activeChat, messages, streamingMessage
│   │   │   ├── models.svelte.ts # availableModels, selectedModel
│   │   │   └── ui.svelte.ts     # sidebarOpen, theme
│   │   │
│   │   ├── socket.ts            # Socket.IO client singleton, typed events
│   │   │
│   │   ├── components/
│   │   │   ├── chat/
│   │   │   │   ├── ChatWindow.svelte      # Message list + input area
│   │   │   │   ├── MessageBubble.svelte   # Renders message with markdown
│   │   │   │   ├── ChatInput.svelte       # Textarea, send, attachment, prompt picker
│   │   │   │   ├── StreamingIndicator.svelte
│   │   │   │   └── KnowledgeToggle.svelte # Enable/disable knowledge collection
│   │   │   ├── sidebar/
│   │   │   │   ├── Sidebar.svelte
│   │   │   │   └── ChatHistoryItem.svelte
│   │   │   ├── admin/
│   │   │   │   ├── ModelConfigForm.svelte
│   │   │   │   ├── UserTable.svelte
│   │   │   │   ├── GroupForm.svelte
│   │   │   │   └── GroupMemberPicker.svelte
│   │   │   └── shared/
│   │   │       ├── Modal.svelte
│   │   │       ├── Toast.svelte
│   │   │       ├── Spinner.svelte
│   │   │       └── ConfirmDialog.svelte
│   │   │
│   │   └── types/
│   │       ├── api.ts           # TypeScript interfaces matching Pydantic schemas
│   │       └── socket.ts        # Socket.IO event type definitions
│   │
│   └── routes/
│       ├── +layout.svelte       # Auth guard, sidebar, toast container
│       ├── +layout.ts           # Load: silent token refresh on page load
│       ├── +page.svelte         # / → redirect to /chat or /login
│       ├── login/+page.svelte
│       ├── chat/
│       │   ├── +layout.svelte   # Chat layout with sidebar
│       │   ├── +page.svelte     # New chat
│       │   └── [id]/+page.svelte
│       ├── knowledge/
│       │   ├── +page.svelte     # List collections
│       │   └── [id]/+page.svelte # Collection detail + doc upload
│       ├── prompts/+page.svelte
│       └── admin/
│           ├── +layout.svelte   # isAdmin guard
│           ├── users/+page.svelte
│           ├── groups/+page.svelte
│           └── models/+page.svelte
│
├── svelte.config.js             # adapter-static (no SSR)
├── vite.config.ts               # Dev proxy: /api + /socket.io → localhost:8000
├── tailwind.config.ts
├── package.json
├── Dockerfile                   # npm build → nginx static
└── nginx.conf                   # Serves /build, proxies /api and /socket.io
```

---

## Database Schema

### `users`
| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| email | VARCHAR(255) UNIQUE | |
| username | VARCHAR(100) UNIQUE | |
| password_hash | VARCHAR(255) | bcrypt |
| role | ENUM('admin','user') | DEFAULT 'user' |
| is_active | BOOLEAN | DEFAULT TRUE |
| created_at / updated_at | TIMESTAMP | |

### `groups`
| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| name | VARCHAR(100) UNIQUE | |
| description | TEXT | |
| created_by | UUID FK → users.id | |

### `group_memberships`
| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| group_id | UUID FK → groups.id CASCADE | |
| user_id | UUID FK → users.id CASCADE | |
| UNIQUE(group_id, user_id) | | |

### `group_permissions` (additive allow-list)
| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| group_id | UUID FK → groups.id CASCADE | |
| model_id | UUID FK → models_config.id NULLABLE | NULL = all models |
| collection_id | UUID FK → knowledge_collections.id NULLABLE | NULL = all collections |

### `chats`
| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| user_id | UUID FK → users.id CASCADE | |
| title | VARCHAR(255) | auto from first message |

### `messages`
| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| chat_id | UUID FK → chats.id CASCADE | |
| role | ENUM('user','assistant','system') | |
| content | TEXT | |
| token_count | INTEGER | for context window mgmt |
| model_id | UUID FK NULLABLE | |
| knowledge_used | BOOLEAN | |
| created_at | TIMESTAMP | |

### `models_config`
| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| name | VARCHAR(100) UNIQUE | display name |
| base_url | VARCHAR(500) | e.g. https://...openai.azure.com |
| api_key | TEXT | Fernet-encrypted at app level |
| model_id | VARCHAR(200) | e.g. "gpt-4o" |
| is_active | BOOLEAN | |

### `files`
| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| user_id | UUID FK → users.id | |
| original_name | VARCHAR(500) | |
| blob_path | TEXT | Azure Blob key |
| content_type | VARCHAR(100) | |
| size_bytes | BIGINT | |

### `knowledge_collections`
| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| name | VARCHAR(255) | |
| chroma_collection_name | VARCHAR(255) UNIQUE | maps to Chroma |
| created_by | UUID FK → users.id | |

### `knowledge_documents`
| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| collection_id | UUID FK → knowledge_collections.id CASCADE | |
| file_id | UUID FK → files.id CASCADE | |
| title | VARCHAR(500) | |
| chunk_count | INTEGER | |
| status | ENUM('pending','processing','indexed','failed') | |
| error_message | TEXT | |
| indexed_at | TIMESTAMP | |

### `prompts`
| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| user_id | UUID FK → users.id CASCADE | |
| title | VARCHAR(255) | |
| content | TEXT | |
| is_public | BOOLEAN | visible to all users |

---

## API Routes

All prefixed with `/api`. JWT Bearer token required unless marked (public).

**Auth** — `/api/auth`
- `POST /login` (public) — credentials → access + refresh tokens
- `POST /refresh` — refresh token → new access token
- `POST /logout` — invalidate Redis session

**Users** — `/api/users`
- `GET /me`, `PUT /me` — own profile
- `GET /`, `POST /`, `PUT /{id}`, `DELETE /{id}` — admin only

**Groups** — `/api/groups` (admin only)
- Full CRUD + `POST /{id}/members`, `DELETE /{id}/members/{uid}`, `PUT /{id}/permissions`

**Chats** — `/api/chats`
- `GET /` — list own chats
- `POST /` — create chat
- `GET /{id}` — chat + all messages
- `PUT /{id}` — rename; `DELETE /{id}`
- `POST /{id}/messages` — save user turn, kick off Socket.IO stream, return immediately

**Models** — `/api/models`
- `GET /` — list accessible models (filtered by group permissions)
- `POST /`, `PUT /{id}`, `DELETE /{id}` — admin only

**Knowledge** — `/api/knowledge`
- `GET /`, `POST /`, `GET /{id}`, `DELETE /{id}` — collection CRUD
- `POST /{id}/documents` — trigger async indexing
- `DELETE /{id}/documents/{doc_id}`

**Files** — `/api/files`
- `POST /upload`, `GET /{id}`, `GET /{id}/download`, `DELETE /{id}`

**Prompts** — `/api/prompts`
- `GET /`, `POST /`, `PUT /{id}`, `DELETE /{id}`

---

## Key Data Flows

### Chat Message with RAG
1. Frontend POSTs to `/api/chats/{id}/messages` with `{content, model_id, knowledge_id?}`
2. Backend saves user message to DB
3. If `knowledge_id`: embed query → Chroma vector search → retrieve top-K chunks → prepend as system context
4. Load last N messages from DB (context window)
5. Call LLM stream API with assembled prompt
6. Emit `stream_chunk` events via Socket.IO room `chat_{id}` as tokens arrive
7. Emit `stream_end` when done; save assistant message to DB
8. Frontend joined the Socket.IO room on page load, receives tokens live

### Document Upload + Indexing
1. `POST /api/files/upload` → stream to Azure Blob → create `File` record
2. `POST /api/knowledge/{id}/documents` → create `KnowledgeDocument` (status=pending) → return immediately
3. `BackgroundTasks`: download from Azure Blob → extract text (pdfplumber / python-docx / plain) → chunk (512 tokens, 50 overlap) → embed via embedding API → upsert to Chroma collection → update status=indexed

### Token Security
- Access token (JWT, 15 min): stored in Svelte memory store only — never localStorage (XSS protection)
- Refresh token (opaque, 7 days): stored as HttpOnly cookie
- On page reload: layout `load()` calls `/api/auth/refresh` silently to restore session
- API keys for LLM models: encrypted with Fernet (`cryptography` lib) using `ENCRYPTION_KEY` env var; never returned in API responses

---

## RBAC Design

```
admin role → full access to everything

user role  → access determined by group memberships
             └── GroupPermission rows (additive allow-list):
                 model_id=NULL       = access all models
                 model_id=<uuid>     = access that specific model
                 collection_id=NULL  = access all knowledge collections
                 collection_id=<uuid>= access that specific collection
```

Permission check (in `utils/permissions.py`):
```python
def can_access_model(user_id, model_id, db) -> bool:
    group_ids = get_user_group_ids(user_id, db)
    return db.query(GroupPermission).filter(
        GroupPermission.group_id.in_(group_ids),
        or_(GroupPermission.model_id == model_id, GroupPermission.model_id == None)
    ).first() is not None
```

FastAPI dependency chain: `get_current_user` → `require_admin` (for admin-only routes).

---

## Docker Compose

```yaml
services:
  backend:   uvicorn:8000  — volumes: sqlite_data:/data; depends_on: redis, chroma
  frontend:  nginx:80      — serves static SvelteKit build; proxies /api + /socket.io to backend
  redis:     redis:7-alpine — volumes: redis_data:/data
  chroma:    chromadb/chroma:latest — volumes: chroma_data:/chroma/chroma; IS_PERSISTENT=TRUE

volumes: sqlite_data, redis_data, chroma_data
```

**Backend**: 1 Uvicorn worker (SQLite write contention). Scale horizontally by migrating to Postgres + increasing workers — Redis adapter already supports it.

---

## Environment Variables

| Variable | Purpose |
|----------|---------|
| `DATABASE_URL` | `sqlite:////data/app.db` |
| `REDIS_URL` | `redis://redis:6379/0` |
| `CHROMA_URL` | `http://chroma:8001` |
| `SECRET_KEY` | JWT signing key (32 hex bytes) |
| `ENCRYPTION_KEY` | Fernet key for LLM API key encryption |
| `AZURE_STORAGE_CONNECTION_STRING` | Azure Blob connection string |
| `AZURE_STORAGE_CONTAINER` | Blob container name |
| `FIRST_ADMIN_EMAIL` / `FIRST_ADMIN_PASSWORD` | Seed admin user on first run |
| `RAG_CHUNK_SIZE` | Default 512 tokens |
| `RAG_TOP_K` | Default 5 chunks retrieved per query |

---

## Build & Dev Commands

```bash
# Backend dev
cd backend && python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8000

# Frontend dev (proxies /api to localhost:8000 via Vite)
cd frontend && npm install && npm run dev

# Infra only (for local dev)
docker compose up redis chroma -d

# Full stack
docker compose up --build

# Migrations
alembic revision --autogenerate -m "description"
alembic upgrade head

# Tests
pytest --cov=app --cov-report=term-missing
pytest tests/test_auth.py -v

# Lint/format
ruff check . --fix && ruff format .  # backend
npm run check && npm run lint        # frontend
```

---

## Verification Plan

1. `docker compose up --build` — all four services start cleanly
2. `GET /api/health` returns 200
3. Create admin via `FIRST_ADMIN_EMAIL` env var on first boot
4. Admin logs in, gets JWT, can reach `/admin` panel
5. Admin creates a model config (Azure OpenAI), creates a group with model access
6. Admin creates a regular user, assigns to group
7. User logs in, selects model, sends a chat message → response streams in UI
8. User uploads a PDF, adds to knowledge collection → status becomes "indexed"
9. User enables knowledge collection in chat, asks a question → RAG chunks visible in context
10. Refresh token flow: expire access token manually, confirm silent refresh works
11. Non-admin user cannot reach `/api/groups` (403)
