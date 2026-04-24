# Smart Document Q&A

Smart Document Q&A is a backend system for uploading PDF and DOCX documents, processing them asynchronously, indexing their contents, and answering questions strictly from the uploaded material.

The project was built to feel like a real service, not just a demo of retrieval-augmented generation. That means the focus is not only on getting an answer back from a model, but also on clear system boundaries, predictable failure handling, traceable processing, reproducible local setup, and grounded responses with citations.

## Problem

Teams often rely on internal documents such as employee policies, onboarding guides, operating procedures, product notes, or technical documentation. Those documents are useful, but they are rarely easy to search in practice.

The common problems are familiar:

- manual document search is slow
- keyword search misses meaning and context
- direct LLM usage can hallucinate
- large files take time to process
- systems become hard to trust when answers are not traceable

So the real problem is not simply "how to chat with a PDF." The real problem is:

How can a system answer questions from documents in a way that is grounded, explainable, and operationally reliable?

## Objective

This project aims to build a document question-answering backend that:

- accepts PDF and DOCX uploads
- stores documents and processing status cleanly
- processes uploads asynchronously so the API remains responsive
- extracts text and splits it into usable chunks
- generates embeddings for semantic retrieval
- retrieves the most relevant context for a question
- asks the LLM to answer only from that context
- returns citations for traceability
- supports conversations and follow-up questions
- runs locally with a straightforward Docker setup

## What This System Does

At a practical level, the system supports the following flow:

1. A document is uploaded through the API.
2. The API saves the file, creates a document record, and creates a pending job.
3. A Celery worker picks up the job and:
   - extracts text
   - chunks the text
   - embeds the chunks
   - stores vectors in FAISS
4. A user asks a question.
5. The system:
   - embeds the query
   - retrieves the nearest chunks
   - builds a grounded prompt
   - calls the LLM
6. The response is returned with citations to the chunks used.

## Architecture

### High-Level View

```mermaid
flowchart TD
    client[Client]
    api[FastAPI API]
    db[(PostgreSQL)]
    storage[File Storage]
    redis[(Redis)]
    worker[Celery Worker]
    extract[Extraction]
    chunking[Chunking]
    embedding[Embedding]
    faiss[(FAISS Index)]
    retrieval[Retrieval + Prompt Building]
    llm[Hosted Ollama-Compatible LLM Endpoint]
    answer[Grounded Answer + Citations]

    client --> api
    api --> db
    api --> storage
    api --> redis
    redis --> worker
    worker --> extract
    extract --> chunking
    chunking --> embedding
    embedding --> faiss
    api --> retrieval
    retrieval --> faiss
    retrieval --> db
    retrieval --> llm
    llm --> answer
```

### Processing Flow

```text
Upload request
  -> validate file
  -> save file to storage
  -> create document row
  -> create job row
  -> enqueue worker task

Worker task
  -> mark document as processing
  -> extract text
  -> chunk text
  -> store chunks
  -> embed chunks
  -> store vectors in FAISS
  -> mark document as ready
```

### Question Answering Flow

```text
Question
  -> embed query
  -> search FAISS
  -> fetch chunk text from DB
  -> build grounded prompt
  -> call LLM
  -> return answer + citations
```

## RAG Design

This project uses a dense-retrieval RAG design.

That means the system retrieves chunks based on semantic similarity in embedding space, not just keyword overlap.

### What retrieval approach is used?

The current implementation uses:

- dense semantic retrieval
- sentence-transformer embeddings
- FAISS exact nearest-neighbor search
- top-k retrieval
- distance-threshold filtering
- optional document filtering
- grounded prompting for final answer generation

### What it does not use right now

The current version does not use:

- hybrid search
- BM25 or keyword-first retrieval
- reranking
- metadata filtering inside FAISS itself
- query rewriting with a separate LLM step

So the honest description is:

This is a semantic-search RAG system, not a hybrid-search RAG system.

### Embedding model

The embedding layer uses:

```text
sentence-transformers/all-MiniLM-L6-v2
```

This model converts both document chunks and user queries into dense vectors so that semantically similar text lands close together in vector space.

### Vector search algorithm

The FAISS index used in this project is:

```text
faiss.IndexFlatL2
```

That means the system is using exact nearest-neighbor search with L2 distance.

For this project, that choice was intentional:

- it keeps the retrieval behavior simple and transparent
- it is easy to run locally
- it avoids the extra complexity of approximate indexing for a relatively small local system

