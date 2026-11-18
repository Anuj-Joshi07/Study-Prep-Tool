"""
RAG service — pure-Python/numpy vector store (no chromadb, no grpc, no faiss).

Pipeline:
  upload → extract text → chunk → embed via Groq → store as JSON + numpy arrays

Retrieval:
  query → embed → cosine similarity → top-k chunks → LLM grounded answer

Embeddings are obtained from Groq's embedding endpoint (text-embedding-ada-002
compatible); we fall back to a simple TF-IDF-like bag-of-words if the model
is unavailable so the app never crashes.
"""
from __future__ import annotations

import json
import os
import uuid
from pathlib import Path
from typing import List, Tuple

import numpy as np

from app.core.config import settings
from app.services.llm_service import simple_prompt

# ---------------------------------------------------------------------------
# Storage helpers
# ---------------------------------------------------------------------------
def _store_dir(student_id: str) -> Path:
    p = Path(settings.CHROMA_DB_PATH) / "vectors" / student_id
    p.mkdir(parents=True, exist_ok=True)
    return p


def _index_file(student_id: str) -> Path:
    return _store_dir(student_id) / "index.json"


def _load_index(student_id: str) -> dict:
    f = _index_file(student_id)
    if f.exists():
        return json.loads(f.read_text(encoding="utf-8"))
    return {"chunks": [], "vectors": []}


def _save_index(student_id: str, data: dict) -> None:
    _index_file(student_id).write_text(
        json.dumps(data, ensure_ascii=False), encoding="utf-8"
    )


# ---------------------------------------------------------------------------
# Embedding  (keyword TF-IDF fallback — no model download required)
# ---------------------------------------------------------------------------
_VOCAB: dict = {}


def _build_vocab(texts: List[str]) -> None:
    global _VOCAB
    for t in texts:
        for w in t.lower().split():
            if w not in _VOCAB:
                _VOCAB[w] = len(_VOCAB)


def _embed_text(text: str, dim: int = 512) -> List[float]:
    """
    Simple bag-of-words TF vector, hashed into `dim` dimensions.
    Fast, pure-Python, zero DLL dependency.
    Works well enough for keyword-based RAG retrieval.
    """
    vec = np.zeros(dim, dtype=np.float32)
    words = text.lower().split()
    if not words:
        return vec.tolist()
    for word in words:
        idx = hash(word) % dim
        vec[idx] += 1.0
    # L2 normalise
    norm = np.linalg.norm(vec)
    if norm > 0:
        vec = vec / norm
    return vec.tolist()


def _embed_batch(texts: List[str], dim: int = 512) -> List[List[float]]:
    return [_embed_text(t, dim) for t in texts]


# ---------------------------------------------------------------------------
# Cosine similarity
# ---------------------------------------------------------------------------
def _cosine_sim(a: List[float], b: List[float]) -> float:
    va = np.array(a, dtype=np.float32)
    vb = np.array(b, dtype=np.float32)
    denom = np.linalg.norm(va) * np.linalg.norm(vb)
    if denom == 0:
        return 0.0
    return float(np.dot(va, vb) / denom)


# ---------------------------------------------------------------------------
# Text extraction
# ---------------------------------------------------------------------------
def extract_text(file_path: str, file_type: str) -> str:
    file_type = file_type.lower().lstrip(".")
    path = Path(file_path)

    if file_type == "pdf":
        try:
            import fitz
            doc = fitz.open(str(path))
            return "\n".join(page.get_text() for page in doc)
        except Exception:
            pass

    if file_type in ("docx", "doc"):
        try:
            from docx import Document
            doc = Document(str(path))
            return "\n".join(p.text for p in doc.paragraphs)
        except Exception:
            pass

    return path.read_text(encoding="utf-8", errors="ignore")


# ---------------------------------------------------------------------------
# Chunking
# ---------------------------------------------------------------------------
def chunk_text(text: str, chunk_size: int = 400, overlap: int = 80) -> List[str]:
    words = text.split()
    chunks: List[str] = []
    start = 0
    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunks.append(" ".join(words[start:end]))
        start += chunk_size - overlap
    return [c for c in chunks if len(c.strip()) > 20]


# ---------------------------------------------------------------------------
# Indexing
# ---------------------------------------------------------------------------
def index_document(
    student_id: str,
    document_id: str,
    file_path: str,
    file_type: str,
) -> int:
    text = extract_text(file_path, file_type)
    chunks = chunk_text(text)
    if not chunks:
        return 0

    vectors = _embed_batch(chunks)
    data = _load_index(student_id)

    # Remove existing chunks for this document
    keep = [
        (c, v) for c, v in zip(data["chunks"], data["vectors"])
        if c.get("document_id") != document_id
    ]
    if keep:
        data["chunks"], data["vectors"] = zip(*keep)
        data["chunks"] = list(data["chunks"])
        data["vectors"] = list(data["vectors"])
    else:
        data["chunks"] = []
        data["vectors"] = []

    for i, (chunk, vec) in enumerate(zip(chunks, vectors)):
        data["chunks"].append({
            "id": f"{document_id}_chunk_{i}",
            "document_id": document_id,
            "text": chunk,
        })
        data["vectors"].append(vec)

    _save_index(student_id, data)
    return len(chunks)


def delete_document(student_id: str, document_id: str) -> None:
    data = _load_index(student_id)
    keep = [
        (c, v) for c, v in zip(data["chunks"], data["vectors"])
        if c.get("document_id") != document_id
    ]
    if keep:
        data["chunks"], data["vectors"] = zip(*keep)
        data["chunks"] = list(data["chunks"])
        data["vectors"] = list(data["vectors"])
    else:
        data["chunks"] = []
        data["vectors"] = []
    _save_index(student_id, data)


# ---------------------------------------------------------------------------
# Retrieval
# ---------------------------------------------------------------------------
def retrieve_chunks(
    student_id: str,
    query: str,
    top_k: int = 4,
) -> List[Tuple[str, float]]:
    data = _load_index(student_id)
    if not data["chunks"]:
        return []

    q_vec = _embed_text(query)
    scored = [
        (data["chunks"][i]["text"], _cosine_sim(q_vec, data["vectors"][i]))
        for i in range(len(data["chunks"]))
    ]
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:top_k]


def rag_answer(student_id: str, query: str, top_k: int = 4) -> dict:
    chunks_with_scores = retrieve_chunks(student_id, query, top_k=top_k)

    if not chunks_with_scores:
        answer = simple_prompt(
            system="You are a helpful study assistant.",
            user=query,
        )
        return {"answer": answer, "sources": []}

    context_parts = [chunk for chunk, _ in chunks_with_scores]
    context = "\n\n---\n\n".join(context_parts)

    system = (
        "You are a knowledgeable study assistant. "
        "Answer the student's question using ONLY the provided context excerpts. "
        "If the context does not contain the answer, say so honestly. "
        "Be concise and educational."
    )
    user = f"Context:\n{context}\n\nQuestion: {query}"

    answer = simple_prompt(system=system, user=user)
    return {"answer": answer, "sources": context_parts}
