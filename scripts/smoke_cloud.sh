#!/usr/bin/env bash
set -euo pipefail
PROJECT_ID="decent-surf-467802-h9"
REGION="us-central1"
API_URL="$(gcloud run services describe wcct-api --project "$PROJECT_ID" --region "$REGION" --format='value(status.url)')"
SA="wcct-ui-sa@$PROJECT_ID.iam.gserviceaccount.com"
TOK="$(gcloud auth print-identity-token --impersonate-service-account="$SA" --audiences="$API_URL")"
echo "api $API_URL"
echo -n "healthz "
curl -s -o /dev/null -w "%{http_code}\n" -H "Authorization: Bearer $TOK" "$API_URL/healthz" || true
echo "solve"
curl -s -H "Authorization: Bearer $TOK" -H "Content-Type: application/json" -d '{"N":64,"steps":400,"omega":1.9}' "$API_URL/solve"
