# Open Web UI - Architecture Overview

## High-Level Architecture

Open Web UI is a **full-stack web application** with a clear separation between frontend and backend:

```
┌─────────────────────────────────────────────────────────────┐
│                    FRONTEND (SvelteKit)                     │
│                   src/lib, src/routes                       │
└─────────────────────────┬───────────────────────────────────┘
                          │ (WebSocket, HTTP/REST)
┌─────────────────────────▼───────────────────────────────────┐
│                 FastAPI Backend (Python)                    │
│              backend/open_webui/ (main.py)                  │
└─────────────────────────┬───────────────────────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
    ┌───▼────┐    ┌──────▼──────┐    ┌───▼─────┐
    │Database │    │ Vector DBs  │    │ LLM APIs│
    │(SQLite/ │    │(Chroma, Qdrant)   │(Ollama, │
    │Postgres)│    │etc.         │    │OpenAI...)
    └────────┘    └─────────────┘    └─────────┘
```

---

## 🔧 Backend Architecture (Python/FastAPI)

### Core Entry Point: `backend/open_webui/main.py`

- **Web Framework**: FastAPI
- **Server**: Uvicorn (ASGI)
- **Key Components**:
  - Middleware stack (CORS, compression, sessions, audit logging)
  - Static file serving
  - Router registration
  - WebSocket integration (Socket.IO)

### Backend Directory Structure

```
backend/open_webui/
├── main.py                    # FastAPI app setup & middleware
├── config.py                  # Configuration management (133KB!)
├── env.py                     # Environment variable handling
├── models/                    # Database models (24 files)
├── routers/                   # API endpoints (30 routers)
├── utils/                     # Helper utilities (35 modules)
├── retrieval/                 # RAG/Vector DB logic
├── socket/                    # WebSocket (Socket.IO) handlers
├── tools/                     # Tool/function implementations
├── storage/                   # Cloud storage backends (S3, GCS, Azure)
├── migrations/                # Database migrations (Alembic)
└── data/                      # Data directory
```

### Database Models (`backend/open_webui/models/`)

Open Web UI supports multiple databases:
- **SQLite** (default, embedded)
- **PostgreSQL** (with pgvector for embeddings)
- **MongoDB** (optional)
- **MariaDB** (optional)

Key model files:
- `users.py` - User accounts & authentication
- `chats.py` - Conversation history
- `documents.py` - RAG documents
- `models.py` - Model metadata
- `knowledge.py` - Knowledge base/collections
- `memories.py` - User/chat memories
- `prompts.py` - Saved prompts
- `channels.py` - Team channels
- `groups.py` - User groups & RBAC
- `evaluations.py` - Model evaluations
- `files.py` - File metadata

### API Routers (`backend/open_webui/routers/`)

RESTful API endpoints organized by feature:

| Router | Purpose |
|--------|---------|
| `auths.py` | Authentication, login, SSO, LDAP |
| `users.py` | User management, profiles |
| `chats.py` | Chat conversations, messages |
| `models.py` | Model management, pulling (Ollama) |
| `ollama.py` | Ollama integration, model operations |
| `openai.py` | OpenAI & compatible API proxying |
| `retrieval.py` | RAG, vector DB, document indexing |
| `knowledge.py` | Knowledge collections, embeddings |
| `documents.py` (in retrieval) | Document management |
| `images.py` | Image generation (DALL-E, ComfyUI, etc.) |
| `audio.py` | Speech-to-text & text-to-speech |
| `files.py` | File upload/download |
| `prompts.py` | Prompt management |
| `tools.py` | Tool/function management |
| `functions.py` | Python function execution |
| `memories.py` | Persistent artifact storage |
| `channels.py` | Team channels & collaboration |
| `groups.py` | User group management |
| `configs.py` | App configuration endpoints |
| `analytics.py` | Usage analytics |
| `tasks.py` | Background tasks |
| `terminals.py` | Browser terminal (xterm) |
| `skills.py` | Plugin/skill management |
| `pipelines.py` | Pipeline plugin integration |
| `scim.py` | SCIM 2.0 for enterprise provisioning |
| `evaluations.py` | Model evaluation tracking |

### WebSocket Layer (`backend/open_webui/socket/`)

Real-time features using **Socket.IO**:
- Live chat streaming (LLM responses)
- Model status updates
- Connection pooling for concurrent users
- Event emitters for real-time messaging

### Retrieval/RAG (`backend/open_webui/retrieval/`)

Advanced features:
- **Vector databases**: Chroma, PGVector, Qdrant, Milvus, Elasticsearch, Pinecone, Oracle, S3Vector
- **Document loaders**: Tika, Docling, Document Intelligence, Mistral OCR
- **Embeddings**: Multiple providers (local transformers, OpenAI, etc.)
- **Web search**: 15+ providers (Google PSE, Brave, DuckDuckGo, Tavily, etc.)
- **Web browsing**: URL content extraction

