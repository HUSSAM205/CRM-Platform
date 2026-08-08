from fastapi import APIRouter
from sqlalchemy import text

from app.db.session import engine

router = APIRouter(tags=["health"])


@router.get("/health")
def liveness() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/health/ready")
def readiness() -> dict[str, str]:
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_status = "ok"
    except Exception as exc:  # noqa: BLE001 - readiness probe reports any failure
        db_status = f"error: {exc}"

    return {"status": "ok" if db_status == "ok" else "degraded", "database": db_status}
