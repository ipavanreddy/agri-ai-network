# Agri AI Network: AI-Powered Interoperable Digital Agriculture Network

Build with AI (Google) hackathon, Track 4. Full spec: [docs/PRD.md](docs/PRD.md).

## Core journey (PRD §57 Priority 1, built end to end)

```text
Field (draw on map / pick a demo farmer)
 ↓
Weather (Open-Meteo) + Soil (Soil Health Card via state adapter + SoilGrids) + Satellite (Earth Engine Sentinel-2 NDVI)
 ↓
Farm Intelligence + Farm Health score
 ↓
Gemini Advisory (observed → interpretation → recommendation, + regenerative practice)
 ↓
Regenerative Crop Recommendation (rule scores + Gemini explanation)
 ↓
Crop Doctor: leaf-photo diagnosis (Gemini multimodal)
```

Also built: English / Hindi / Telugu UI and advisories, a voice question loop (Priority 2), the Agriculture
Officer dashboard with a human review queue, and three state configurations (AP groundnut, Maharashtra
cotton, Punjab wheat) mapped through a canonical schema by declarative state adapters (Priority 3).

**Users:** Farmer (`apps/farmer-web`, :3040) · Agriculture Officer (`apps/officer-dashboard`, :3041) · API (`services/api`, :8040)

## Run the demo

```bash
cp .env.example .env                      # keys are optional - see "Demo mode" below
for a in apps/*; do cp $a/.env.example $a/.env.local; done
pnpm install
(cd services/api && uv sync)

pnpm dev:api                 # http://localhost:8040  (OpenAPI docs at /docs)
pnpm dev:farmer-web          # http://localhost:3040
pnpm dev:officer-dashboard   # http://localhost:3041
```

The API seeds the three demo farmers/fields on startup by running each state's sample export through
its adapter. Local data lives in `services/api/.data/` (SQLite + uploaded images; delete it to reset).

### Five-minute demo script (PRD §44)

1. **Farmer (0:00)** - open :3040, pick *Lakshmi Devi · Groundnut · AP* (2.4 acres, Anantapur). Or click
   *Register a new field* and tap the field's corners on the map.
2. **Farm intelligence (0:30)** - weather, soil and satellite cards, each with source + freshness, feed the
   Farm Health score with a per-factor breakdown. Tick *Use sample scenario data* for the scripted,
   offline-safe story (dry spell, rain expected in 48 h, NDVI dipping).
3. **Advisory (1:10)** - *Generate advisory*: observed data → AI interpretation → recommended actions,
   risk, time sensitivity, one field-specific regenerative practice, missing information, provenance.
4. **Crop recommendation** - ≥ 3 crops with suitability, rule-score breakdown and rotation plan.
5. **Crop Doctor (1:50)** - upload a leaf photo (or *Use sample leaf photo*): potential condition,
   confidence, visible symptoms, next steps, disclaimer. Farm Health now includes *crop condition*.
6. **Language + voice (2:30)** - switch to తెలుగు / हिन्दी: the same advisory is re-presented without
   re-analysis. Tap *Speak* (or an example question) for a spoken answer grounded in farm context.
7. **Officer (3:00)** - open :3041: India → state → district → block risk map, crop distribution,
   hotspots; approve/reject the farmer's AI advisory in the *Review queue* (the farmer sees the status).
8. **Interoperability (3:40)** - *Interoperability* tab: switch AP / MH / PB and compare the raw state
   record, the adapter mapping and the identical canonical record.

## Demo mode vs real integrations

Every Google integration works for real when its variable is set and otherwise falls back to a clearly
labelled demo path. The UIs show amber **"Demo mode · sample data"** badges wherever a fallback or sample
data is used; `GET /api/system/status` lists the state of each integration.

| Variable (repo `.env` unless noted) | Switches on | Fallback when empty |
|---|---|---|
| `GEMINI_API_KEY` (or `GOOGLE_GENAI_USE_VERTEXAI=true` + `GOOGLE_CLOUD_PROJECT`), model from `GEMINI_MODEL` | Gemini advisory, crop-option explanations, Crop Doctor (multimodal), voice Q&A, translation | Deterministic rules (`model_name=demo-rules`); Crop Doctor returns per-crop fixtures and says the photo was **not** analysed |
| `EARTH_ENGINE_PROJECT` (+ ADC or `GOOGLE_APPLICATION_CREDENTIALS` service account) | Sentinel-2 SR NDVI/NDMI time series for the field polygon + NDVI thumbnail | Sample NDVI series per state scenario |
| `USE_PUBLIC_APIS=true` (default, keyless) | Open-Meteo weather (14-day history, 7-day forecast, soil moisture); ISRIC SoilGrids texture | Sample weather/texture (also used automatically if the APIs are unreachable) |
| `GOOGLE_CLOUD_API_KEY` | Cloud Translation, Speech-to-Text, Text-to-Speech | Built-in en/hi/te message catalogue; browser Web Speech API |
| `FIREBASE_PROJECT_ID` (+ ADC) | Firestore document store | Local SQLite |
| `GOOGLE_CLOUD_PROJECT` + `BIGQUERY_DATASET` | Officer analytics from BigQuery `district_indicators` (load with `data/transformations/load_bigquery.py`) | Synthetic district sample |
| `GCS_BUCKET` | Crop photos stored in Cloud Storage | Local disk |
| `NEXT_PUBLIC_MAPS_API_KEY` (`apps/*/.env.local`) | Google Maps satellite basemap | Leaflet + OpenStreetMap |

