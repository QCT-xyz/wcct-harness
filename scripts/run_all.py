import os, json, time, nbformat as nbf
from nbclient import NotebookClient
root = os.path.dirname(os.path.abspath(__file__))
root = os.path.dirname(root)
nbdir = os.path.join(root, "notebooks")
outdir = os.path.join(root, "artifacts", "executed")
os.makedirs(outdir, exist_ok=True)
names = sorted([n for n in os.listdir(nbdir) if n.endswith(".ipynb")])
summary = []
for name in names:
    path = os.path.join(nbdir, name)
    out = os.path.join(outdir, name)
    nb = nbf.read(path, as_version=4)
    from jupyter_client.kernelspec import KernelSpecManager
    kn="wcct"
    if kn not in KernelSpecManager().get_all_specs():
        kn="python3"
    client = NotebookClient(nb, timeout=600, kernel_name=kn, resources={"metadata": {"path": nbdir}})
    ok = True
    err = ""
    try:
        client.execute()
    except Exception as e:
        ok = False
        err = str(e)
    nbf.write(nb, out)
    summary.append({"name": name, "ok": ok, "error": err})
rep = {"total": len(summary), "ok": sum(1 for s in summary if s["ok"]), "fail": [s for s in summary if not s["ok"]], "timestamp": time.time()}
os.makedirs(os.path.join(root, "artifacts"), exist_ok=True)
with open(os.path.join(root, "artifacts", "report.json"), "w") as f:
    json.dump(rep, f, indent=2)
print(json.dumps(rep, indent=2))
raise SystemExit(0 if rep["ok"] == rep["total"] else 1)
