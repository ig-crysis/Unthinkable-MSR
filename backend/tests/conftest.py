import os
import tempfile
from pathlib import Path

# Must run before any `app.*` module is imported anywhere (including by other
# test files), so settings pick up an isolated DB/upload dir instead of the
# real dev database.
_TEST_DIR = Path(tempfile.mkdtemp(prefix="meeting-summarizer-test-"))
os.environ["DATABASE_URL"] = f"sqlite:///{(_TEST_DIR / 'test.db').as_posix()}"
os.environ["UPLOAD_DIR"] = str(_TEST_DIR / "uploads")
os.environ["GROQ_API_KEY"] = "test-key-not-used-services-are-mocked"

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture()
def client():
    with TestClient(app) as test_client:
        yield test_client