Soil NPK/pH/OC always come from the state's Soil Health Card style records (sample exports mapped by the
adapters); replacing those exports with real state feeds is a data change, not a code change.

## Farm Health score (PRD §11)

`Farm Health = Vegetation × 30% + Soil × 25% + Weather × 20% + Water × 15% + Crop condition × 10%`
(`services/api/app/intelligence/health.py::WEIGHTS`). Bands: ≥ 75 Good, 50-74 Moderate, < 50 Poor.

- **Vegetation** - latest NDVI ÷ expected NDVI for the crop's stage at that date; −10/−20 if NDVI fell ≥ 0.05/0.10 in ~30 days.
- **Soil** - pH vs crop range (40), organic carbon (30), N/P/K Soil Health Card ratings (10 each).
- **Weather** - starts at 100; penalties for heat near the crop threshold, heavy rain (IMD 64.5 mm), humidity ≥ 85 % (worse after heavy rain), strong wind, frost.
- **Water** - 14-day rain (+ irrigation credit) vs 14-day crop need; waterlogging, topsoil moisture and forecast-rain adjustments.
- **Crop condition** - from the latest Crop Doctor result (≤ 30 days).

A factor with missing inputs is shown as *missing* and its weight is redistributed - values are never imputed.

## AI design

- Prompts: `ai/prompts/*_v1.md`; output schemas: `app/ai/schemas.py`, exported to `ai/schemas/*.schema.json`.
- `app/ai/runner.py` sends the canonical field context (`app/intelligence/context.py::ai_context`) to
  `generate_structured` (schema-validated JSON) and records `model_name`, `model_version`, `prompt_version`
  on every advisory, recommendation and diagnosis. Gemini failures fall back to the demo path with a reason.
- Every AI output starts as `pending_officer_review`; the officer approves or rejects it in the dashboard.

## Interoperability

`data/adapters/{ap,mh,pb}.json` declare field mappings, code tables, unit conversions (ha/kanal → acres,
g/kg → %, kg/acre → kg/ha), date formats and language fallbacks. One engine
(`services/api/app/interop/adapters.py`) applies any of them to produce the canonical model
(`data/schemas/*.schema.json`). Onboarding a state = new config + data export.

## Data

`python3 data/scripts/generate_sample_data.py` regenerates everything in `data/sample/` deterministically;
each file carries `source`, `reference_timestamp`, `dataset_version`, `geographic_scope`, `is_sample`,
`is_synthetic`. Schemas: `cd services/api && uv run python -m app.canonical.export`.

## Tests and checks

```bash
pnpm test:api   # pytest: Farm Health, adapters, API endpoints, demo-mode end-to-end journey
pnpm lint
pnpm build
```

## API (selected, PRD §37)

`POST /api/farmers` · `POST /api/fields` · `GET /api/fields/{id}/intelligence|weather|soil|satellite|health` ·
`POST /api/advisory/generate` · `POST /api/advisories/{id}/localize` · `POST /api/crop-recommendation` ·
`POST /api/diagnosis` · `POST /api/ask` · `POST /api/translate|speech-to-text|text-to-speech` ·
`GET /api/states`, `/api/states/{id}/analytics`, `/api/states/{id}/adapter-demo`, `/api/districts/{id}/risks` ·
`GET /api/review-queue` · `POST /api/reviews/{kind}/{id}` · `GET /api/system/status`

## Known gaps

- No authentication/role enforcement yet (two roles are separate apps only).
- Regional indicators, state exports and scenario weather/NDVI are synthetic samples until real feeds/keys are added.
- Hindi/Telugu strings are hand-written and need native-speaker review; Marathi/Punjabi fall back to Hindi.
- The Cloud Run Dockerfile copies only `services/api/`; `data/` and `ai/` must be added to the image before deploying.
- Crop requirement ranges are indicative, not validated agronomic advice.

## Layout

| Path | Purpose |
|---|---|
| `apps/farmer-web/` | Farmer app |
| `apps/officer-dashboard/` | Agriculture Officer dashboard |
| `services/api/app/` | FastAPI: `farms/`, `intelligence/` (weather, soil, satellite, health), `advisory/`, `crops/`, `diagnosis/`, `localization/`, `interop/`, `analytics/`, `ai/` |
| `ai/` | Versioned prompts and exported output schemas |
| `data/` | Canonical schemas, state adapters, labelled sample data, generator and BigQuery loader |
| `infrastructure/` | Cloud Run, BigQuery, Firebase config |
