"""Knowledge service for querying McKinsey vector store."""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class KnowledgeService:
    """Retrieves strategy snippets from Chroma or JSON fallback."""

    def __init__(
        self,
        chroma_path: str,
        collection_name: str = "mckinsey-openai",
        fallback_store: str | None = None,
    ):
        self.collection_name = collection_name
        self.chroma_path = Path(chroma_path)
        self.collection = None
        self._client = None
        self._fallback_docs: List[Dict[str, Any]] = []
        self._init_chroma()
        self._load_fallback_docs(fallback_store)

    def _init_chroma(self) -> None:
        try:
            import chromadb  # type: ignore

            self._client = chromadb.PersistentClient(path=str(self.chroma_path))
            self.collection = self._client.get_or_create_collection(name=self.collection_name, metadata={"hnsw:space": "cosine"})
        except Exception as err:  # pragma: no cover - optional dependency
            logger.warning("Chroma unavailable, falling back to JSON store: %s", err)
            self.collection = None

    def _load_fallback_docs(self, override_path: str | None) -> None:
        path = Path(override_path) if override_path else self.chroma_path / "memory_store.json"
        if not path.exists():
            return
        try:
            self._fallback_docs = json.loads(path.read_text(encoding="utf-8"))
        except Exception as err:  # pragma: no cover - corrupted file
            logger.warning("Failed to load fallback vector store: %s", err)
            self._fallback_docs = []

    def available(self) -> bool:
        return self.collection is not None or bool(self._fallback_docs)

    def search(
        self,
        query: Optional[str],
        *,
        hints: Optional[List[str]] = None,
        top_k: int = 4,
    ) -> List[Dict[str, Any]]:
        """Return list of relevant knowledge snippets."""

        search_text = " ".join(filter(None, [query or "", *(hints or [])])).strip()
        if not search_text:
            search_text = "agentic operations"

        if self.collection is not None:
            try:
                result = self.collection.query(query_texts=[search_text], n_results=top_k)
                docs = []
                ids = result.get("ids", [[]])[0]
                documents = result.get("documents", [[]])[0]
                metas = result.get("metadatas", [[]])[0]
                distances = result.get("distances", [[]])[0]
                for idx, doc_id in enumerate(ids):
                    meta = metas[idx] if idx < len(metas) else {}
                    docs.append(
                        {
                            "id": doc_id,
                            "title": meta.get("title") or Path(meta.get("source", "")).stem,
                            "snippet": documents[idx][:320],
                            "source": meta.get("source"),
                            "score": distances[idx] if idx < len(distances) else None,
                        }
                    )
                return docs
            except Exception as err:  # pragma: no cover - query edge cases
                logger.warning("Chroma query failed, using fallback search: %s", err)

        return self._fallback_search(search_text, top_k)

    def _fallback_search(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        if not self._fallback_docs:
            return []
        lowered = query.lower()
        scored: List[tuple[float, Dict[str, Any]]] = []
        for doc in self._fallback_docs:
            text = (doc.get("content") or "").lower()
            if not text:
                continue
            score = text.count(lowered) if lowered in text else 0
            if score == 0 and lowered not in text:
                continue
            meta = doc.get("metadata", {})
            scored.append(
                (
                    float(score) or 0.5,
                    {
                        "id": doc.get("id"),
                        "title": meta.get("title") or Path(meta.get("source", "")).stem,
                        "snippet": doc.get("content", "")[:320],
                        "source": meta.get("source"),
                        "score": score,
                    },
                )
            )
        scored.sort(key=lambda item: item[0], reverse=True)
        return [item[1] for item in scored[:top_k]]


__all__ = ["KnowledgeService"]
