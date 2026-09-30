import os
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = REPO_ROOT / "data"
SAMPLE_DIR = DATA_DIR / "sample"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=REPO_ROOT / ".env", extra="ignore")

    project_name: str = "agri-ai-network"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"
    google_genai_use_vertexai: bool = False
    google_cloud_project: str = ""
    google_cloud_location: str = "asia-south1"
    google_application_credentials: str = ""
    bigquery_dataset: str = "agri_ai_network"
    gcs_bucket: str = ""
    firebase_project_id: str = ""
    maps_api_key: str = ""
    earth_engine_project: str = ""
    # API key for Cloud Translation / Speech-to-Text / Text-to-Speech REST APIs.
    google_cloud_api_key: str = ""
    # Keyless public APIs (Open-Meteo weather, ISRIC SoilGrids). false = always use data/sample fixtures.
    use_public_apis: bool = True
    public_api_timeout_s: float = 6.0
    # Local store (SQLite) used when FIREBASE_PROJECT_ID is empty.
    store_path: str = str(Path(__file__).resolve().parents[1] / ".data" / "agri.sqlite")
    upload_dir: str = str(Path(__file__).resolve().parents[1] / ".data" / "uploads")
    cors_origins: str = "http://localhost:3040,http://localhost:3041"

    # ---- derived integration switches -------------------------------------------------------
    @property
    def gemini_enabled(self) -> bool:
        return bool(self.gemini_api_key) or (self.google_genai_use_vertexai and bool(self.google_cloud_project))

    @property
    def earth_engine_enabled(self) -> bool:
        return bool(self.earth_engine_project)

    @property
    def firestore_enabled(self) -> bool:
        return bool(self.firebase_project_id)

    @property
    def bigquery_enabled(self) -> bool:
        return bool(self.google_cloud_project) and bool(self.bigquery_dataset)

    @property
    def gcs_enabled(self) -> bool:
        return bool(self.gcs_bucket)

    @property
    def cloud_speech_enabled(self) -> bool:
        return bool(self.google_cloud_api_key)


settings = Settings()

# Google client libraries read ADC from the process environment, not from pydantic settings.
if settings.google_application_credentials and "GOOGLE_APPLICATION_CREDENTIALS" not in os.environ:
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = settings.google_application_credentials
