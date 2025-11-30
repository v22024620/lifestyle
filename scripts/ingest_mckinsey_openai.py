"""Ingest McKinsey PDFs using OpenAI embeddings into Chroma."""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Dict, List

from openai import OpenAI
import chromadb

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(BASE_DIR))

from app.config import get_settings

CHUNK_SIZE = 800
CHUNK_OVERLAP = 150
BATCH_SIZE = 16
EMBED_MODEL = "text-embedding-3-large"
PDF_DIR = BASE_DIR / "Mckinsey"


def load_pdf_text(path: Path) -> str:
    from PyPDF2 import PdfReader

    reader = PdfReader(str(path))
    texts: List[str] = []
    for page in reader.pages:
        texts.append(page.extract_text() or "")
    return "\n".join(texts)


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
    tokens = text.split()
    chunks: List[str] = []
    start = 0
    while start < len(tokens):
        end = min(len(tokens), start + chunk_size)
        chunk = " ".join(tokens[start:end]).strip()
        if chunk:
            chunks.append(chunk)
        if end == len(tokens):
            break
        start = max(end - overlap, 0)
    return chunks


def embed_chunks(client: OpenAI, chunks: List[str]) -> List[List[float]]:
    embeddings: List[List[float]] = []
    for idx in range(0, len(chunks), BATCH_SIZE):
        batch = chunks[idx : idx + BATCH_SIZE]
        response = client.embeddings.create(model=EMBED_MODEL, input=batch)
        embeddings.extend([item.embedding for item in response.data])
    return embeddings


def main() -> None:
    settings = get_settings()
    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY missing; set it in .env or environment")
    pdf_files = sorted(PDF_DIR.glob("*.pdf"))
    if not pdf_files:
        raise RuntimeError("No PDF files found under Mckinsey/ directory")
    chroma_client = chromadb.PersistentClient(path=str(settings.chroma_path))
    collection = chroma_client.get_or_create_collection(
        name="mckinsey-openai",
        metadata={"hnsw:space": "cosine"},
    )
    client = OpenAI(api_key=settings.openai_api_key)

    total_chunks = 0
    for pdf in pdf_files:
        text = load_pdf_text(pdf)
        chunks = chunk_text(text)
        if not chunks:
            continue
        embeddings = embed_chunks(client, chunks)
        ids = [f"openai-{pdf.stem}-{idx}" for idx in range(len(chunks))]
        metadatas: List[Dict[str, str]] = [
            {
                "source": str(pdf),
                "title": pdf.stem.replace("-", " "),
                "chunk_index": str(idx),
                "total_chunks": str(len(chunks)),
            }
            for idx in range(len(chunks))
        ]
        collection.upsert(ids=ids, embeddings=embeddings, documents=chunks, metadatas=metadatas)
        total_chunks += len(chunks)
        print(f"Embedded {pdf.name}: {len(chunks)} chunks")
    print(f"Stored {total_chunks} chunks using OpenAI embeddings in Chroma collection 'mckinsey-openai'")


if __name__ == "__main__":
    main()
