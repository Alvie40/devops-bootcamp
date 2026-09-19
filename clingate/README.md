# ClinGate

Clinical data ingestion gateway: a **lab platform** for practicing DevSecOps and scalability on
regulated health data. Two inbound adapters (HL7 v2 over MLLP, device JSON over HTTPS) feed one
pipeline: durable raw store → queue → worker → Postgres (RLS) → HL7 export.

> Lab and design proposal. Not deployed anywhere, synthetic data only. See
> [docs/SPEC.md](docs/SPEC.md) §1.2 for exactly what may and may not be claimed about it.

Docs: [SPEC](docs/SPEC.md) · [SECURITY](docs/SECURITY.md) · [LOADTEST](docs/LOADTEST.md)

## Quickstart (NavyBlue / any Mac with Docker + uv)

```bash
make sync              # install deps (uv, Python 3.12)
make test              # 91 unit + in-process end-to-end tests, ~4 s, no docker
make test-integration  # Postgres: RLS isolation, idempotency, INSERT-only audit, partitions
make dev-up-aws        # LocalStack (S3/SQS + DLQs) + Postgres
make smoke-aws         # 5 real processes + LocalStack + Postgres, then reconcile I1-I4
make baseline-sweep    # single-pod (0.5 vCPU) capacity sweep with k6 in docker
make ci                # lint + tests + gitleaks + semgrep + trivy + SBOM (installed tools only)
make help
```

## Layout

```
apps/clingate_lib/     hl7 (strict parser/builder/ACK/scrub), mllp, ids, logging (PHI-safe),
                       audit, ports + memory/aws adapters, repo (memory/postgres), consumer
apps/ingest_api/       FastAPI: JWT authz, durable S3 write, enqueue pointer, 202 (never touches the DB)
apps/mllp_listener/    mTLS-capable MLLP server: scrub → durable write → enqueue → ACK AA/AE/AR
apps/clingate_worker/  idempotent parse + one-transaction commit + export intents
apps/hl7_exporter/     per-destination connection pool, circuit breaker, ACK handling
apps/clingate_ops/     migrate, reconcile (I1-I4), devdb (dev reset + seed)
sim/clingate_sim/      sink-sim, sender-sim (backlog dump + ledger), seeded generator, dev auth
db/migrations/         schema, RLS (FORCE), partitioning, grants
loadtest/              k6 script (open model, thresholds) + single-pod sweep
dev/                   clients, seed, postgres/localstack init, smoke script
```

## What P1 delivers, and what it does not

Delivered and verified: the four apps, the shared libraries, the simulators, the reconciliation
tool, the local pipeline, and a single-pod capacity baseline (LOADTEST.md §3.3).

Deferred (tracked in SPEC §11): `GET` endpoints and the operator read API with audit (needs the
Postgres audit writer wired into the API), the `replay`/`redrive-dlq` jobs, Helm/kind manifests
(P3), Terraform (P2), image signing/attestation in CI (P3), mTLS proven end to end with real certs
(the TLS code path exists in the listener; only the plain-TCP dev path is exercised in tests).

## Invariants that are tested (and mutation-checked)

| Id | Invariant | Where |
|---|---|---|
| FR-3 / H1 | ACK/202 only after the raw object is durable **and** enqueued | listener + API tests |
| FR-4 / H2 | Duplicates are harmless; redelivery after a crash converges | worker, exporter, pg integration |
| H3 | Tenant isolation is enforced by Postgres, not by the app | pg integration (RLS, FORCE) |
| H4 | Checksum mismatch → quarantine, never silently processed | worker |
| H6 | Direct identifiers never reach S3, queues, logs, or the far end | listener, logging, e2e |
| H8 | Parser only ever raises `Hl7Error` on hostile input | Hypothesis fuzz |

Notes: moto does not emulate S3 checksum enforcement; that and the DLQ redrive policy are
covered against LocalStack (`tests/integration/test_localstack.py`). LocalStack is an emulator, not AWS.
