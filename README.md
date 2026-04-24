# Smart Document Q&A

Smart Document Q&A is a backend system for uploading PDF and DOCX documents, processing them asynchronously, indexing their content, and answering user questions using retrieval-augmented generation.

The system supports document upload, background processing, chunking, embeddings, FAISS-based retrieval, grounded LLM answers, citations, and multi-turn conversations.

## Features

- Upload PDF and DOCX documents
- Background processing with Celery and Redis
- Text extraction from PDF and DOCX
- Paragraph-aware chunking with overlap
- Local embeddings using sentence-transformers
- FAISS vector search
- Grounded Q&A using retrieved document chunks
- Ollama-compatible hosted LLM support
- Conversation history and follow-up questions
- Basic no-answer fallback to reduce hallucination
- Docker Compose setup for local execution

## Tech Stack

- FastAPI
- PostgreSQL
- Redis
- Celery
- SQLAlchemy
- FAISS
- sentence-transformers
- Ollama-compatible hosted endpoint
- Docker Compose

## Architecture

```text
User
  |
  | upload document
  v
FastAPI API
  |
  | save file + metadata
  v
PostgreSQL
  |
  | enqueue job
  v
Redis + Celery Worker
  |
  | extract text
  | chunk text
  | generate embeddings
  | store vectors
  v
FAISS Index + Chunk DB
  |
  | ask question
  v
Retrieval Service
  |
  | top-k chunks
  v
LLM Service
  |
  | grounded answer
  v
API Response with citations
```

## Local Setup

### 1. Clone the repo

```bash
git clone https://github.com/Rehan018/smart-doc-qa.git
cd smart-doc-qa
```

### 2. Create the environment file

```bash
cp .env.example .env
```

Default Docker values:

```env
DATABASE_URL=postgresql://user:password@postgres:5432/smartdocqa
REDIS_URL=redis://redis:6379/0
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=https://ollama.merai.app
OLLAMA_MODEL=llama3
```

### 3. Hosted Ollama endpoint

The default setup uses a hosted Ollama-compatible endpoint:

```text
https://ollama.merai.app
```

No local Ollama install or model download is required for the default setup. If you want to switch to a different Ollama-compatible endpoint later, update `OLLAMA_BASE_URL` and `OLLAMA_MODEL` in `.env`.

### 4. Start the system

```bash
docker compose up --build
```

API:

```text
http://localhost:8000
```

Swagger docs:

```text
http://localhost:8000/docs
```

Included sample documents:

- `sample_docs/employee_policy.docx`
- `sample_docs/recruitment_process.docx`

Note: the first end-to-end processing run may take a bit longer because the sentence-transformers embedding model is downloaded into the containers. The first chat request can also be slower for the same reason.

## API Examples

### Health check

```bash
curl http://localhost:8000/api/v1/health/
```

### Upload document

```bash
curl -X POST "http://localhost:8000/api/v1/documents/upload" \
  -F "file=@sample_docs/employee_policy.docx"
```

Example response:

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

### Check document status

```bash
curl http://localhost:8000/api/v1/documents/<document_id>
```

Status flow:

```text
uploaded -> processing -> ready
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

### Create conversation

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

## Design Choices

### Why background processing?

Document parsing, chunking, embedding, and indexing can be slow for large files. Upload stays fast while Celery handles the heavier processing work.

### Why FAISS?

FAISS is lightweight, fast, and easy to run locally. It avoids requiring a hosted vector database for a take-home assignment.

### Why Ollama?

Using a hosted Ollama-compatible endpoint keeps the project easy to run without requiring local LLM setup. The LLM layer is provider-based, so another provider can be added behind the same interface later.

### Why chunk overlap?

Chunk overlap helps preserve context across chunk boundaries. Without overlap, relevant information can be split and retrieval quality drops.

### How hallucination is reduced

The LLM receives only retrieved chunks as context. The prompt instructs it to answer only from that context and return a no-answer response when the answer is not supported.

## Known Limitations

- Scanned PDFs without OCR may fail because the current extractor expects a text layer.
- FAISS metadata filtering is handled after vector search. For larger datasets, per-document indexes or metadata-aware vector storage would be better.
- Old FAISS vectors are not automatically deleted if a document is reprocessed. A rebuild script can handle this.
- Ollama output quality depends on the configured hosted model.
- No authentication is implemented in this version.

## Future Improvements

- Add OCR for scanned PDFs
- Add Alembic migrations instead of direct table creation
- Add a FAISS rebuild command
- Add a document deletion API
- Add authentication and user-level document isolation
- Add reranking for better retrieval quality
- Add streaming answers
- Add automated tests in CI

## Testing Notes

This repository includes lightweight smoke and unit tests for health endpoints, upload validation, extraction, chunking, and stable constants.

Full integration coverage still runs best through Docker because the end-to-end document pipeline depends on PostgreSQL, Redis, Celery, FAISS, and the hosted Ollama-compatible endpoint.

## Maintenance

### Rebuild FAISS index

If the vector index becomes inconsistent or documents are reprocessed:

```bash
python scripts/rebuild_faiss.py
```

This regenerates embeddings from stored chunks and rebuilds the FAISS index.

## Debugging

- Check API logs:

```bash
docker compose logs -f api
```

- Check worker logs:

```bash
docker compose logs -f worker
```

- Verify Redis:

```bash
docker compose logs redis
```

- Verify Postgres:

```bash
docker compose logs postgres
```

## Notes for Reviewer

- The system is designed to run locally with Docker Compose.
- The default LLM configuration uses a hosted Ollama-compatible endpoint for reproducibility without local model setup.
- The LLM layer is pluggable and can be switched to OpenAI through environment variables.
- Background processing keeps uploads responsive while extraction, chunking, embeddings, and indexing run asynchronously.
- Retrieval uses chunk overlap and distance filtering to reduce weak matches and lower hallucination risk.
