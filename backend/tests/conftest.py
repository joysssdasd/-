import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

os.environ["TEST_DATABASE_URL"] = "sqlite:///./test.db"

from backend.app.config import get_settings

get_settings.cache_clear()

from backend.app.database import Base, SessionLocal, engine, get_db
from backend.app.main import app


def override_get_db():
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


@pytest.fixture(autouse=True)
def setup_database():
    if Path("test.db").exists():
        Path("test.db").unlink()
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    if Path("test.db").exists():
        Path("test.db").unlink()


@pytest.fixture
def client():
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.pop(get_db, None)
