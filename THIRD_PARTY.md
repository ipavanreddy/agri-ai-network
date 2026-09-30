# Third-party datasets, models and libraries

Every reused dataset, model and library must be cited here (hackathon rule).

## Libraries

| Name | Type | Licence | Source URL | Used for |
|---|---|---|---|---|
| Next.js | Library | MIT | https://nextjs.org | Frontend |
| React | Library | MIT | https://react.dev | Frontend |
| shadcn/ui | Library | MIT | https://ui.shadcn.com | UI components |
| Base UI | Library | MIT | https://base-ui.com | Primitives under shadcn/ui |
| Tailwind CSS | Library | MIT | https://tailwindcss.com | Styling |
| lucide-react | Library | ISC | https://lucide.dev | Icons |
| Leaflet | Library | BSD-2-Clause | https://leafletjs.com | Non-Google map fallback (field drawing, regional map) |
| @types/leaflet, @types/google.maps | Library | MIT | https://github.com/DefinitelyTyped/DefinitelyTyped | TypeScript types |
| FastAPI | Library | MIT | https://fastapi.tiangolo.com | API |
| Pydantic / pydantic-settings | Library | MIT | https://docs.pydantic.dev | Canonical schema, AI output schemas, config |
| HTTPX | Library | BSD-3-Clause | https://www.python-httpx.org | Calls to Open-Meteo, SoilGrids, Cloud REST APIs |
| Uvicorn | Library | BSD-3-Clause | https://www.uvicorn.org | API server |
| Google Gen AI SDK | Library | Apache-2.0 | https://github.com/googleapis/python-genai | Gemini calls |
| Earth Engine Python API | Library | Apache-2.0 | https://github.com/google/earthengine-api | Sentinel-2 NDVI/NDMI time series |
| google-cloud-bigquery / google-cloud-storage | Library | Apache-2.0 | https://github.com/googleapis/python-bigquery | Regional analytics, image storage |
| firebase-admin | Library | Apache-2.0 | https://github.com/firebase/firebase-admin-python | Firestore document store |
| pytest | Library | MIT | https://pytest.org | Tests |

## Services and models (used only when the matching key is configured)

| Name | Type | Terms | Source URL | Used for |
|---|---|---|---|---|
| Gemini (model from `GEMINI_MODEL`) | Model | Google AI / Vertex AI terms | https://ai.google.dev | Advisory, crop-option explanation, Crop Doctor (multimodal), voice Q&A, translation fallback |
| Google Maps JavaScript API | Service | Google Maps Platform ToS | https://developers.google.com/maps | Satellite basemap when `NEXT_PUBLIC_MAPS_API_KEY` is set |
| Cloud Translation, Speech-to-Text, Text-to-Speech | Service | Google Cloud ToS | https://cloud.google.com | Localisation and voice |
| Web Speech API (browser) | Service | Browser vendor terms | https://developer.mozilla.org/docs/Web/API/Web_Speech_API | Demo-mode voice fallback |

## Datasets

| Name | Type | Licence | Source URL | Used for |
|---|---|---|---|---|
| Copernicus Sentinel-2 SR Harmonized (`COPERNICUS/S2_SR_HARMONIZED`) via Earth Engine | Dataset | Copernicus Sentinel data terms (free, attribution) | https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S2_SR_HARMONIZED | Field NDVI/NDMI (live mode) |
| Open-Meteo Forecast API | Dataset/API | Data CC BY 4.0; free API for non-commercial use | https://open-meteo.com | Live weather, 14-day history, 7-day forecast, soil moisture |
| ISRIC SoilGrids 2.0 | Dataset/API | CC BY 4.0 | https://soilgrids.org | Modelled soil texture (and pH/SOC when no state record exists) |
| OpenStreetMap tiles and data | Dataset | ODbL; OSMF tile usage policy | https://www.openstreetmap.org/copyright | Map fallback basemap |
| Soil Health Card nutrient rating thresholds (N 280/560, P 10/25, K 110/280 kg/ha) | Reference | Government of India public guidance | https://soilhealth.dac.gov.in | Soil factor of the Farm Health score |
| IMD heavy-rainfall threshold (64.5 mm/day) | Reference | Public terminology | https://mausam.imd.gov.in | Weather alerts / weather factor |

## Project-generated data (no third-party content)

| Name | Location | Notes |
|---|---|---|
| Synthetic state exports (AP, MH, PB), weather/NDVI/texture fixtures, district aggregates, diagnosis fixtures, synthetic leaf image | `data/sample/` | Generated deterministically by `data/scripts/generate_sample_data.py`; every file is labelled `is_sample` / `is_synthetic` |
| Crop catalogue (indicative requirement ranges, expected NDVI by stage) | `data/sample/crops/crop_catalog.json` | Curated for the demo from general agronomy knowledge; not validated extension advice |
| Hindi / Telugu UI and demo-advisory strings | `apps/farmer-web/src/lib/i18n.tsx`, `services/api/app/advisory/messages.py` | Hand-written demo translations; need native-speaker review |
