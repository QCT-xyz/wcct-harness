.PHONY: lab run api smoke test clean
lab:
	. .venv/bin/activate && python -m jupyterlab
run:
	. .venv/bin/activate && ./scripts/run_all.sh
api:
	./scripts/run_api.sh
smoke:
	. .venv/bin/activate && ./scripts/smoke_api.sh
test:
	. .venv/bin/activate && ./scripts/test_api.sh
clean:
	rm -rf artifacts/*