### Retrieval steps used in this codebase

When a question comes in, the system does the following:

1. embeds the question into a dense vector
2. queries FAISS for the top-k nearest chunk vectors
3. filters weak matches using a distance threshold
4. fetches the matching chunk text from PostgreSQL
5. optionally filters the chunks by selected document IDs
6. preserves FAISS ranking order
7. builds a prompt from only those retrieved chunks
8. sends that prompt to the LLM

### Follow-up question handling

Follow-up handling is lightweight but intentional.

Instead of running a separate query-rewrite model, the service expands the retrieval query using recent user turns from the same conversation. That gives the retriever extra context without adding another model stage.

### Why semantic retrieval was chosen

Semantic retrieval fits this use case better than plain keyword matching because users often ask questions differently than the source document is written.

For example, a user may ask:

```text
leave policy
```

while the document says:

```text
12 casual leave days per year
```

Dense semantic retrieval is more likely to connect those two ideas than a simple lexical match.

### Why hybrid retrieval was not added yet

Hybrid search can improve recall in many systems, especially when exact terms matter a lot.

It was not the first choice here because the priority for this project was to build a smaller, grounded, reproducible end-to-end system first. Dense retrieval alone was enough to get a reliable local pipeline in place without adding BM25, score fusion, or reranking complexity.

### How hallucination is reduced in this RAG flow

The system reduces hallucination through a few deliberate choices:

- only retrieved chunks are sent to the LLM
- weak retrieval results are filtered by distance
- if no reliable chunks remain, the system returns a no-answer fallback
- the prompt explicitly instructs the LLM not to answer outside the provided context
- citations are returned with the answer

## Why This Architecture

This architecture was chosen for a few practical reasons.

### 1. Asynchronous processing keeps the API responsive

Document extraction, chunking, and embedding are not lightweight operations. Running that work inside the request cycle would make uploads slow and fragile. Offloading processing to Celery keeps the upload endpoint fast and makes the system easier to scale later.

### 2. Layered boundaries keep the code understandable

The codebase follows a simple layering pattern:

- API layer for HTTP request and response handling
- service layer for business logic
- repository layer for database access

That separation makes the project easier to reason about and easier to extend. For example, a change in storage logic should not require rewriting request handlers.

### 3. FAISS keeps vector search local and reproducible

FAISS was chosen because it is fast, simple to run locally, and does not require an external managed vector database. That makes the project reviewer-friendly and easy to debug.

This project uses `IndexFlatL2`, which keeps search behavior simple and exact for the current scale.

### 4. Grounded answering is more important than fluent guessing

The system does not treat the LLM as the source of truth. The LLM is used only after retrieval, and the prompt explicitly tells it to answer only from the provided context. If the answer is not supported by the retrieved chunks, the system returns a no-answer fallback instead of improvising.

### 5. Conversations improve the product experience

Single-turn question answering works, but follow-up questions make the product feel much closer to a real assistant. Conversation history is persisted so that follow-up queries can reuse recent context.

## Why This API Design

The API is intentionally resource-oriented and predictable.

### Resource groups

- `/documents` handles upload and status
- `/chat` handles retrieval and question answering
- `/conversations` handles chat session persistence
- `/health` handles service checks

### Design choices behind the API

- Upload and processing status are separated, because document readiness is asynchronous.
- Retrieval and final answering are separated, because retrieval is useful to inspect independently while debugging.
- Conversations are explicit resources rather than hidden session state.
- Status values are visible through the API, which makes background work observable.

This design keeps the interface easy to understand from the outside and easy to evolve from the inside.

## Tech Stack

| Layer | Technology | Why it was chosen |
|---|---|---|
| API | FastAPI | Simple, fast, strong typing, good docs support |
| Database | PostgreSQL | Reliable relational storage for application state |
| ORM | SQLAlchemy | Clear model layer and flexible DB access |
| Queue / Broker | Redis | Lightweight and a natural fit with Celery |
| Background jobs | Celery | Reliable async task handling |
| Embeddings | sentence-transformers | Strong local semantic embeddings with minimal setup |
| Vector store | FAISS | Fast local vector search without extra infrastructure |
| LLM integration | Ollama-compatible hosted endpoint | Keeps the system easy to run without local model installation |
| Containerization | Docker / Docker Compose | Reproducible local startup |

## Project Structure

