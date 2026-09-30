# Data

Every dataset (file or table) must carry: `source`, `reference_timestamp`, `dataset_version`,
`geographic_scope`, and `is_sample` / `is_synthetic`. Labelled in the UI as well.

- `schemas/`: canonical schema (PRD §21)
- `adapters/`: state adapters mapping state data → canonical schema (≥ 2 states)
- `sample/`: small, committed, labelled demo data
- `transformations/`: loaders into BigQuery
- `scripts/generate_sample_data.py`: deterministic generator for everything in `sample/` (re-run to rebuild)
- `transformations/load_bigquery.py`: loads the regional sample into BigQuery (`district_indicators`)
