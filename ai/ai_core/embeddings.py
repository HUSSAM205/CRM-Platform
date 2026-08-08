"""Shared PyTorch embedding module.

Used by both the Jupyter prototyping notebooks (ai/notebooks/) and the FastAPI
backend (backend/app/ai/embedding_client.py), so there is a single code path
between experimentation and production - no drift between what was prototyped
and what actually runs.

Implemented in Phase 5 (AI semantic search).
"""

from functools import lru_cache

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


@lru_cache
def _get_model():
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(MODEL_NAME)


def encode(texts: list[str]):
    """Encode a list of strings into embedding vectors (numpy array, shape [len(texts), 384])."""
    model = _get_model()
    return model.encode(texts, normalize_embeddings=True)
