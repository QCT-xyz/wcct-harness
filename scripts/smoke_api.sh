#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
. .venv/bin/activate
need_kill=0
if ! pgrep -f "uvicorn.*poisson_api.main:app" >/dev/null 2>&1; then
  ./scripts/run_api.sh >/dev/null 2>&1 &
  echo $! > .uvicorn.pid
  need_kill=1
fi
for i in $(seq 1 40); do
  code=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8000/healthz || true)
  [ "$code" = "200" ] && break
  sleep 0.25
done
resp=$(curl -s http://127.0.0.1:8000/healthz)
python - "$resp" <<'PY'
import sys, json
d = json.loads(sys.argv[1])
assert d.get("ok") is True
print("healthz_ok")
PY
resp=$(curl -s -X POST http://127.0.0.1:8000/solve -H "Content-Type: application/json" -d '{"N":64,"steps":400,"omega":1.9}')
python - "$resp" <<'PY'
import sys, json
r = json.loads(sys.argv[1])
p = float(r["onnx_parity"])
t = float(r["rel_to_truth"])
assert 0 <= p < 1e-5
assert 0 <= t < 1e-4
print("solve_ok", p, t)
PY
resp=$(curl -s -X POST http://127.0.0.1:8000/v1/xi/step -H "Content-Type: application/json" -d '{"N":96,"T":150,"lam":0.2,"m2":0.0,"dt":0.1,"seed":42}')
python - "$resp" <<'PY'
import sys, json, math
r = json.loads(sys.argv[1])
xf = float(r["xi_final"])
xm = float(r["xi_mean"])
steps = int(r["steps"])
assert steps == 150
assert math.isfinite(xf) and 0.0 <= xf < 0.5
assert math.isfinite(xm) and 0.0 <= xm < 0.5
print("xi_ok", xf, xm)
PY
echo "SMOKE_PASS"
if [ "$need_kill" = "1" ]; then
  pkill -f "uvicorn.*poisson_api.main:app" || true
  rm -f .uvicorn.pid
fi
