import dataclasses
import math
import re
import uuid
import zlib

import chromadb
import fitz
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.config import get_settings
from backend.database import Base, get_db
from backend.dependencies import get_ai_provider, get_embedder, get_retrieval
from backend.main import app
from backend.models import database_models  # noqa: F401
from backend.services.ai_provider import AIProvider
from backend.services.retrieval_service import RetrievalService


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


class FakeEmbedder:
    """Deterministic bag-of-words vectors: texts sharing words get similar vectors."""

    model_name = "fake"

    def embed(self, texts):
        return [self._vec(t) for t in texts]

    @staticmethod
    def _vec(text):
        v = [0.0] * 64
        for word in re.findall(r"[a-z0-9]+", text.lower()):
            v[zlib.crc32(word.encode()) % 64] += 1.0
        norm = math.sqrt(sum(x * x for x in v)) or 1.0
        return [x / norm for x in v]


def make_pdf_bytes(pages):
    """Build a real PDF in memory. An empty string gives a blank (scanned-like) page."""
    doc = fitz.open()
    for text in pages:
        page = doc.new_page()
        if text:
            page.insert_textbox(fitz.Rect(72, 72, 520, 770), text, fontsize=11)
    data = doc.tobytes()
    doc.close()
    return data


@pytest.fixture
def fake_provider():
    return FakeProvider()


@pytest.fixture
def retrieval():
    return RetrievalService(chromadb.EphemeralClient(), collection_name=f"test_{uuid.uuid4().hex}")


@pytest.fixture
def client(fake_provider, retrieval, tmp_path):
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

    settings = dataclasses.replace(
        get_settings(), upload_directory=tmp_path / "uploads", max_upload_size_mb=1
    )
    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_ai_provider] = lambda: fake_provider
    app.dependency_overrides[get_embedder] = lambda: FakeEmbedder()
    app.dependency_overrides[get_retrieval] = lambda: retrieval
    app.dependency_overrides[get_settings] = lambda: settings
    yield TestClient(app)  # no "with": skips lifespan, so no real files are created
    app.dependency_overrides.clear()