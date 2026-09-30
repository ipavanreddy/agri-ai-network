"""Export JSON Schemas: canonical model -> data/schemas/, AI output schemas -> ai/schemas/.

    cd services/api && uv run python -m app.canonical.export

tests/test_schemas.py fails if the committed files drift from the Pydantic models.
"""

import json
from typing import Any

from app.ai.schemas import AI_SCHEMAS
from app.canonical import models
from app.config import DATA_DIR, REPO_ROOT

CANONICAL = {
    "farmer": models.Farmer,
    "field": models.Field_,
    "crop": models.Crop,
    "soil_observation": models.SoilObservation,
    "weather_observation": models.WeatherObservation,
    "satellite_observation": models.SatelliteObservation,
    "farm_health": models.FarmHealth,
    "provenance": models.Provenance,
    "ai_record_meta": models.AIRecordMeta,
}


def canonical_schemas() -> dict[str, Any]:
    return {name: model.model_json_schema() for name, model in CANONICAL.items()}


def ai_schemas() -> dict[str, Any]:
    return {name: model.model_json_schema() for name, model in AI_SCHEMAS.items()}


def rendered() -> dict[str, str]:
    files = {}
    for name, schema in canonical_schemas().items():
        files[str(DATA_DIR / "schemas" / f"{name}.schema.json")] = json.dumps(schema, indent=2) + "\n"
    for name, schema in ai_schemas().items():
        files[str(REPO_ROOT / "ai" / "schemas" / f"{name}.schema.json")] = json.dumps(schema, indent=2) + "\n"
    return files


def main() -> None:
    from pathlib import Path

    for path, content in rendered().items():
        Path(path).write_text(content)
        print("wrote", Path(path).relative_to(REPO_ROOT))


if __name__ == "__main__":
    main()
