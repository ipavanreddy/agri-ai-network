"""Force deterministic demo mode for every test, regardless of keys present in the repo .env."""

import os
import tempfile

_TMP = tempfile.mkdtemp(prefix="agri-api-tests-")
os.environ.update({
    "GEMINI_API_KEY": "",
    "GOOGLE_GENAI_USE_VERTEXAI": "false",
    "EARTH_ENGINE_PROJECT": "",
    "FIREBASE_PROJECT_ID": "",
    "GOOGLE_CLOUD_PROJECT": "",
    "GCS_BUCKET": "",
    "GOOGLE_CLOUD_API_KEY": "",
    "MAPS_API_KEY": "",
    "USE_PUBLIC_APIS": "false",
    "STORE_PATH": os.path.join(_TMP, "test.sqlite"),
    "UPLOAD_DIR": os.path.join(_TMP, "uploads"),
})

import pytest
from fastapi.testclient import TestClient

from app.config import SAMPLE_DIR
from app.main import app


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="session")
def leaf_png() -> bytes:
    return (SAMPLE_DIR / "images" / "leaf_spot_synthetic.png").read_bytes()


AP_FIELD = "FLD-ECB-2026-K-55112"
MH_FIELD = "FLD-PN-2026-0091"
PB_FIELD = "FLD-PB-34--12"
