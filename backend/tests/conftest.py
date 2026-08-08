"""Test isolation strategy: each test runs inside a SAVEPOINT on the real Neon
database (there's no local Postgres available in this environment - see
docs/architecture.md) and is rolled back afterward, so tests never leave data
behind or interfere with each other, without needing a separate test database.
"""

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import event
from sqlalchemy.orm import Session, sessionmaker

from app.core.rate_limit import limiter
from app.db.session import engine, get_db
from app.main import app


@pytest.fixture(autouse=True)
def _reset_rate_limiter() -> Generator[None, None, None]:
    # slowapi's limiter keeps its counters in an in-process store that isn't touched by
    # the per-test DB rollback below, so without this every test after the 10th request
    # to a rate-limited endpoint (e.g. /auth/register) would fail with a spurious 429.
    limiter.reset()
    yield


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    connection = engine.connect()
    outer_transaction = connection.begin()
    TestSessionLocal = sessionmaker(bind=connection)
    session = TestSessionLocal()

    session.begin_nested()

    @event.listens_for(session, "after_transaction_end")
    def restart_savepoint(sess, transaction):
        if transaction.nested and not transaction._parent.nested:
            sess.begin_nested()

    try:
        yield session
    finally:
        session.close()
        outer_transaction.rollback()
        connection.close()


@pytest.fixture
def client(db_session: Session) -> Generator[TestClient, None, None]:
    def _get_db_override():
        yield db_session

    app.dependency_overrides[get_db] = _get_db_override
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
