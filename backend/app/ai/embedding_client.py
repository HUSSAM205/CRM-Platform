"""Thin bridge to the shared `ai` package (../../ai/ai_core) so the backend and the
Jupyter notebooks in ai/notebooks/ run the exact same embedding code - no separate
reimplementation to drift out of sync with what was prototyped.
"""

import sys
from pathlib import Path

_AI_PACKAGE_DIR = Path(__file__).resolve().parents[3] / "ai"
if str(_AI_PACKAGE_DIR) not in sys.path:
    sys.path.insert(0, str(_AI_PACKAGE_DIR))

from ai_core.embeddings import MODEL_NAME, encode  # noqa: E402

__all__ = ["MODEL_NAME", "encode"]
