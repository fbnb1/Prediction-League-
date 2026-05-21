import pytest
from sqlalchemy import text

import app.models  # noqa: F401  -- registers models on Base.metadata
from app.db import Base, SessionLocal, engine


@pytest.fixture(scope="session", autouse=True)
def _schema():
    """Create the schema once for the test session."""
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)


@pytest.fixture()
def session():
    """A clean database and a session for each test."""
    with engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(text(f'TRUNCATE TABLE "{table.name}" RESTART IDENTITY CASCADE'))
    with SessionLocal() as s:
        yield s