### Storage/Cloud Integration (`backend/open_webui/storage/`)

Multi-cloud support:
- AWS S3
- Google Cloud Storage (GCS)
- Azure Blob Storage
- Local file storage

### Utilities (`backend/open_webui/utils/`)

Supporting modules (35 utilities):
- **Logging & Monitoring**: OpenTelemetry, audit logging
- **Auth**: JWT, LDAP, OAuth, Session management
- **Document Processing**: PDF, Word, Excel parsing
- **Caching**: Redis integration
- **LLM Integration**: Provider abstraction layer
- **Rate limiting, permissions, validation**

---

## 🎨 Frontend Architecture (SvelteKit/TypeScript)

### Tech Stack

- **Framework**: SvelteKit (Svelte 5.x)
- **Build Tool**: Vite
- **Styling**: Tailwind CSS + PostCSS
- **Component Library**: Bits UI
- **Editor**: TipTap (rich text)
- **Real-time**: Socket.IO client
- **Package Manager**: npm

### Frontend Directory Structure

```
src/
├── lib/                       # Reusable code
│   ├── apis/                 # API client modules (30+ files)
│   ├── components/           # UI components (20+ folders)
│   ├── stores/               # Svelte stores (state management)
│   ├── types/                # TypeScript interfaces
│   ├── utils/                # Helper functions
│   ├── constants/            # App constants
│   ├── i18n/                 # Internationalization (i18n)
│   ├── workers/              # Web workers (background tasks)
│   └── pyodide/              # Python execution in browser (Pyodide)
├── routes/                    # SvelteKit pages (file-based routing)
├── app.html                   # Root HTML template
├── app.css                    # Global styles
└── tailwind.css              # Tailwind utilities
```

### Key Frontend Modules

#### API Clients (`src/lib/apis/`)

30+ API modules for different features:
- `chat.ts` - Chat API calls
- `models.ts` - Model management
- `ollama.ts` - Ollama integration
- `openai.ts` - OpenAI proxy
- `rag.ts` / `documents.ts` - RAG/retrieval
- `knowledge.ts` - Knowledge base
- `audio.ts` - Audio operations
- `images.ts` - Image generation
- `users.ts` - User operations
- `auth.ts` - Authentication
- `files.ts` - File operations
- `tools.ts` - Tool management
- `memories.ts` - Memory operations
- `channels.ts` - Channel operations
- `analytics.ts` - Analytics
- `config.ts` - Configuration
- **All use**: Fetch API with error handling & auth tokens

#### State Management (`src/lib/stores/`)

Svelte stores for:
- User authentication state
- Chat history & messages
- Models list
- UI state (sidebar, theme, modals)
- Settings & preferences
- WebSocket connection status

#### Components (`src/lib/components/`)

Rich UI component library:
- **Chat UI**: Chat interface, message display, input
- **Settings**: User settings, preferences, model config
- **Models**: Model selector, model management
- **Documents**: Document viewer, RAG interface
- **Navigation**: Sidebar, header, navigation
- **Forms**: Input components, form handling
- **Modals**: Dialog boxes, confirmation modals
- **Code**: Code editor, syntax highlighting (CodeMirror)
- **Rich Text**: TipTap editor with extensions
- **Shared**: Common components (buttons, icons, etc.)

#### Routes/Pages (`src/routes/`)

File-based routing (SvelteKit):
```
src/routes/
├── +layout.svelte           # Root layout
├── +page.svelte             # Home page
├── chat/
│   └── [id]/               # Chat detail page
├── settings/                # Settings pages
├── documents/              # Document management
├── models/                 # Model management
├── tools/                  # Tool management
├── admin/                  # Admin pages
└── [API routes]            # Server-side endpoints (+server.ts)
```

#### Web Workers (`src/lib/workers/`)

Background processing:
- Markdown parsing
- Image optimization
- Document processing
- Heavy computations (keep UI responsive)

#### Internationalization (`src/lib/i18n/`)

Multi-language support (i18next):
- Locale files (JSON)
- Language detection
- Dynamic language switching
- 20+ languages supported

---

## 🔄 Data Flow & Communication

### Request/Response Flow

```
Frontend (Browser)
    │
    ├─── HTTP/REST ──────────────────→ FastAPI Routers
    │                                      │
    │    (REST API)                    (CRUD operations,
    │                                  Business logic)
    │                                      │
    │    ←──────────── JSON ──────────── Database
    │
    └─── WebSocket (Socket.IO) ──────→ Socket handlers
                                           │
         (Real-time streaming,         Event emission,
          live model outputs)           Data broadcasting
                                           │
                                    ← Messages, events
```

