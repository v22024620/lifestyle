"""Vector store service using Chroma with safe fallbacks."""
from __future__ import annotations

import hashlib
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

try:
    import chromadb  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    chromadb = None  # type: ignore
else:
    chromadb = None  # disable to avoid heavy dependency
    chromadb = None  # type: ignore


class _HashEmbeddingFunction:
    """Deterministic lightweight embedding to avoid network downloads."""

    def __init__(self, dimensions: int = 8):
        self.dimensions = dimensions

    @staticmethod
    def name() -> str:
        return "hash-embedding"

    @staticmethod
    def default_space() -> str:
        return "l2"

    @staticmethod
    def supported_spaces() -> list[str]:
        return ["l2", "cosine"]

    @staticmethod
    def is_legacy() -> bool:  # chroma inspects this attribute
        return False

    def get_config(self) -> dict:
        return {"name": self.name(), "dimensions": self.dimensions, "default_space": self.default_space()}

    def _hash(self, text: str) -> List[float]:
        digest = hashlib.sha256((text or "").encode("utf-8")).digest()
        step = max(1, len(digest) // self.dimensions)
        vec = [int.from_bytes(digest[i:i + step], "big") % 1000 / 1000 for i in range(0, len(digest), step)]
        return vec[: self.dimensions]

    def embed_documents(self, input: List[str]) -> List[List[float]]:
        return [self._hash(text) for text in input or []]

    def embed_query(self, input: str) -> List[float]:
        return self._hash(input or "")

    __call__ = embed_documents


class VectorService:
    """Handles vector embedding storage and retrieval."""

    def __init__(self, persist_path: str, collection_name: str = "documents"):
        self.persist_path = Path(persist_path)
        self.collection_name = collection_name
        self._client = None
        self._collection = None
        self._memory_docs: List[Dict[str, Any]] = []
        self._memory_store_path = self.persist_path / "memory_store.json"
        self.embedding_fn = _HashEmbeddingFunction()
        self._init_client()
        if not self._collection:
            self._load_memory_docs()

    def is_connected(self) -> bool:
        return self._collection is not None or bool(self._memory_docs)

    def _init_client(self) -> None:
        if not chromadb:
            logger.warning("chromadb not installed; using in-memory vectors")
            return
        try:
            self.persist_path.mkdir(parents=True, exist_ok=True)
            self._client = chromadb.PersistentClient(path=str(self.persist_path))
            self._collection = self._client.get_or_create_collection(
                name=self.collection_name,
                embedding_function=self.embedding_fn,
            )
        except Exception as err:  # pragma: no cover - env dependent
            logger.warning("Chroma init failed, falling back to memory: %s", err)
            self._client = None
            self._collection = None

    def _load_memory_docs(self) -> None:
        if not self._memory_store_path.exists():
            return
        try:
            self._memory_docs = json.loads(self._memory_store_path.read_text(encoding="utf-8"))
        except Exception as err:  # pragma: no cover - corrupted file
            logger.warning("Failed to load memory vector store: %s", err)
            self._memory_docs = []

    def _persist_memory_docs(self) -> None:
        try:
            self._memory_store_path.parent.mkdir(parents=True, exist_ok=True)
            self._memory_store_path.write_text(json.dumps(self._memory_docs), encoding="utf-8")
        except Exception as err:  # pragma: no cover - disk issues
            logger.warning("Failed to persist memory vector store: %s", err)

    def add_documents(self, docs: List[Dict[str, Any]]) -> None:
        """Ingest documents with embeddings."""
        if not docs:
            return
        contents = [doc.get("content", "") for doc in docs]
        metadatas = [doc.get("metadata", {}) for doc in docs]
        ids = [doc.get("id", f"doc-{idx}") for idx, doc in enumerate(docs)]
        if self._collection:
            try:
                self._collection.upsert(documents=contents, metadatas=metadatas, ids=ids)
                return
            except Exception as err:  # pragma: no cover - env dependent
                logger.warning("Chroma upsert failed, using memory fallback: %s", err)
        # simple memory store with on-disk persistence
        if not self._memory_docs:
            self._load_memory_docs()
        for doc_id, content, metadata in zip(ids, contents, metadatas):
            self._memory_docs.append({"id": doc_id, "content": content, "metadata": metadata})
        self._persist_memory_docs()

    def search(
        self,
        query: str,
        k: int = 5,
        metadata_filter: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Return vector search results from Chroma or memory fallback."""
        metadata_filter = metadata_filter or {}
        where_clause = metadata_filter if metadata_filter else None
        if self._collection:
            try:
                results = self._collection.query(query_texts=[query], n_results=k, where=where_clause)
                hits = []
                raw_ids = results.get("ids", [[]])[0]
                raw_docs = results.get("documents", [[]])[0]
                raw_meta = results.get("metadatas", [[]])[0]
                raw_dists = results.get("distances", [[]])[0]
                for idx in range(len(raw_docs)):
                    hits.append(
                        {
                            "id": raw_ids[idx],
                            "content": raw_docs[idx],
                            "metadata": raw_meta[idx],
                            "score": raw_dists[idx],
                        }
                    )
                return hits
            except Exception as err:  # pragma: no cover - env dependent
                logger.warning("Chroma query failed, using memory fallback: %s", err)
        # memory search via simple substring scoring
        if not self._memory_docs:
            self._load_memory_docs()
        hits: List[Dict[str, Any]] = []
        q = query.lower()
        for doc in self._memory_docs:
            if metadata_filter and not all(doc.get("metadata", {}).get(k) == v for k, v in metadata_filter.items()):
                continue
            score = 1.0 if q in (doc.get("content", "").lower()) else 0.0
            hits.append({
                "id": doc.get("id"),
                "content": doc.get("content"),
                "metadata": doc.get("metadata", {}),
                "score": score,
            })
        hits.sort(key=lambda h: h["score"], reverse=True)
        return hits[:k]

    def seed_from_rows(self, rows: List[Dict[str, Any]], content_key: str = "content") -> None:
        """Helper to ingest structured rows as docs."""
        docs = []
        for idx, row in enumerate(rows):
            docs.append({
                "id": row.get("id", f"seed-{idx}"),
                "content": row.get(content_key, ""),
                "metadata": {k: v for k, v in row.items() if k != content_key},
            })
        self.add_documents(docs)
