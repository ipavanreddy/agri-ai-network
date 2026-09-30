"""Load the labelled regional sample into BigQuery so the officer dashboard reads it live.

    cd services/api && uv run python ../../data/transformations/load_bigquery.py

Needs GOOGLE_CLOUD_PROJECT (+ ADC or GOOGLE_APPLICATION_CREDENTIALS) and BIGQUERY_DATASET in the repo .env.
Creates/replaces the table `{project}.{dataset}.district_indicators` (the dataset must already exist). Nested fields are stored as JSON strings and
decoded by services/api/app/analytics/service.py. Replace this sample with real state feeds later.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "services" / "api"))

from google.cloud import bigquery  # noqa: E402

from app.config import settings  # noqa: E402


def main() -> None:
    if not settings.google_cloud_project:
        raise SystemExit("Set GOOGLE_CLOUD_PROJECT in .env first")
    sample = json.loads((ROOT / "data" / "sample" / "regional" / "district_indicators.json").read_text())
    meta = sample["_meta"]
    rows = []
    for state_id, districts in sample["states"].items():
        for d in districts:
            rows.append({**d, "state_id": state_id,
                         "crop_distribution_pct": json.dumps(d["crop_distribution_pct"]),
                         "blocks": json.dumps(d["blocks"]), "top_issues": json.dumps(d["top_issues"]),
                         "source": meta["source"], "dataset_version": meta["dataset_version"], "is_sample": True})
    client = bigquery.Client(project=settings.google_cloud_project)
    # The dataset is provisioned by the project owner; this script only (re)creates the table inside it.
    client.get_dataset(f"{settings.google_cloud_project}.{settings.bigquery_dataset}")
    table = f"{settings.google_cloud_project}.{settings.bigquery_dataset}.district_indicators"
    job = client.load_table_from_json(rows, table, job_config=bigquery.LoadJobConfig(
        autodetect=True, write_disposition="WRITE_TRUNCATE"))
    job.result()
    print(f"loaded {len(rows)} rows into {table}")


if __name__ == "__main__":
    main()
