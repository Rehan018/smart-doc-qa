import os
import json
import faiss
import numpy as np

from app.core.config import settings


class VectorSearchResult:
    def __init__(self, chunk_id: str, distance: float):
        self.chunk_id = chunk_id
        self.distance = distance


class VectorService:
    def __init__(self, dim: int):
        self.dim = dim
        self.index_path = os.path.join(settings.FAISS_INDEX_DIR, "index.faiss")
        self.meta_path = os.path.join(settings.FAISS_INDEX_DIR, "index_meta.json")

        self._load_or_create()

    def _load_or_create(self):
        os.makedirs(settings.FAISS_INDEX_DIR, exist_ok=True)

        if os.path.exists(self.index_path):
            self.index = faiss.read_index(self.index_path)
            with open(self.meta_path, "r") as f:
                self.metadata = json.load(f)
        else:
            self.index = faiss.IndexFlatL2(self.dim)
            self.metadata = []

    def add_embeddings(self, embeddings: np.ndarray, chunk_ids):
        self.index.add(embeddings)

        for cid in chunk_ids:
            self.metadata.append(str(cid))

        self._save()

    def search(self, query_embedding, top_k=5):
        if self.index.ntotal == 0:
            return []

        distances, indices = self.index.search(query_embedding, top_k)

        results = []
        for distance, idx in zip(distances[0], indices[0]):
            if idx == -1:
                continue

            if idx < len(self.metadata):
                results.append(
                    VectorSearchResult(
                        chunk_id=self.metadata[idx],
                        distance=float(distance),
                    )
                )

        return results

    def _save(self):
        faiss.write_index(self.index, self.index_path)
        with open(self.meta_path, "w") as f:
            json.dump(self.metadata, f)
