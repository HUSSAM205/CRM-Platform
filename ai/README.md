# AI / Data Layer

PyTorch-backed embedding module and Jupyter notebooks for the platform's semantic document search feature (implemented in Phase 5).

- `ai_core/embeddings.py` — shared `encode(texts) -> np.ndarray` function, imported both by notebooks here and by the FastAPI backend (`backend/app/ai/embedding_client.py`), so the prototyped code is the exact code that runs in production.
- `notebooks/` — experimentation: loading the model, evaluating candidate models, testing similarity ranking on sample documents.

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
jupyter notebook notebooks/
```
