SHELL := /bin/bash
UV ?= uv
COMPOSE ?= docker compose
TEST_DSN := postgresql://migrator:dev-migrator@127.0.0.1:55432/clingate_test
TEST_APP_DSN := postgresql://app_rw:dev-app@127.0.0.1:55432/clingate_test

.DEFAULT_GOAL := help
.PHONY: help sync lint fmt test test-integration ci db-up db-down migrate token baseline baseline-sweep mllp-sweep worker-db-sweep dev-up-aws smoke-aws sink loadtest-mllp clean

help: ## list targets
	@grep -E '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  %-18s %s\n", $$1, $$2}'

sync: ## install dependencies
	$(UV) sync

lint: ## ruff check + format check
	$(UV) run ruff check apps sim tests loadtest
	$(UV) run ruff format --check apps sim tests loadtest

fmt: ## auto-format
	$(UV) run ruff check --fix apps sim tests loadtest && $(UV) run ruff format apps sim tests loadtest

test: ## unit + e2e (in-process, no docker)
	$(UV) run pytest tests/unit -q

db-up: ## start dev Postgres
	$(COMPOSE) up -d --wait postgres

db-down: ## stop dev Postgres and delete its data
	$(COMPOSE) down -v

test-integration: db-up ## Postgres integration tests (RLS, idempotency, partitions)
	CLINGATE_TEST_DSN=$(TEST_DSN) CLINGATE_TEST_APP_DSN=$(TEST_APP_DSN) $(UV) run pytest tests/integration -q

migrate: db-up ## apply migrations to the dev database
	CLINGATE_MIGRATOR_DSN=postgresql://migrator:dev-migrator@127.0.0.1:55432/clingate $(UV) run python -m clingate_ops.migrate

ci: lint test test-integration ## local pipeline: lint, tests, then the security gates that are installed
	@if command -v gitleaks >/dev/null; then gitleaks dir . --config .gitleaks.toml --no-banner --redact; else echo "skip gitleaks (not installed)"; fi
	@if command -v semgrep >/dev/null; then semgrep scan --config auto --error --quiet apps sim; else echo "skip semgrep (not installed)"; fi
	@if command -v trivy >/dev/null; then trivy fs --scanners vuln,secret,misconfig --severity HIGH,CRITICAL --skip-dirs .venv,dev/.keys,build,loadtest/out --exit-code 1 --quiet .; else echo "skip trivy (not installed)"; fi
	@if command -v syft >/dev/null; then syft dir:. --source-name clingate --source-version $$(git rev-parse --short HEAD) -o cyclonedx-json=build/sbom.cdx.json -q && echo "SBOM: build/sbom.cdx.json"; fi

token: ## mint a dev access token (24h) for dev-device-client
	@$(UV) run python -m clingate_sim.devauth dev-device-client 86400

baseline: ## single-pod capacity baseline: 0.5 vCPU container + k6 (RATE=50 or STAGES=60:50,60:100)
	@mkdir -p loadtest/out build
	@$(UV) run python -m clingate_sim.devauth dev-device-client 86400 >/dev/null   # ensures dev/.keys exists
	TOKEN=$$($(UV) run python -m clingate_sim.devauth dev-device-client 86400) \
	  $(COMPOSE) --profile baseline up --build --abort-on-container-exit --exit-code-from k6 k6
	$(COMPOSE) --profile baseline down

baseline-sweep: ## sweep arrival rates against one 0.5 vCPU pod to find the knee (RATES="50 100 200" DUR=20)
	./loadtest/sweep.sh

mllp-sweep: ## hypothesis 2: MLLP serial-ACK ceiling vs connections (ACK_LATENCY_MS=20)
	$(UV) run python loadtest/mllp_sweep.py

worker-db-sweep: db-up ## hypothesis 1: worker -> Postgres throughput vs concurrency (N=1500)
	$(UV) run python loadtest/worker_db_sweep.py

dev-up-aws: db-up ## start LocalStack (S3/SQS + DLQs) next to Postgres
	$(COMPOSE) --profile aws up -d --wait localstack

smoke-aws: ## full local stack, real processes, reconcile against S3 + Postgres
	./dev/smoke.sh

sink: ## downstream interface-engine simulator on :2576 (LATENCY_MS, AE_RATE, AR_RATE)
	$(UV) run python -m clingate_sim.sink --port 2576 --latency-ms $${LATENCY_MS:-0} --ae-rate $${AE_RATE:-0} --ar-rate $${AR_RATE:-0}

loadtest-mllp: ## partner-lab backlog dump against a listener on :2575 (COUNT, CONNECTIONS)
	@mkdir -p loadtest/out
	$(UV) run python -m clingate_sim.sender --count $${COUNT:-1000} --connections $${CONNECTIONS:-1}

clean: ## remove caches and build output
	rm -rf .pytest_cache .ruff_cache build loadtest/out