```text
app/
  api/            HTTP routes and dependencies
  core/           config, constants, logging
  db/             SQLAlchemy base, session, models
  prompts/        prompt templates
  repositories/   DB access layer
  schemas/        request/response models
  services/       business logic
  utils/          file helpers
  workers/        Celery app and tasks

scripts/          startup, DB init, FAISS rebuild, smoke helpers
sample_docs/      example documents for testing
storage/          uploads and FAISS files
```

## API List

### Root

```text
GET /
```

Returns a simple service message.

### Health

```text
GET /api/v1/health/
GET /api/v1/health/ready
```

Used for service health and readiness checks.

### Documents

```text
POST /api/v1/documents/upload
GET  /api/v1/documents/{document_id}
```

`upload` accepts PDF or DOCX files and creates a processing job.  
`{document_id}` returns current document status such as `uploaded`, `processing`, `ready`, or `failed`.

### Chat

```text
POST /api/v1/chat/retrieve
POST /api/v1/chat/ask
```

`retrieve` is a debug-friendly retrieval endpoint that returns the top chunks.  
`ask` performs retrieval + prompt building + LLM answer generation.

### Conversations

```text
POST /api/v1/conversations/
GET  /api/v1/conversations/{conversation_id}
```

Creates and reads conversation sessions along with their stored messages.

## API Request and Response Design

### Upload response

The upload endpoint returns document metadata immediately, even though background processing may still be pending.

Example:

```json
{
  "id": "document-uuid",
  "file_name": "stored-file.docx",
  "original_name": "employee_policy.docx",
  "file_type": "docx",
  "status": "uploaded",
  "error_message": null,
  "created_at": "2026-04-24T..."
}
```

### Chat response

The chat endpoint returns both the answer and the citations used to support it.

Example:

```json
{
  "conversation_id": "conversation-uuid",
  "answer": "Employees are entitled to 12 casual leave days per year.",
  "citations": [
    {
      "chunk_id": "chunk-uuid",
      "document_id": "document-uuid",
      "chunk_index": 0
    }
  ]
}
```

### No-answer behavior

If the system cannot find reliable support in the retrieved chunks, it returns:

```text
I couldn't find a reliable answer in the uploaded documents.
```

This behavior is intentional and is part of the trust model of the system.

## Environment Variables

The default Docker path uses the values in `.env.example`.

```env
ENV=dev

DATABASE_URL=postgresql://user:password@postgres:5432/smartdocqa
REDIS_URL=redis://redis:6379/0

LLM_PROVIDER=ollama
OPENAI_API_KEY=
OLLAMA_BASE_URL=https://ollama.merai.app
OLLAMA_MODEL=llama3

UPLOAD_DIR=storage/uploads
FAISS_INDEX_DIR=storage/faiss

MAX_FILE_SIZE_MB=10

CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
```

Important note: the default setup uses a hosted Ollama-compatible endpoint. No local Ollama install or model pull is required for the normal Docker path.

## How to Run

### Recommended: Docker Compose

This is the easiest and most reliable way to run the project.

#### 1. Clone the repository

```bash
git clone https://github.com/Rehan018/smart-doc-qa.git
cd smart-doc-qa
```

#### 2. Create the environment file

```bash
cp .env.example .env
```

#### 3. Start the stack

```bash
docker compose up --build
```

This starts:

- FastAPI API
- Celery worker
- PostgreSQL
- Redis

#### 4. Open the API docs

```text
http://localhost:8000/docs
```

### Included sample documents

The repository includes sample documents that can be used immediately:

- `sample_docs/employee_policy.docx`
- `sample_docs/recruitment_process.docx`

### What to expect on first run

The first processing and retrieval requests may be slower because the embedding model is downloaded and initialized inside the containers.

## How to Build

### Build images only

```bash
docker compose build
```

### Build and run together

```bash
docker compose up --build
```

### Rebuild after code changes

```bash
docker compose up --build
```

## How to Execute Without Docker

Docker is the recommended path, but the project can also be run manually if PostgreSQL and Redis are already available.

### 1. Create and activate a virtual environment

