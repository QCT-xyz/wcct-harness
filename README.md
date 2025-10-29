# WCCT Notebook Harness

Self-contained mini-suite for WCCT diagnostics. Six notebooks with built-in sanity checks, a batch runner, and reproducible pins.

## Quick start

```bash
cd "$HOME/wcct"
. .venv/bin/activate
jupyter lab

Batch execute everything headless:

cd "$HOME/wcct"
./scripts/run_all.sh
cat artifacts/report.json

Environment

Python 3.13 with pinned wheels:
	•	numpy 2.1.0
	•	scipy 1.14.1
	•	matplotlib 3.10.7
	•	jupyterlab 4.1.6
	•	ipykernel 6.29.5
	•	onnx >= 1.16.0
	•	onnxruntime 1.23.2
	•	numba 0.61.0
	•	networkx 3.2.1

Kernel appears as: Python (wcct).

Layout

wcct/
  notebooks/
    00_env_check.ipynb
    01_xi_nlkg.ipynb
    02_poisson_onnx.ipynb
    03_yukawa_lensing.ipynb
    04_bao_anisotropy.ipynb
    05_potential_flow.ipynb
  scripts/
    run_all.py
    run_all.sh
  artifacts/
    executed/            # executed copies of notebooks
    report.json          # PASS/FAIL summary
  .venv/
  requirements.txt
  requirements.lock

Notebooks and pass criteria
	•	00_env_check
Prints library versions and runs a small CG solve. Pass if it executes without error.
	•	01_xi_nlkg
Nonlinear Klein-Gordon toy with coherence index Xi. Plot shows Xi rising and stabilizing. Pass if all Xi values are finite and the cell completes.
	•	02_poisson_onnx
Poisson solver with red-black SOR encoded in ONNX. Parity check compares NumPy and ONNX trajectories.
Pass if:
	•	onnx_parity < 1e-6
	•	rel_to_truth < 5e-2
	•	03_yukawa_lensing
Toy residuals for a repulsive Yukawa-like term. Pass if:
	•	resid_rms > 1e-5
	•	04_bao_anisotropy
Anisotropic ring power with E/B-style ratio. Pass if:
	•	E_over_B > 1.05
	•	05_potential_flow
Cosmograph-style potential flow from Gaussian sources. Pass if:
	•	finite velocities
	•	shapes consistent
	•	rel_curl < 5e-2

Artifacts
	•	Executed notebooks: artifacts/executed/*.ipynb
	•	Batch summary: artifacts/report.json
	•	ONNX model export: artifacts/poisson_jacobi.onnx

Reproducibility
	•	Seeds are fixed inside each demo.
	•	Versions are pinned and locked in requirements.lock.
	•	The batch harness executes notebooks in a clean kernel with kernel_name="wcct".

Troubleshooting
	•	ONNX IR version error
Ensure the model sets m.ir_version = 11 before creating the session.
	•	SciPy API change for CG
Use rtol and optionally atol rather than tol.
	•	Headless plotting
If needed, set MPLBACKEND=Agg before running the batch harness.

License

Copyright 2025 QuantumCore Technologies. All rights reserved.
