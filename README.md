# WCCT Notebook Harness and API

[![publish](https://github.com/QCT-xyz/wcct-harness/actions/workflows/publish.yml/badge.svg)](https://github.com/QCT-xyz/wcct-harness/actions/workflows/publish.yml)

Minimal, reproducible WCCT diagnostics with six notebooks, an ONNX Poisson solver served via FastAPI, a small Dash UI, smoke tests, Docker, and Cloud Run deploys. Everything has pass criteria and runs headless.

---

## Quick start (local)

```bash
cd "$HOME/wcct"
. .venv/bin/activate
make run      # execute all notebooks, write artifacts/report.json
make smoke    # hit local API: /healthz, /solve, /v1/xi/step
make test     # pytest for API contract
make api      # start FastAPI locally on 127.0.0.1:8000
make ui       # start Dash UI on 127.0.0.1:8050
```

Environment pins (Python 3.13):
- numpy 2.1.0
- scipy 1.14.1
- matplotlib 3.10.7
- jupyterlab 4.1.6
- ipykernel 6.29.5
- onnx >= 1.16.0
- onnxruntime 1.23.2
- numba 0.61.0
- networkx 3.2.1
- fastapi 0.120.1
- uvicorn 0.38.0
- nbclient 0.10.0
- dash 2.17.1
- requests 2.32.3

---

## Layout

```
wcct/
  notebooks/
    00_env_check.ipynb
    01_xi_nlkg.ipynb
    02_poisson_onnx.ipynb
    03_yukawa_lensing.ipynb
    04_bao_anisotropy.ipynb
    05_potential_flow.ipynb
  services/
    poisson_api/main.py        # FastAPI with /solve and /v1/xi/*
    ui_app/app.py              # Dash UI that calls the API
  scripts/
    run_all.py                 # batch notebook executor
    run_all.sh                 # wrapper
    run_api.sh                 # start API locally
    smoke_api.sh               # local API smoke
    test_api.sh                # pytest runner
    run_ui.sh                  # start UI locally
    smoke_docker.sh            # container smoke
    smoke_cloud.sh             # Cloud Run API smoke with SA impersonation
  artifacts/
    executed/                  # executed notebooks
    report.json                # harness summary
    poisson_jacobi.onnx        # exported ONNX model
  .github/workflows/ci.yml     # CI runs notebooks and pytest
  Dockerfile                   # API container
  Dockerfile.ui                # UI container
  docker-compose.yml           # local compose, api on 8001:8000
  requirements.txt
  requirements.api.txt
  requirements.ui.txt
  README.md
```

---

## Notebooks and pass criteria

- 00_env_check  
  Prints versions and runs a small CG solve. Pass on clean execution.

- 01_xi_nlkg  
  Nonlinear Klein Gordon toy with coherence index Xi. Pass on finite Xi and completion.

- 02_poisson_onnx  
  Red black SOR Poisson in NumPy and ONNX with parity check.  
  Pass if:
  - onnx_parity < 1e-6  
  - rel_to_truth < 5e-2

- 03_yukawa_lensing  
  Residuals for a repulsive Yukawa like term.  
  Pass if resid_rms > 1e-5

- 04_bao_anisotropy  
  Toy E/B style parity from an anisotropic ring.  
  Pass if E_over_B > 1.05

- 05_potential_flow  
  Cosmograph style potential flow from Gaussian sources.  
  Pass if finite fields and rel_curl < 5e-2

Executed copies live in `artifacts/executed/` with a summary in `artifacts/report.json`.

---

## Local API

Start:
```bash
make api
```

Endpoints:
- GET `/healthz`  
- POST `/solve`  
  Body: `{"N":64,"steps":400,"omega":1.9}`  
  Returns: parity vs ONNX, rel_to_truth, moments, hist
- POST `/v1/xi/step`  
  Body: `{"N":96,"T":150,"lam":0.2,"m2":0.0,"dt":0.1,"seed":42}`
- POST `/v1/xi/series`  
  Same fields, returns series

Quick check:
```bash
curl -s http://127.0.0.1:8000/healthz
curl -s -X POST http://127.0.0.1:8000/solve -H "Content-Type: application/json" -d '{"N":64,"steps":400,"omega":1.9}'
curl -s -X POST http://127.0.0.1:8000/v1/xi/step -H "Content-Type: application/json" -d '{"N":96,"T":150,"lam":0.2,"m2":0.0,"dt":0.1,"seed":42}'
```

Expected local numbers:
- onnx_parity about 6.46e-07
- rel_to_truth about 7.76e-07
- xi_final about 0.086, xi_mean about 0.042 for T=150

---

## Local UI

Start:
```bash
make ui
```

Open http://127.0.0.1:8050 and run:
- Poisson RB SOR: N=64, steps=400, omega=1.9  
- Xi series: N=96, T=150

If your API is running in Docker on 8001:
```bash
API_BASE=http://127.0.0.1:8001 make ui
```

---

## Docker

Build and run:
```bash
make dbuild
make dup
make dsmoke
```

`dsmoke` auto detects the mapped port and checks:
- `/healthz`
- `/solve`
- `/v1/xi/step`

---

## CI

`.github/workflows/ci.yml` runs:
- pip install from `requirements.txt`
- `python scripts/run_all.py`
- `pytest`

You can extend it to build and push containers after tests pass.

---

## Cloud: project, images, deploy

- Project id: `decent-surf-467802-h9`  
- Region: `us-central1`  
- Artifact Registry repo: `wcct`  
- Services:
  - `wcct-api` private IAM  
  - `wcct-ui` private IAM

Images are built with Cloud Build using `cloudbuild.yaml` and pushed to `us-central1-docker.pkg.dev/decent-surf-467802-h9/wcct`.

---

## Access in Cloud Run (IAM gated UI)

UI URL:
```bash
gcloud run services describe wcct-ui --project "decent-surf-467802-h9" --region "us-central1" --format='value(status.url)'
```

Allowlist a viewer:
```bash
gcloud run services add-iam-policy-binding wcct-ui   --member="user:YOUR_EMAIL"   --role="roles/run.invoker"   --region "us-central1" --project "decent-surf-467802-h9"
```

Browse with proxy:
```bash
gcloud run services proxy wcct-ui --region "us-central1" --project "decent-surf-467802-h9"
# then open http://127.0.0.1:8080
```

Curl the UI with a token using service account impersonation:
```bash
UI_URL="$(gcloud run services describe wcct-ui --project "decent-surf-467802-h9" --region "us-central1" --format='value(status.url)')"
SA="wcct-ui-sa@decent-surf-467802-h9.iam.gserviceaccount.com"
TOK="$(gcloud auth print-identity-token --impersonate-service-account="$SA" --audiences="$UI_URL")"
curl -s -o /dev/null -w "%{http_code}
" -H "Authorization: Bearer $TOK" "$UI_URL"
```

Programmatic call to the private API:
```bash
API_URL="$(gcloud run services describe wcct-api --project "decent-surf-467802-h9" --region "us-central1" --format='value(status.url)')"
SA="wcct-ui-sa@decent-surf-467802-h9.iam.gserviceaccount.com"
TOK="$(gcloud auth print-identity-token --impersonate-service-account="$SA" --audiences="$API_URL")"
curl -s -H "Authorization: Bearer $TOK" -H "Content-Type: application/json"   -d '{"N":64,"steps":400,"omega":1.9}' "$API_URL/solve"
```

Notes:
- Always mint ID tokens with audience equal to the exact service URL you call.  
- Cloud Run IAM does not redirect to Google sign in. A bare curl without a token will return 401 or 403.  
- UI to API calls are already service to service with the UI service account.

---

## Troubleshooting

- Port 8000 in use  
  Stop local uvicorn or map the container to 8001:8000 with docker compose.

- 401 or 403 on Cloud Run  
  Use an ID token with Authorization: Bearer. The audience must equal the service URL. Make sure your principal has roles/run.invoker.

- 404 on /healthz in Cloud Run  
  The API is healthy if /solve works with the same token. You can switch readiness checks to a POST on /solve if needed.

- ONNX IR version  
  The model sets ir_version = 11. Keep onnxruntime at 1.23.2.

- SciPy API change  
  Use rtol and optional atol for CG, not tol.

- Headless plotting  
  If needed set MPLBACKEND=Agg for batch runs.

---

## License

Copyright 2025 QuantumCore Technologies.
All rights reserved.
