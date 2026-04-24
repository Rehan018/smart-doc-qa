import json
import os
from pathlib import Path

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
        self.index_dir = Path(settings.FAISS_INDEX_DIR)
        self.index_path = self.index_dir / "index.faiss"
        self.meta_path = self.index_dir / "index_meta.json"

        self._load_or_create()

    def _load_or_create(self):
        self.index_dir.mkdir(parents=True, exist_ok=True)

        index_exists = self.index_path.exists()
        meta_exists = self.meta_path.exists()

        if index_exists and meta_exists:
            self.index = faiss.read_index(str(self.index_path))
            with open(self.meta_path, "r", encoding="utf-8") as f:
                self.metadata = json.load(f)

            if self.index.ntotal != len(self.metadata):
                raise RuntimeError(
                    "FAISS index and metadata are out of sync. "
                    "Run: python scripts/rebuild_faiss.py"
                )

            return

        if index_exists != meta_exists:
            raise RuntimeError(
                "FAISS index files are incomplete. "
                "Run: python scripts/rebuild_faiss.py"
            )

        self.index = faiss.IndexFlatL2(self.dim)
        self.metadata = []
        self._save()

    def add_embeddings(self, embeddings: np.ndarray, chunk_ids):
        if embeddings.ndim != 2:
            raise ValueError("Embeddings must be a 2D array.")

        if embeddings.shape[1] != self.dim:
            raise ValueError(
                f"Embedding dimension mismatch. Expected {self.dim}, got {embeddings.shape[1]}."
            )

        if len(chunk_ids) != embeddings.shape[0]:
            raise ValueError("Number of chunk IDs must match number of embeddings.")

        self.index.add(embeddings.astype("float32"))

        self.metadata.extend(str(chunk_id) for chunk_id in chunk_ids)

        self._save()

    def search(self, query_embedding, top_k=5):
        if self.index.ntotal == 0:
            return []

        if query_embedding.ndim != 2:
            raise ValueError("Query embedding must be a 2D array.")

        if query_embedding.shape[1] != self.dim:
            raise ValueError(
                f"Query embedding dimension mismatch. Expected {self.dim}, got {query_embedding.shape[1]}."
            )

        distances, indices = self.index.search(query_embedding.astype("float32"), top_k)

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

    def reset(self):
        self.index = faiss.IndexFlatL2(self.dim)
        self.metadata = []
        self._save()

    def _save(self):
        faiss.write_index(self.index, str(self.index_path))

        tmp_meta_path = self.meta_path.with_suffix(".json.tmp")
        with open(tmp_meta_path, "w", encoding="utf-8") as f:
            json.dump(self.metadata, f)

        os.replace(tmp_meta_path, self.meta_path)