### Key Request/Response Patterns

#### 1. Chat Interaction
```
User types message
    ↓
Frontend: POST /api/chat/completions (streaming)
    ↓
Backend: Route to LLM (Ollama/OpenAI/etc.)
    ↓
LLM generates response (streaming)
    ↓
Frontend receives chunks via SSE or WebSocket
    ↓
Display incremental response in UI
```

#### 2. RAG/Document Retrieval
```
User uploads document
    ↓
Frontend: POST /api/documents/upload
    ↓
Backend:
  - Extract text (using Tika/Docling)
  - Chunk text
  - Generate embeddings (vector)
  - Store in vector DB
    ↓
User queries with #document
    ↓
Backend:
  - Embed user query
  - Vector search (retrieve similar chunks)
  - Include in LLM prompt as context
    ↓
LLM generates informed response
```

#### 3. WebSocket for Real-time Updates
```
Client connects: socket.io
    ↓
Subscribe to events: socket.on('message_chunk')
    ↓
Server streams LLM response chunks
    ↓
Frontend updates UI in real-time
    ↓
Connection maintains state in Redis
```

---

## 🔐 Authentication & Security

### Supported Auth Methods

1. **Local**: Username/password with bcrypt
2. **OAuth**: Google, GitHub, Microsoft, etc.
3. **LDAP/Active Directory**: Enterprise integration
4. **SCIM 2.0**: User provisioning (Okta, Azure AD)
5. **JWT**: Token-based auth
6. **SSO**: Trusted headers

### Session Management

- **Sessions store**: Redis (distributed) or in-memory
- **Session middleware**: `starsessions` with Redis backend
- **Token**: JWT for API authentication
- **RBAC**: Role-based access control with granular permissions

---

## 🗄️ Database Architecture

### Default (SQLite)

```
webui.db (or custom path)
├── Users table
├── Chats table (conversations)
├── Messages table
├── Models table (metadata)
├── Documents table
├── Embeddings table (vectors)
├── Knowledge collections
└── ... (24+ tables)
```

### PostgreSQL (Production)

```
PostgreSQL database
├── All SQLite tables
├── pgvector extension (embeddings as vectors)
├── Full-text search
└── Horizontal scaling with Redis
```

### Vector Databases (for RAG)

Pluggable vector DB support:
- **Chroma**: Embedded or server mode
- **Qdrant**: Modern vector DB
- **Milvus**: Scalable vector DB
- **PGVector**: PostgreSQL native
- **Elasticsearch/OpenSearch**: Search + vectors
- **Pinecone**: Cloud vector DB
- **Weaviate**: Vector search engine
- **Oracle 23ai**: Enterprise DB with vectors
- **S3Vector**: AWS-native

---

## 🔌 Extension Points

### 1. Pipelines Plugin System

Custom logic injection via Python:
```python
# Custom pipeline in separate service
def init_handler(request) -> dict:
    return {"status": True}

def process_message_handler(messages: list, **kwargs) -> dict:
    # Custom processing
    return {"messages": messages}
```

Connection via `OPENAI_API_BASE_URL=http://pipeline-service:8000`

### 2. Tools/Function Calling

Built-in Python function support:
- Pure Python functions (no imports)
- Exposed to LLM for calling
- Execute in sandbox (RestrictedPython)
- Return results to LLM

### 3. LLM Providers

Configurable LLM backends:
- **Ollama** (local)
- **OpenAI API** (ChatGPT, GPT-4)
- **OpenAI-compatible** (LM Studio, Mistral, Groq, etc.)
- **Google Gemini** (`google-genai`)
- **Anthropic Claude** (`anthropic`)
- **Custom**: Any OpenAI-compatible endpoint

### 4. Models Integration

Multiple models in parallel:
- Same conversation with different models
- Compare outputs
- Custom model builders
- Model pulling (from Ollama Hub)

---

## 📊 Key Features Architecture

### Chat System
- **Messages**: Stored in DB with embeddings
- **Conversations**: Grouped into chats
- **Memory**: Configurable context window
- **Streaming**: Server-sent events or WebSocket
- **Multi-model**: Compare models simultaneously

### RAG/Knowledge Base
- **Document ingest**: Multiple formats (PDF, Word, etc.)
- **Chunking**: Configurable chunk size & overlap
- **Embeddings**: Multiple embedding models
- **Vector search**: Semantic similarity
- **Web integration**: Search + browsing
- **Collections**: Organize documents

### Image Generation
- **DALL-E 3** (OpenAI)
- **Gemini** (Google)
- **ComfyUI** (local, open-source)
- **Stable Diffusion** (AUTOMATIC1111)
- **Image editing**: Prompt-based editing