```bash
python -m venv venv
source venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure `.env`

For non-Docker local execution, update `.env` to point to your local PostgreSQL and Redis instances. For example:

```env
DATABASE_URL=postgresql://user:password@localhost:5432/smartdocqa
REDIS_URL=redis://localhost:6379/0
OLLAMA_BASE_URL=https://ollama.merai.app
```

Use the actual host and port values from your machine.

### 4. Initialize the database

```bash
python scripts/init_db.py
```

### 5. Run the API

```bash
uvicorn app.main:app --reload
```

### 6. Run the worker in another terminal

```bash
./scripts/run_worker.sh
```

## Example Usage

### Health check

```bash
curl http://localhost:8000/api/v1/health/
```

### Upload a document

```bash
curl -X POST "http://localhost:8000/api/v1/documents/upload" \
  -F "file=@sample_docs/employee_policy.docx"
```

### Check document status

```bash
curl http://localhost:8000/api/v1/documents/<document_id>
```

Document status moves through:

```text
uploaded -> processing -> ready
```

### Retrieve relevant chunks

```bash
curl -X POST "http://localhost:8000/api/v1/chat/retrieve" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "leave policy",
    "document_ids": ["<document_id>"],
    "top_k": 3
  }'
```

### Ask a question

```bash
curl -X POST "http://localhost:8000/api/v1/chat/ask" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "How many casual leave days are allowed?",
    "document_ids": ["<document_id>"],
    "top_k": 3
  }'
```

### Create a conversation

```bash
curl -X POST "http://localhost:8000/api/v1/conversations/" \
  -H "Content-Type: application/json" \
  -d '{"title": "Policy questions"}'
```

### Ask a follow-up question

```bash
curl -X POST "http://localhost:8000/api/v1/chat/ask" \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": "<conversation_id>",
    "question": "What about maternity leave?",
    "document_ids": ["<document_id>"],
    "top_k": 3
  }'
```

## Testing

### Lightweight test suite

```bash
source venv/bin/activate
pytest
```

### Bytecode compile check

```bash
source venv/bin/activate
python -m compileall app scripts
```

### Docker smoke run

```bash
docker compose up --build
```

There is also a small helper:

```bash
./scripts/smoke_test.sh
```

## Deployment Guidance

This repository is primarily designed for local execution and evaluation through Docker Compose.

There is no public deployment URL included in the repository today. For review, the recommended path is to run the stack locally.

If this service were deployed, the deployment would typically require:

- one API container
- one worker container
- PostgreSQL
- Redis
- persistent storage for uploaded files
- persistent storage for FAISS index files
- a configured Ollama-compatible or OpenAI-compatible LLM endpoint

Platforms that could host this layout include:

- Render
- Railway
- Fly.io
- a VM or Kubernetes environment

### Deployment considerations

- uploads and FAISS files need persistent volumes
- API and worker must share storage
- background workers should scale independently from the API
- secrets and endpoint URLs must come from environment variables
- health endpoints should be wired into deployment checks

## Maintenance

### Rebuild FAISS index

If the FAISS index becomes inconsistent with the chunks stored in PostgreSQL, rebuild it with:

```bash
python scripts/rebuild_faiss.py
```

Inside Docker:

```bash
docker compose exec api python scripts/rebuild_faiss.py
```

This regenerates embeddings from stored chunks and recreates the FAISS index metadata mapping.

## Debugging

Check API logs:

```bash
docker compose logs -f api
```

Check worker logs:

```bash
docker compose logs -f worker
```

Check Redis:

```bash
docker compose logs redis
```

Check Postgres:

```bash
docker compose logs postgres
```

## Limitations

- scanned PDFs without OCR may fail because the current extractor expects a text layer
- retrieval is dense semantic search only; there is no hybrid search or BM25 fallback yet
- FAISS filtering by `document_id` happens after vector search
- old FAISS vectors are not automatically removed during document reprocessing
- no authentication or user isolation is implemented yet
- embedding model load can make the first retrieval request slower
- answer quality still depends on the configured LLM endpoint and model

## Future Improvements

- OCR support for scanned PDFs
- hybrid retrieval with semantic + keyword search
- reranking after retrieval
- streaming answers
- document deletion and cleanup
- stronger integration tests in CI
- Alembic migrations for schema evolution
- per-document or metadata-aware vector filtering
- authentication and user-level isolation

## Why This Project Matters

A lot of document-question-answering demos stop at "the model said something plausible." This project tries to go one step further.

The system is structured to be:

- grounded rather than freeform
- asynchronous rather than blocking
- modular rather than tangled
- reproducible rather than environment-sensitive
- debuggable rather than opaque

That makes it a better fit for real engineering discussion, because the interesting part is not only the LLM call. The interesting part is how the whole system behaves around the LLM.
