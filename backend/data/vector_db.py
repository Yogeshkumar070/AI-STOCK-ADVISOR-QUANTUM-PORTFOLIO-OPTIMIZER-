from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Iterable

import chromadb


BASE_DIR = Path(__file__).resolve().parents[1]
CHROMA_DIR = BASE_DIR / "chroma_data"
CHROMA_DIR.mkdir(parents=True, exist_ok=True)

try:
    chroma_client = chromadb.PersistentClient(path=str(CHROMA_DIR))
except Exception:
    chroma_client = chromadb.EphemeralClient()


class SimpleHashEmbeddingFunction:
    """Local deterministic embedding fallback that avoids external model downloads."""

    def name(self) -> str:
        return "simple-hash-embedding"

    def __call__(self, input: Iterable[str]) -> list[list[float]]:
        embeddings = []
        for text in input:
            digest = hashlib.sha256(text.encode("utf-8")).digest()
            embeddings.append([(byte / 255.0) for byte in digest])
        return embeddings


collection = chroma_client.get_or_create_collection(
    name="nifty50_transcripts",
    embedding_function=SimpleHashEmbeddingFunction(),
)


def seed_test_data(ticker: str) -> bool:
    """Inject dummy promises so the audit math can be tested before transcript scraping exists."""
    normalized = ticker.upper().replace(".NS", "")
    chunks = [
        "We expect totalRevenue to grow by 25% by 2022.",
        "We target a 15% increase in totalRevenue for 2023.",
        "Our operatingMargins should expand by 20% in 2024.",
    ]
    ids = [f"{normalized}_test_{index}" for index in range(len(chunks))]
    metadatas = [{"ticker": normalized, "year": 2020 + index} for index in range(len(chunks))]

    existing_ids = set(collection.get(ids=ids).get("ids", []))
    pending_docs = []
    pending_ids = []
    pending_meta = []

    for doc_id, chunk, metadata in zip(ids, chunks, metadatas):
        if doc_id not in existing_ids:
            pending_docs.append(chunk)
            pending_ids.append(doc_id)
            pending_meta.append(metadata)

    if pending_ids:
        collection.add(documents=pending_docs, metadatas=pending_meta, ids=pending_ids)

    return True
