# Cloud Run deployment

One script deploys all three services to Cloud Run in `asia-south1`, public (`--allow-unauthenticated`),
running as `hackathon-dev@spontom-build-with-ai.iam.gserviceaccount.com`.

```bash
export PATH=/opt/homebrew/share/google-cloud-sdk/bin:$PATH   # if gcloud is not on PATH
infrastructure/cloud-run/deploy.sh                 # api, farmer-web, officer-dashboard
infrastructure/cloud-run/deploy.sh api             # one service
```

| Service | Source | URL (deterministic: `https://<service>-<project-number>.asia-south1.run.app`) |
|---|---|---|
| `agri-ai-network-api` | `services/api/Dockerfile` | https://agri-ai-network-api-847963771142.asia-south1.run.app |
| `agri-ai-network-farmer-web` | `apps/farmer-web/Dockerfile` | https://agri-ai-network-farmer-web-847963771142.asia-south1.run.app |
| `agri-ai-network-officer-dashboard` | `apps/officer-dashboard/Dockerfile` | https://agri-ai-network-officer-dashboard-847963771142.asia-south1.run.app |

## How it works

1. **Images** are built by Cloud Build (`cloudbuild.yaml`) with the repository root as build context
   (the API image needs `ai/prompts` and `data/`; the Next.js images need the pnpm workspace) and pushed to
   Artifact Registry `asia-south1-docker.pkg.dev/<project>/cloud-run-source-deploy`. `.gcloudignore` and
   `.dockerignore` keep `.env`, `.env.local`, credentials, `node_modules` and build output out of the upload.
2. **API** gets plain env vars (project, region, BigQuery dataset, bucket, Gemini model/backend, CORS origins)
   and **secrets from Secret Manager**: `MAPS_API_KEY=maps-api-key:latest`,
   `GOOGLE_CLOUD_API_KEY=google-api-key:latest`, and `GEMINI_API_KEY=gemini-api-key:latest` *only if that secret
   exists*. Google Cloud clients (BigQuery, Cloud Storage, Vertex AI) authenticate as the service account.
   `max-instances=1` because the document store is per-instance SQLite until Firestore is enabled.
3. **Frontends**: `NEXT_PUBLIC_*` values are inlined by `next build`, so the script writes a temporary
   `apps/<app>/.env.production` (gitignored, deleted on exit) containing the API URL and the browser Maps key
   (from `$NEXT_PUBLIC_MAPS_API_KEY` or `apps/<app>/.env.local`). The key is never committed; it is visible in
   the browser bundle by design and must stay HTTP-referrer restricted to `https://*.run.app` (+ localhost).
4. **CORS**: the API allows the two frontend URLs explicitly plus any `agri-ai-network-<app>-*.run.app` origin.

## Adding Gemini later

Gemini already runs **live on Vertex AI** through the service account (`GEMINI_BACKEND=vertex`, the default,
model `gemini-2.5-flash`). To switch to a Google AI Studio key instead:

```bash
# lead only - creates the secret
printf '%s' "$GEMINI_API_KEY" | gcloud secrets create gemini-api-key --data-file=- --replication-policy=automatic
# redeploy the API: the script detects the secret and attaches GEMINI_API_KEY=gemini-api-key:latest
GEMINI_BACKEND=api-key infrastructure/cloud-run/deploy.sh api
```

The service account needs `roles/secretmanager.secretAccessor` on the new secret (same as the existing two).

## Other switches

| Variable | Default | Effect |
|---|---|---|
| `GEMINI_MODEL` | `gemini-2.5-flash` | Model id (must exist for the chosen backend/region) |
| `EARTH_ENGINE_PROJECT` | empty | Set to the registered project once Earth Engine registration is approved - live Sentinel-2 NDVI |
| `GCS_BUCKET` | `<project>-media` | Crop Doctor photos (`diagnoses/` prefix; bucket stays private, images streamed by the API) |
| `BIGQUERY_DATASET` | `agri_ai_network` | Officer analytics table `district_indicators` (load: `data/transformations/load_bigquery.py`) |

Firestore: once a Firestore database exists, add `FIREBASE_PROJECT_ID` to the API env file in `deploy.sh`
and raise `--max-instances`. The API probes Firestore at startup and falls back to SQLite if it is missing.

## Verify

```bash
API=https://agri-ai-network-api-847963771142.asia-south1.run.app
curl -s $API/health
curl -s $API/api/system/status | jq '.integrations[] | {key, mode}'
curl -s -X POST $API/api/advisory/generate -H 'content-type: application/json' \
  -d '{"field_id":"FLD-ECB-2026-K-55112"}' | jq '.ai'
```
