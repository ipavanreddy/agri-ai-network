# Third-party datasets, models, services and libraries

Every reused dataset, model, service, map tile source and library is cited here (hackathon rule). Versions are pinned
in `pnpm-lock.yaml` and `services/api/uv.lock`.

## AI models

| Name | Type | Terms | Source URL | Used for |
|---|---|---|---|---|
| Gemini 2.5 Flash on Vertex AI (`GEMINI_MODEL`, default `gemini-2.5-flash`) | Model | Google Cloud / Vertex AI Generative AI terms | https://cloud.google.com/vertex-ai/generative-ai/docs/models | Agro-advisory, crop-option explanation, Crop Doctor (multimodal image analysis), voice Q&A, translation fallback |
| Gemini API via Google AI Studio (optional backend, `GEMINI_API_KEY`) | Model | Gemini API terms | https://ai.google.dev | Same roles when a Gemini API key is used instead of Vertex AI |
| Google Cloud Speech-to-Text v1 models (en-IN, hi-IN, te-IN) | Model (service) | Google Cloud terms | https://cloud.google.com/speech-to-text | Farmer's spoken question |
| Google Cloud Text-to-Speech voices (en-IN, hi-IN, te-IN) | Model (service) | Google Cloud terms | https://cloud.google.com/text-to-speech | Spoken answers |
| Google Cloud Translation v2 (NMT) | Model (service) | Google Cloud terms | https://cloud.google.com/translate | Localising advisories to Hindi / Telugu |

No model was trained or fine-tuned for this project. Prompts (`ai/prompts/`) and output schemas (`ai/schemas/`) are original.

## Google Cloud and Maps Platform services

| Name | Terms | Source URL | Used for |
|---|---|---|---|
| Cloud Run | Google Cloud terms | https://cloud.google.com/run | Hosting the API and both web apps |
| Cloud Build, Artifact Registry | Google Cloud terms | https://cloud.google.com/build | Building and storing container images |
| Secret Manager | Google Cloud terms | https://cloud.google.com/secret-manager | `maps-api-key`, `google-api-key`, optional `gemini-api-key` |
| BigQuery | Google Cloud terms | https://cloud.google.com/bigquery | Officer analytics table `district_indicators` |
| Cloud Storage | Google Cloud terms | https://cloud.google.com/storage | Crop Doctor photos (private bucket) |
| Google Earth Engine | Earth Engine terms (noncommercial / registered project) | https://earthengine.google.com | Sentinel-2 NDVI/NDMI for the field polygon (live once registration is approved) |
| Firebase / Cloud Firestore | Firebase terms | https://firebase.google.com | Document store when enabled (SQLite fallback) |
| Google Maps JavaScript API (satellite/hybrid tiles) | Google Maps Platform Terms of Service | https://developers.google.com/maps/documentation/javascript | Basemap for field drawing and the officer risk map |
| Google Maps Geocoding API | Google Maps Platform Terms of Service | https://developers.google.com/maps/documentation/geocoding | Village / town search, reverse geocoding of new fields |
| Google Places API (Text Search) | Google Maps Platform Terms of Service | https://developers.google.com/maps/documentation/places/web-service | Nearest Krishi Vigyan Kendra / agriculture office |
| Google Routes API (computeRoutes) | Google Maps Platform Terms of Service | https://developers.google.com/maps/documentation/routes | Driving distance and time to that office |
| Web Speech API (browser) | Browser vendor terms | https://developer.mozilla.org/docs/Web/API/Web_Speech_API | Voice fallback when Cloud Speech is not configured or the browser cannot record Opus |

## Datasets and map tiles

| Name | Type | Licence | Source URL | Used for |
|---|---|---|---|---|
| Copernicus Sentinel-2 SR Harmonized (`COPERNICUS/S2_SR_HARMONIZED`) via Earth Engine | Dataset | Copernicus Sentinel data terms (free, attribution) | https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S2_SR_HARMONIZED | Field NDVI/NDMI (live mode) |
| Open-Meteo Forecast API (ECMWF, NOAA GFS, DWD ICON models) | Dataset/API | Data CC BY 4.0; free API for non-commercial use | https://open-meteo.com | Live weather, 14-day history, 7-day forecast, soil moisture |
| ISRIC SoilGrids 2.0 | Dataset/API | CC BY 4.0 | https://soilgrids.org | Modelled soil texture (and pH/SOC when no state record exists) |
| Google Maps Platform map tiles and place data | Map tiles / data | Google Maps Platform ToS (attribution shown in the map) | https://cloud.google.com/maps-platform/terms | Basemap, geocoding and place results |
| OpenStreetMap tiles and data | Map tiles / data | ODbL; OSMF tile usage policy | https://www.openstreetmap.org/copyright | Fallback basemap (Leaflet) |
| Soil Health Card nutrient rating thresholds (N 280/560, P 10/25, K 110/280 kg/ha) | Reference | Government of India public guidance | https://soilhealth.dac.gov.in | Soil factor of the Farm Health score |
| IMD heavy-rainfall threshold (64.5 mm/day) | Reference | Public terminology | https://mausam.imd.gov.in | Weather alerts / weather factor |
| Indian state and district names (approximate district centroids entered by hand) | Reference | Public administrative information (official list: Local Government Directory) | https://lgdirectory.gov.in | State adapter district tables |