### Speech/Audio
- **Speech-to-Text (STT)**:
  - Whisper (local, OpenAI)
  - Azure, Deepgram
- **Text-to-Speech (TTS)**:
  - Azure, ElevenLabs, OpenAI
  - Transformers (local)
  - WebAPI (browser native)

### Team Features
- **Channels**: Shared conversation spaces
- **User Groups**: Organize users
- **Permissions**: Granular RBAC
- **Admin panel**: User & model management

---

## 🚀 Deployment Architecture

### Docker Deployment

```dockerfile
# Multi-stage build
FROM node:... AS frontend-build
  # SvelteKit build → dist/

FROM python:3.11-slim
  # Copy frontend build
  # Install Python deps
  # Run FastAPI + Uvicorn
```

### Environment Variables

Key configs:
- `OLLAMA_BASE_URL` - Ollama endpoint
- `OPENAI_API_KEY` - OpenAI key
- `OPENAI_API_BASE_URL` - Custom LLM endpoint
- `DATABASE_URL` - DB connection
- `REDIS_URL` - Redis for sessions
- `HF_TOKEN` - Hugging Face token
- `VECTOR_DB_*` - Vector DB configs

### Scaling Considerations

- **Horizontal**: Multiple workers behind load balancer
- **Sessions**: Redis-backed for multi-worker
- **WebSocket**: Socket.IO with Redis adapter
- **Database**: PostgreSQL for multi-instance
- **Vector DB**: Managed cloud service (Pinecone, Qdrant Cloud)

---

## 📝 Development Workflow

### Frontend Development
```bash
npm run dev              # Start SvelteKit dev server (port 5173)
npm run build           # Production build
npm run check           # TypeScript checks
npm run lint            # ESLint + type checking
npm run format          # Prettier formatting
npm run test:frontend   # Vitest unit tests
```

### Backend Development
```bash
# Python development
pip install -e .                    # Install in dev mode
open-webui serve                    # Run server
python -m pytest                    # Run tests
pylint backend/                     # Lint
ruff format backend/                # Format
```

### Database Migrations
```bash
# Using Alembic
alembic revision --autogenerate -m "description"
alembic upgrade head
```

---

## 📂 File Sizes & Code Statistics

### Backend Highlights
- `config.py`: 133KB (extensive configuration)
- `main.py`: 96KB (FastAPI setup)
- `retrieval.py`: 121KB (RAG implementation)
- `openai.py`: 54KB (OpenAI integration)
- `ollama.py`: 63KB (Ollama integration)
- **Total Backend**: ~24 Python modules, comprehensive

### Frontend Highlights
- `package.json`: Svelte 5.x, Vite, TailwindCSS
- `package-lock.json`: 552KB (large dependency tree)
- Rich TypeScript frontend with 30+ API modules
- Extensive component library (20+ folders)

---

## 🎯 Architecture Patterns

### 1. Middleware Pattern (Backend)
- CORS, compression, session management
- Audit logging
- Error handling
- Custom middleware chain

### 2. Router Pattern (Backend)
- Modular endpoints by feature
- Dependency injection (FastAPI)
- Middleware per router
- OpenAPI/Swagger docs

### 3. Store Pattern (Frontend)
- Svelte stores for state
- Reactive updates
- Centralized state management
- Local storage persistence

### 4. Component Pattern (Frontend)
- Reusable Svelte components
- Props-based composition
- Slot-based content projection
- Reactive state bindings

### 5. Provider Pattern (Backend)
- LLM provider abstraction
- Vector DB provider abstraction
- Storage provider abstraction
- Flexible switching between implementations

---

## 🔄 Real-time Communication Stack

### Socket.IO (WebSocket)
- **Purpose**: Real-time streaming, live updates
- **Usage**: Chat response streaming, model updates
- **Server**: Python socket.io library
- **Client**: socket.io-client (browser)
- **Storage**: Redis for distributed sessions

### Server-Sent Events (SSE)
- **Alternative**: Streaming responses
- **Usage**: Fallback for WebSocket
- **Browser native**: EventSource API

---

## Summary

Open Web UI is a **modular, extensible AI platform** with:

✅ **Clean separation**: Frontend (Svelte) ↔ Backend (FastAPI)
✅ **Multiple LLM support**: Ollama, OpenAI, custom APIs
✅ **Advanced RAG**: Multiple vector DBs, document processing
✅ **Real-time**: WebSocket + Socket.IO streaming
✅ **Enterprise-ready**: LDAP, SCIM, RBAC, audit logging
✅ **Cloud-native**: Containerized, scalable, multi-database support
✅ **Extensible**: Pipelines, plugins, custom tools
✅ **Developer-friendly**: Clear architecture, well-organized code

The architecture prioritizes **flexibility, scalability, and user experience** while maintaining code clarity through domain-driven organization.
