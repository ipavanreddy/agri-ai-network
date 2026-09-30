#!/usr/bin/env bash
# One repeatable deploy for all Agri AI Network services on Cloud Run (public, asia-south1).
#
#   infrastructure/cloud-run/deploy.sh            # api, then farmer-web and officer-dashboard
#   infrastructure/cloud-run/deploy.sh api        # only the API (e.g. after adding the Gemini secret)
#   infrastructure/cloud-run/deploy.sh farmer-web officer-dashboard
#
# Images are built by Cloud Build from the repo root (cloudbuild.yaml) and pushed to Artifact Registry.
# Secrets come from Secret Manager and are never written to the repo or the image:
#   MAPS_API_KEY=maps-api-key, GOOGLE_CLOUD_API_KEY=google-api-key, GEMINI_API_KEY=gemini-api-key (only if it exists)
# The browser Maps key (NEXT_PUBLIC_MAPS_API_KEY) is inlined into the JS bundle by `next build`, so it is taken
# from the environment or apps/<app>/.env.local, written to a temporary, gitignored apps/<app>/.env.production that
# is uploaded with the build (see .gcloudignore) and deleted again when the script exits.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

PROJECT="${GOOGLE_CLOUD_PROJECT:-spontom-build-with-ai}"
REGION="${REGION:-asia-south1}"
SERVICE_ACCOUNT="${SERVICE_ACCOUNT:-hackathon-dev@${PROJECT}.iam.gserviceaccount.com}"
AR_REPO="${AR_REPO:-cloud-run-source-deploy}"
BIGQUERY_DATASET="${BIGQUERY_DATASET:-agri_ai_network}"
GCS_BUCKET="${GCS_BUCKET:-${PROJECT}-media}"
GEMINI_MODEL="${GEMINI_MODEL:-gemini-2.5-flash}"
# vertex = Gemini on Vertex AI through the service account (works today);
# api-key = Gemini API with GEMINI_API_KEY from Secret Manager (needs the gemini-api-key secret).
GEMINI_BACKEND="${GEMINI_BACKEND:-vertex}"
# Set to the Earth Engine-registered project once registration is approved (empty = sample NDVI).
EARTH_ENGINE_PROJECT="${EARTH_ENGINE_PROJECT:-}"

API=agri-ai-network-api
APPS=(farmer-web officer-dashboard)
TARGETS=("$@")
[ ${#TARGETS[@]} -eq 0 ] && TARGETS=(api "${APPS[@]}")

gc() { gcloud --project "$PROJECT" --quiet "$@"; }
REGISTRY="$REGION-docker.pkg.dev/$PROJECT/$AR_REPO"
TAG="$(git rev-parse --short HEAD)$(git diff --quiet HEAD -- . ':!docs' || echo -dirty)-$(date +%Y%m%d%H%M%S)"
PROJECT_NUMBER="$(gc projects describe "$PROJECT" --format='value(projectNumber)')"
url_of() { echo "https://$1-$PROJECT_NUMBER.$REGION.run.app"; }  # deterministic Cloud Run URL
API_URL="$(url_of "$API")"
FARMER_URL="$(url_of agri-ai-network-farmer-web)"
OFFICER_URL="$(url_of agri-ai-network-officer-dashboard)"

cleanup() { rm -f apps/*/.env.production; }
trap cleanup EXIT

ensure_repo() {
  gc artifacts repositories describe "$AR_REPO" --location "$REGION" >/dev/null 2>&1 ||
    gc artifacts repositories create "$AR_REPO" --location "$REGION" --repository-format docker \
      --description "Cloud Run images"
}

build() {  # build <dockerfile> <image>
  gc builds submit "$ROOT" --region "$REGION" --config infrastructure/cloud-run/cloudbuild.yaml \
    --substitutions "_DOCKERFILE=$1,_IMAGE=$2"
}

deploy_api() {
  local image="$REGISTRY/$API:$TAG" envfile secrets
  build services/api/Dockerfile "$image"
  envfile="$(mktemp)"
  cat >"$envfile" <<EOF
GOOGLE_CLOUD_PROJECT: "$PROJECT"
GOOGLE_CLOUD_LOCATION: "$REGION"
BIGQUERY_DATASET: "$BIGQUERY_DATASET"
GCS_BUCKET: "$GCS_BUCKET"
GEMINI_MODEL: "$GEMINI_MODEL"
GOOGLE_GENAI_USE_VERTEXAI: "$([ "$GEMINI_BACKEND" = vertex ] && echo true || echo false)"
EARTH_ENGINE_PROJECT: "$EARTH_ENGINE_PROJECT"
USE_PUBLIC_APIS: "true"
CORS_ORIGINS: "$FARMER_URL,$OFFICER_URL,http://localhost:3040,http://localhost:3041"
EOF
  secrets="MAPS_API_KEY=maps-api-key:latest,GOOGLE_CLOUD_API_KEY=google-api-key:latest"
  if gc secrets describe gemini-api-key >/dev/null 2>&1; then
    secrets="$secrets,GEMINI_API_KEY=gemini-api-key:latest"
    echo "gemini-api-key secret found: attaching GEMINI_API_KEY (backend: $GEMINI_BACKEND)"
  fi
  # max-instances=1: without Firestore the store is per-instance SQLite, so one instance keeps the
  # farmer -> officer review loop consistent. Raise it once FIREBASE_PROJECT_ID (Firestore) is configured.
  gc run deploy "$API" --image "$image" --region "$REGION" --service-account "$SERVICE_ACCOUNT" \
    --allow-unauthenticated --env-vars-file "$envfile" --set-secrets "$secrets" \
    --memory 1Gi --cpu 1 --timeout 120 --concurrency 40 --min-instances 0 --max-instances 1 \
    --labels app=agri-ai-network,component=api
  rm -f "$envfile"
}

maps_browser_key() {  # $1 = app dir
  if [ -n "${NEXT_PUBLIC_MAPS_API_KEY:-}" ]; then echo "$NEXT_PUBLIC_MAPS_API_KEY"; return; fi
  [ -f "apps/$1/.env.local" ] && sed -n 's/^NEXT_PUBLIC_MAPS_API_KEY=//p' "apps/$1/.env.local" | tail -1 || true
}

deploy_app() {  # $1 = farmer-web | officer-dashboard
  local app="$1" service="agri-ai-network-$1" image
  image="$REGISTRY/$service:$TAG"
  # Public, build-time values only. This file is gitignored and removed on exit.
  printf 'NEXT_PUBLIC_API_URL=%s\nNEXT_PUBLIC_MAPS_API_KEY=%s\n' "$API_URL" "$(maps_browser_key "$app")" \
    >"apps/$app/.env.production"
  build "apps/$app/Dockerfile" "$image"
  rm -f "apps/$app/.env.production"
  gc run deploy "$service" --image "$image" --region "$REGION" --service-account "$SERVICE_ACCOUNT" \
    --allow-unauthenticated --memory 512Mi --cpu 1 --min-instances 0 --max-instances 3 \
    --labels app=agri-ai-network,component="$app"
}

ensure_repo
for t in "${TARGETS[@]}"; do
  case "$t" in
    api) deploy_api ;;
    farmer-web | officer-dashboard) deploy_app "$t" ;;
    *) echo "unknown target: $t (use api, farmer-web, officer-dashboard)" >&2; exit 2 ;;
  esac
done

echo
echo "API:               $API_URL  (health: $API_URL/health, docs: $API_URL/docs)"
echo "Farmer app:        $FARMER_URL"
echo "Officer dashboard: $OFFICER_URL"
curl -fsS "$API_URL/health" && echo