## Libraries: frontend (`apps/*`)

| Name | Licence | Source URL | Used for |
|---|---|---|---|
| Next.js | MIT | https://nextjs.org | Web framework (standalone output for Cloud Run) |
| React, React DOM | MIT | https://react.dev | UI |
| shadcn/ui (CLI + component source) | MIT | https://ui.shadcn.com | UI components |
| Base UI (`@base-ui/react`) | MIT | https://base-ui.com | Primitives under shadcn/ui |
| Tailwind CSS, `@tailwindcss/postcss`, tw-animate-css | MIT | https://tailwindcss.com | Styling |
| class-variance-authority | Apache-2.0 | https://cva.style | Component variants |
| cn | MIT | https://www.npmjs.com/package/cn | Class-name helper |
| lucide-react | ISC | https://lucide.dev | Icons |
| sonner | MIT | https://sonner.emilkowal.ski | Toasts |
| next-themes | MIT | https://github.com/pacocoursey/next-themes | Theme handling |
| Leaflet | BSD-2-Clause | https://leafletjs.com | Non-Google map fallback |
| Geist / Geist Mono fonts (via `next/font/google`) | SIL Open Font License 1.1 | https://vercel.com/font | Typography |
| TypeScript, ESLint, eslint-config-next | Apache-2.0 / MIT / MIT | https://www.typescriptlang.org | Tooling |
| @types/leaflet, @types/google.maps, @types/react, @types/node | MIT | https://github.com/DefinitelyTyped/DefinitelyTyped | TypeScript types |

## Libraries: API (`services/api`)

| Name | Licence | Source URL | Used for |
|---|---|---|---|
| FastAPI, Starlette | MIT / BSD-3-Clause | https://fastapi.tiangolo.com | API |
| Pydantic, pydantic-settings | MIT | https://docs.pydantic.dev | Canonical schema, AI output schemas, config |
| Uvicorn | BSD-3-Clause | https://www.uvicorn.org | API server |
| HTTPX | BSD-3-Clause | https://www.python-httpx.org | Open-Meteo, SoilGrids, Maps, Speech/Translation REST calls |
| python-multipart | Apache-2.0 | https://github.com/Kludex/python-multipart | Photo / audio uploads |
| Google Gen AI SDK (`google-genai`) | Apache-2.0 | https://github.com/googleapis/python-genai | Gemini calls (Vertex AI or API key) |
| Earth Engine Python API | Apache-2.0 | https://github.com/google/earthengine-api | Sentinel-2 NDVI/NDMI time series |
| google-cloud-bigquery, google-cloud-storage | Apache-2.0 | https://github.com/googleapis/google-cloud-python | Regional analytics, image storage |
| firebase-admin | Apache-2.0 | https://github.com/firebase/firebase-admin-python | Firestore document store |
| pytest, Ruff | MIT | https://pytest.org | Tests, lint |

## Build and packaging

| Name | Licence | Source URL | Used for |
|---|---|---|---|
| pnpm | MIT | https://pnpm.io | JS workspace |
| uv (and `ghcr.io/astral-sh/uv` image) | MIT / Apache-2.0 | https://github.com/astral-sh/uv | Python env and Docker install |
| Docker official images `python:3.12-slim`, `node:22-slim` | PSF / MIT (+ Debian package licences) | https://hub.docker.com/_/python | Container base images |
| PptxGenJS | MIT | https://github.com/gitbrent/PptxGenJS | Generating the pitch deck (`docs/pitch/build-deck.js`, Spontom deck kit `docs/pitch/deck-kit.js`) |

## Project-generated data (no third-party content)

| Name | Location | Notes |
|---|---|---|
| Synthetic state exports (AP, MH, PB), weather/NDVI/texture fixtures, district aggregates, diagnosis fixtures, synthetic leaf image | `data/sample/` | Generated deterministically by `data/scripts/generate_sample_data.py`; every file is labelled `is_sample` / `is_synthetic`. The BigQuery table is loaded from the same labelled sample. |
| Crop catalogue (indicative requirement ranges, expected NDVI by stage) | `data/sample/crops/crop_catalog.json` | Curated for the demo from general agronomy knowledge; not validated extension advice |
| Hindi / Telugu UI and demo-advisory strings | `apps/farmer-web/src/lib/i18n.tsx`, `services/api/app/advisory/messages.py` | Hand-written demo translations; need native-speaker review |
| Prompts, schemas, state adapters | `ai/`, `data/adapters/`, `data/schemas/` | Original work |

## Pitch deck assets (`docs/pitch/assets/`)

| Name | Source | Notes |
|---|---|---|
| `spontom-mark.png` | Spontom Enterprise Private Limited | Company logo (own mark of the submitting company) |
| `cover-farm-health.png`, `farmer-app.png`, `farmer-crop-doctor.png`, `officer-dashboard.png` | Screenshots of this prototype (headless Chrome, 30 Sep 2026) | Show the sample farmer and labelled synthetic indicators; the officer map tiles are © OpenStreetMap contributors (ODbL). No AI-generated images are used (Imagen was not available to the project at build time) |
