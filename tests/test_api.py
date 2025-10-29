import os, subprocess, time, json, urllib.request
BASE = "http://127.0.0.1:8000"

def _wait_health(timeout=5.0):
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            with urllib.request.urlopen(BASE + "/healthz") as f:
                if f.getcode() == 200:
                    return True
        except Exception:
            time.sleep(0.1)
    return False

def setup_module(module):
    root = os.path.dirname(os.path.dirname(__file__))
    module.proc = subprocess.Popen([os.path.join(root, "scripts", "run_api.sh")])
    assert _wait_health()

def teardown_module(module):
    try:
        module.proc.terminate()
        module.proc.wait(timeout=5)
    except Exception:
        module.proc.kill()

def _post(path, payload):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(BASE + path, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as f:
        return json.loads(f.read().decode())

def test_healthz():
    with urllib.request.urlopen(BASE + "/healthz") as f:
        assert f.getcode() == 200
        d = json.loads(f.read().decode())
        assert d.get("ok") is True

def test_solve():
    r = _post("/solve", {"N": 64, "steps": 400, "omega": 1.9})
    assert 0 <= float(r["onnx_parity"]) < 1e-5
    assert 0 <= float(r["rel_to_truth"]) < 1e-4

def test_xi():
    r = _post("/v1/xi/step", {"N": 96, "T": 150, "lam": 0.2, "m2": 0.0, "dt": 0.1, "seed": 42})
    assert r["steps"] == 150
    assert 0.0 <= float(r["xi_final"]) < 0.5
    assert 0.0 <= float(r["xi_mean"]) < 0.5
