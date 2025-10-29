.PHONY: lab run api smoke test dbuild dup ddown dlogs dsmoke clean
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
dbuild:
	docker build -t wcct-api:latest .
dup:
	docker compose up -d
ddown:
	docker compose down
dlogs:
	docker compose logs -f
dsmoke:
	./scripts/smoke_docker.sh
clean:
	rm -rf artifacts/*
