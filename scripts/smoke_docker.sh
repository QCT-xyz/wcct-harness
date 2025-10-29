#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

docker compose up -d

PORT=$(docker compose port api 8000 | awk -F: 'NF{print $NF}' | tail -n1)
if [ -z "${PORT:-}" ]; then
  echo "ERR: could not determine mapped port for api:8000"
  docker compose ps
  exit 1
fi

ready=0
for i in $(seq 1 60); do
  code=$(curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:$PORT/healthz" || true)
  [ "$code" = "200" ] && ready=1 && break
  sleep 0.5
done
if [ "$ready" != "1" ]; then
  echo "ERR: /healthz never returned 200 on port $PORT"
  docker compose logs --no-color api | tail -n 80 || true
  exit 1
fi

resp=$(curl -s "http://127.0.0.1:$PORT/healthz")
python - "$resp" <<'PY'
import sys, json
d = json.loads(sys.argv[1])
assert d.get("ok") is True
print("docker_healthz_ok")
PY

resp=$(curl -s -X POST "http://127.0.0.1:$PORT/solve" -H "Content-Type: application/json" -d '{"N":64,"steps":400,"omega":1.9}')
python - "$resp" <<'PY'
import sys, json
r = json.loads(sys.argv[1])
p = float(r["onnx_parity"])
t = float(r["rel_to_truth"])
assert 0 <= p < 1e-5
assert 0 <= t < 1e-4
print("docker_solve_ok", p, t)
PY

resp=$(curl -s -X POST "http://127.0.0.1:$PORT/v1/xi/step" -H "Content-Type: application/json" -d '{"N":96,"T":150,"lam":0.2,"m2":0.0,"dt":0.1,"seed":42}')
python - "$resp" <<'PY'
import sys, json, math
r = json.loads(sys.argv[1])
xf = float(r["xi_final"])
xm = float(r["xi_mean"])
steps = int(r["steps"])
assert steps == 150
assert math.isfinite(xf) and 0.0 <= xf < 0.5
assert math.isfinite(xm) and 0.0 <= xm < 0.5
print("docker_xi_ok", xf, xm)
PY

echo "DOCKER_SMOKE_PASS on port $PORT"
