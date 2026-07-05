from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database.session import SessionFactory
from app.main import app


@pytest.fixture
def db_session() -> Iterator[Session]:
    session = SessionFactory()

    try:
        session.execute(text("TRUNCATE TABLE transcription_jobs"))
        session.commit()

        yield session
    finally:
        session.rollback()

        session.execute(text("TRUNCATE TABLE transcription_jobs"))
        session.commit()

        session.close()


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client
