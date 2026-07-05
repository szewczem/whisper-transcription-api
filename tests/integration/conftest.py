from collections.abc import Iterator

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database.session import SessionFactory


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
