"""Shared PyTorch embedding module.

Used by both the Jupyter prototyping notebooks (ai/notebooks/) and the FastAPI
backend (backend/app/ai/embedding_client.py), so there is a single code path
between experimentation and production - no drift between what was prototyped
and what actually runs.
"""

import threading

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

_model = None
_model_lock = threading.Lock()


def _get_model():
    # The backend calls encode() from multiple FastAPI BackgroundTasks threads (one per
    # document upload), which can race on first load: two threads both see _model as
    # None and start constructing a SentenceTransformer concurrently, corrupting a
    # partially-initialized torch module ("meta tensor" errors). Double-checked locking
    # keeps the (fast) common case lock-free after the first load.
    global _model
    if _model is None:
        with _model_lock:
            if _model is None:
                from sentence_transformers import SentenceTransformer

                _model = SentenceTransformer(MODEL_NAME)
    return _model


def encode(texts: list[str]):
    """Encode a list of strings into embedding vectors (numpy array, shape [len(texts), 384])."""
    model = _get_model()
    return model.encode(texts, normalize_embeddings=True)
