import logging
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.embedding_client import MODEL_NAME, encode
from app.db.session import SessionLocal
from app.models.document import Document
from app.models.document_embedding import DocumentEmbedding

logger = logging.getLogger(__name__)


def _embedding_text(document: Document) -> str:
    return f"{document.title}\n{document.description or ''}".strip()


def embed_document_sync(document_id: uuid.UUID) -> None:
    """Runs in a FastAPI BackgroundTask (its own DB session, own thread) after a
    document is created or gets a new version, so the upload response never blocks
    on model inference.

    Best-effort: embedding failures (model not downloaded yet, OOM, etc.) are logged
    and swallowed rather than raised, since search staying keyword-only in the
    meantime is preferable to breaking the upload itself.
    """
    db = SessionLocal()
    try:
        document = db.get(Document, document_id)
        if not document or document.is_deleted:
            return

        text = _embedding_text(document)
        if not text:
            return

        vector = encode([text])[0].tolist()

        existing = db.get(DocumentEmbedding, document_id)
        if existing:
            existing.embedding = vector
            existing.model_version = MODEL_NAME
        else:
            db.add(DocumentEmbedding(document_id=document_id, embedding=vector, model_version=MODEL_NAME))
        db.commit()
    except Exception:
        logger.exception("Failed to embed document %s", document_id)
        db.rollback()
    finally:
        db.close()


def semantic_search(db: Session, organization_id: uuid.UUID, query: str, limit: int = 20) -> list[tuple[uuid.UUID, float]]:
    """Returns [(document_id, cosine_distance)], closest first. Lower distance = more similar."""
    query_vector = encode([query])[0].tolist()

    stmt = (
        select(DocumentEmbedding.document_id, DocumentEmbedding.embedding.cosine_distance(query_vector).label("distance"))
        .join(Document, Document.id == DocumentEmbedding.document_id)
        .where(Document.organization_id == organization_id, Document.is_deleted.is_(False))
        .order_by("distance")
        .limit(limit)
    )
    return [(row[0], row[1]) for row in db.execute(stmt).all()]
