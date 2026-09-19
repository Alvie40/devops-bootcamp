#!/usr/bin/env bash
# Full local stack, real processes: LocalStack (S3/SQS) + Postgres + ingest-api + mllp-listener +
# worker + exporter + sink-sim. Sends HTTP batches and an MLLP backlog dump, waits for the pipeline
# to drain, then reconciles the sent-ledgers against S3 and the database. Exit 0 only if I1-I4 hold.
set -uo pipefail
cd "$(dirname "$0")/.."
export AWS_ENDPOINT_URL=http://localhost:4566 AWS_ACCESS_KEY_ID=test AWS_SECRET_ACCESS_KEY=test AWS_DEFAULT_REGION=us-east-1
export CLINGATE_BACKEND=aws CLINGATE_RAW_BUCKET=clingate-raw-dev
export CLINGATE_INGEST_QUEUE_URL=$AWS_ENDPOINT_URL/000000000000/clingate-ingest
export CLINGATE_EXPORT_QUEUE_URL=$AWS_ENDPOINT_URL/000000000000/clingate-export
export CLINGATE_DB_DSN=postgresql://app_rw:dev-app@127.0.0.1:55432/clingate
export CLINGATE_CLIENTS_FILE=dev/clients.json CLINGATE_PROCESSING_ID=T
export CLINGATE_JWKS_FILE=dev/.keys/jwks.json CLINGATE_JWT_ISSUER=https://dev.clingate.local
export CLINGATE_DEV_CLIENT=dev-lab-client
TENANT=11111111-1111-1111-1111-111111111111
SEED=$(date +%s); MLLP_N=${MLLP_N:-200}; HTTP_N=${HTTP_N:-20}
LOG=build/smoke; mkdir -p "$LOG" loadtest/out
PIDS=()
cleanup() { for p in "${PIDS[@]}"; do kill "$p" 2>/dev/null; done; wait 2>/dev/null; }
trap cleanup EXIT

docker compose up -d --wait postgres >/dev/null
docker compose --profile aws up -d --wait localstack >/dev/null
uv run python -m clingate_sim.devauth dev-device-client >/dev/null
CLINGATE_MIGRATOR_DSN=postgresql://migrator:dev-migrator@127.0.0.1:55432/clingate uv run python -m clingate_ops.devdb
uv run python - <<'PY'
import boto3
sqs = boto3.client("sqs")
for q in ("clingate-ingest", "clingate-export"):
    sqs.purge_queue(QueueUrl=f"http://localhost:4566/000000000000/{q}")
PY

start() { name=$1; shift; "$@" >"$LOG/$name.log" 2>&1 & PIDS+=($!); }
start sink     uv run python -m clingate_sim.sink --port 2576 --latency-ms 5
start api      env PORT=8000 uv run python -m ingest_api
start listener env PORT=2575 uv run python -m mllp_listener
start worker   uv run python -m clingate_worker
start exporter uv run python -m hl7_exporter
for port in 8000 2575 2576; do
  for _ in $(seq 60); do (echo > /dev/tcp/127.0.0.1/$port) 2>/dev/null && break; sleep 0.5; done
done

echo "== sending $HTTP_N HTTP batches and an MLLP backlog of $MLLP_N (4 connections)"
uv run python - "$SEED" "$HTTP_N" <<'PY'
import json, sys, httpx
from clingate_sim.devauth import DevKeys
from clingate_sim.generate import device_batch
seed, n = int(sys.argv[1]), int(sys.argv[2])
tok = DevKeys.load_or_create("dev/.keys").mint("dev-device-client")
rows = []
with httpx.Client(base_url="http://127.0.0.1:8000") as c:
    for i in range(n):
        key, body = device_batch(seed, i, n_obs=30)
        r = c.post("/v1/batches", content=body, headers={"Authorization": f"Bearer {tok}", "Idempotency-Key": key})
        rows.append({"idempotency_key": key, "status": r.status_code})
open("loadtest/out/ledger-http.jsonl", "w").write("\n".join(json.dumps(x) for x in rows) + "\n")
print("http statuses:", sorted({r["status"] for r in rows}))
PY
uv run python -m clingate_sim.sender --count "$MLLP_N" --connections 4 --seed "$SEED" --ledger loadtest/out/ledger-mllp.jsonl

echo "== waiting for the pipeline to drain, then reconciling"
EXPECTED=$(( MLLP_N * 12 + HTTP_N * 30 ))
rc=1
for _ in $(seq 40); do
  if uv run python -m clingate_ops.reconcile --ledger loadtest/out/ledger-mllp.jsonl --tenant $TENANT \
       --source mllp --expected-observations $EXPECTED >"$LOG/reconcile-mllp.txt" 2>&1 \
     && uv run python -m clingate_ops.reconcile --ledger loadtest/out/ledger-http.jsonl --tenant $TENANT \
       --source http >"$LOG/reconcile-http.txt" 2>&1; then rc=0; break; fi
  sleep 1
done
echo "-- mllp"; cat "$LOG/reconcile-mllp.txt"; echo "-- http"; cat "$LOG/reconcile-http.txt"
exit $rc
