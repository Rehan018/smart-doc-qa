import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.db.models.chunk import Chunk
from app.db.session import SessionLocal
from app.services.embedding_service import EmbeddingService
from app.services.vector_service import VectorService


def rebuild():
    db = SessionLocal()

    try:
        chunks = db.query(Chunk).order_by(Chunk.created_at).all()

        if not chunks:
            print("No chunks found. Nothing to rebuild.")
            return

        embedding_service = EmbeddingService()

        texts = [chunk.text for chunk in chunks]
        chunk_ids = [chunk.id for chunk in chunks]

        embeddings = embedding_service.embed_texts(texts)

        vector_service = VectorService(dim=embeddings.shape[1])
        vector_service.index.reset()
        vector_service.metadata = []
        vector_service.add_embeddings(embeddings, chunk_ids)

        print(f"Rebuilt FAISS index with {len(chunk_ids)} chunks.")
    finally:
        db.close()


if __name__ == "__main__":
    rebuild()
