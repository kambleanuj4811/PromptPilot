import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.database import Base, get_db
from backend.dependencies import get_ai_provider
from backend.main import app
from backend.models import database_models  # noqa: F401
from backend.services.ai_provider import AIProvider


class FakeProvider(AIProvider):
    """Returns queued responses; the last one repeats forever."""

    name = "fake"
    model = "fake-model"

    def __init__(self, responses=None):
        self.responses = list(responses or ["OK"])
        self.calls = []

    def is_configured(self) -> bool:
        return True

    def generate_text(self, prompt, system=None, temperature=None, json_mode=False):
        self.calls.append({"prompt": prompt, "system": system, "json_mode": json_mode})
        return self.responses.pop(0) if len(self.responses) > 1 else self.responses[0]


@pytest.fixture
def fake_provider():
    return FakeProvider()


@pytest.fixture
def client(fake_provider):
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(bind=engine)
    TestSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    def override_db():
        db = TestSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_ai_provider] = lambda: fake_provider
    yield TestClient(app)  # no "with": skips lifespan, so no real DB file is created
    app.dependency_overrides.clear()