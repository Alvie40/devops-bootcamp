# ClinGate — Scale and Stress Test Plan

**Draft v0.1 · 2026-09** · Companion to [SPEC.md](SPEC.md) and [SECURITY.md](SECURITY.md)

Goal: **prove we identified the scalability bottleneck before it appeared** — by
writing predictions first, measuring second, fixing the top bottleneck, and re-measuring.
The deliverable is the *before/after curve*, not one big number.

---

## 1. Principles

1. **Hypothesis-first.** The ranked bottleneck table (§5) is committed *before* any run.
   The final report compares predicted vs measured.
2. **Correctness beats speed.** Health data: a fast run that loses or duplicates a
   record is a **failed** run. Every run ends with a reconciliation (§8).
3. **Open-model load.** Fixed arrival rate, not fixed virtual users. In a closed model
   the generator slows down when the system slows, hiding the latency you came to
   measure (coordinated omission).
4. **Generator is outside the target.** Load runs from a separate Fargate task in the
   same region — not inside the cluster under test, and never from a home connection.
5. **SLOs are defined before the run** (§6). Numbers without a threshold are anecdotes.
6. **Only staging is stressed.** Prod gets smoke and canary only.
7. **Synthetic, seeded, deterministic data.** Unique idempotency keys; ~1 % injected
   duplicates; a sent-ledger for every request.

---

## 2. Where each test runs

| Environment | What runs | Why |
|---|---|---|
| **dev (NavyBlue)** | Script development; **single-pod capacity baseline**; algorithmic profiling (N+1, lock contention, pool sizing) | Free; finds design errors early. Absolute numbers are *not* transferable to AWS. |
| **staging** | Load, spike, stress/breakpoint, dependency-failure, (optional) soak | Same shape as prod; the only stress target |
| **prod** | Smoke + synthetic canary after each promotion | Verify the deploy, not the limits |

Staging ≠ prod: extrapolation is reasonable for the stateless tier (API/workers);
**not** for the database or queues. The report states this explicitly.

---

## 3. Workload profiles

Volumes are **assumptions until replaced with real numbers** (marked TBD). Nothing here
is ADI data. Profile S is *sized from SatMed's business volumes* as a hypothetical
scenario — not a description of a deployed system.

### 3.1 Profile S — results ingestion (SatMed-sized scenario)

| Parameter | Symbol | Value |
|---|---|---|
| Exams per month | `E` | **TBD (from SatMed)** |
| Messages per exam | `M` | 1 `ORU^R01` (assumed) |
| Message size | `B` | ~3 KiB, ~20 `OBX` (assumed) |
| Share of monthly volume in the busiest 3 working days | `P` | **TBD** (assumed 0.40) |
| Working hours per day | `W` | 10 |

`peak_msg_per_s = E × M × P / (3 × W × 3600)`

**Honest expectation:** for a business of SatMed's plausible size the real peak is
well **below 1 msg/s** (illustration: `E = 50,000` → ~0.2 msg/s). So the scale test is
**not** "can we serve today's load" — that is trivial. It asks: **how much headroom does
the design have, and how does it fail beyond it?** Headroom multiples tested:
**1× · 10× · 100× · 1,000×** of the computed peak.

Profile-S-specific scenario — **backlog dump:** a single partner lab pushes `N` queued
messages back-to-back on few connections. MLLP waits for each ACK, so per-connection
throughput ≈ 1 / ACK latency (e.g., 20 ms ACK ≈ 50 msg/s ≈ 50,000 messages in ~17 min on
one connection; ~100 s on ten). This is the case where the *protocol*, not the
infrastructure, is the limit — and where "more connections + backpressure" is the answer.

### 3.2 Profile D — device streams (ADI-style scenario)

`steady_rps = D / 60` for `D` devices each posting one batch per minute (5–50 KiB).

| Fleet | Steady |
|---|---|
| 1,000 | ~17 rps |
| 10,000 | ~167 rps |
| 100,000 | ~1,667 rps |

**Reconnect storm:** fraction `f` of the fleet flushes `k` backlogged batches within
one minute → extra `D × f × k / 60` rps (e.g., `D = 100k, f = 0.2, k = 5` → ~1,667 rps
on top of steady). This is the realistic spike.

### 3.3 Initial targets (†, revised after the P1 baseline)

| Tier | Target |
|---|---|
| T1 — baseline | 200 rps sustained, 30 min |
| T2 — high | 1,000 rps sustained, 30 min |
| Spike | T1 → 1,000 rps in seconds, hold 5 min |
| Stress | Ramp from T1 until the knee; capped by ceilings and cost (§9) |

Bottom-up sizing: `pods_needed = target_rps / per_pod_rps / 0.7` (30 % headroom);
then check `maxReplicas` and every downstream limit can carry that many pods.

**Measured single-pod baseline (P1, 2026-09-18, NavyBlue, hypothesis 5 in isolation).**
`ingest-api` in a container limited to 0.5 vCPU / 1 GiB (Fargate-task-shaped), real JWT (RS256)
verification and schema validation, **null backend** (no S3/SQS latency), k6 open-model constant
arrival rate, 20 s per step (`make baseline-sweep`). Steps 250-400 are valid (`dropped_iterations` = 0):

| Arrival rate | Achieved | p50 | p99 | Errors |
|---|---|---|---|---|
| 250 rps | 249.9 | 1.4 ms | 69 ms | 0 |
| 300 rps | 299.9 | 1.3 ms | 86 ms | 0 |
| 350 rps | 349.9 | 1.2 ms | 178 ms | 0 |
| 400 rps | 399.9 | 1.1 ms | 294 ms | 0 |
| 600 rps* | 580 | 126 ms | 520 ms | 0 |

\* Indicative only: from an earlier sweep with too few pre-allocated VUs (250 dropped iterations), so it
fails the validity rule; it does show p50 leaving ~1 ms, i.e. server-side saturation.

Reading: p50 stays ~1 ms while p99 explodes: tail-latency saturation of a CPU-bound pod, with the
knee at **~350-400 rps per 0.5 vCPU**. Planning number with 30 % headroom: **~250 rps per pod**, so
T1 (200 rps) needs 1 pod (2 for AZ spread) and T2 (1,000 rps) needs >= 4. Suspected contributor
to the p99 blow-up: CFS CPU-quota throttling at a 0.5 vCPU limit (Fargate has the same shape);
**unverified**, check `cpu.stat` throttling counters before claiming it.

Limits of this number: no S3/SQS round trips (the real path adds a synchronous S3 PUT, so expect a
lower per-pod ceiling and thread-pool pressure, i.e. hypothesis 6), Docker Desktop VM on Apple
silicon (arm64), generator and target share the host. It bounds the *API CPU* term only; it says
nothing about Aurora or MLLP. Re-measure with LocalStack, then in staging.

### 3.4 Local experiments (P1, NavyBlue, $0)

Run with `make mllp-sweep` and `make worker-db-sweep`. Docker Postgres and Python processes on a
laptop: they rank *where the design bends*, they do not predict Aurora or Fargate numbers.

**MLLP, sink with a 20 ms ACK** (hypothesis 2): throughput tracks `connections / latency`.

| Connections | msg/s | Predicted |
|---|---|---|
| 1 | 43 | 48 |
| 4 | 175 | 190 |
| 16 | 734 | 762 |
| 32 | 1,470 | 1,524 |

**Listener ceiling** (null backend, no network latency): ~4,200 msg/s for one process, flat whether
1, 2 or 4 sender processes push (so the limit is the listener's parse + scrub CPU, not the
generator). Scale is more pods, not more connections.

**Worker -> Postgres**, one process, k threads and k pooled connections (`ingest/s`, 12 obs/msg):

| Threads | ingest/s | p50 | p99 |
|---|---|---|---|
| 1 | 216 | 4.4 ms | 9.5 ms |
| 4 | 517 | 7.5 ms | 13.9 ms |
| 8 | 604 | 12.8 ms | 25 ms |
| 16 | 494 | 31.9 ms | 46.9 ms |

Past 8 the process **gets worse** (pool thrash + GIL): a bigger pool is not a faster worker, which is
why the pool cap is a design constraint. **Control:** 8 threads x P processes gives 614 / 1,080 /
1,436 ingest/s for P = 1 / 2 / 3, near-linear, so the per-process ceiling was Python CPU, not the
database. Postgres in Docker absorbed ~17k observation rows/s without p50 blowing up (12 -> 16 ms).

What this changes:
- **Prediction refined.** I ranked Aurora first. Measured, the worker's own CPU saturates first; the
  database becomes the shared limit only as pods are added, and where that happens is untested
  (needs Aurora at its real min/max ACU).
- **Size the DB in rows/s, not requests/s.** One HTTP batch is 30 rows: 1,000 rps = 30,000 rows/s
  = ~2.6 billion rows/day. That is a storage-volume problem before it is a throughput problem, so
  per-sample rows suit low-rate clinical vitals; high-rate raw sensor data belongs in S3 (the
  presigned-PUT path in SPEC §4) with the database holding summaries. **Design decision still open.**
- **Capacity model per process** (local, indicative): API ~250 rps safe, listener ~4,000 msg/s,
  worker ~600 ingest/s at 12 obs. Multiply by pods, then re-measure in staging.

---

## 4. Test catalog

| Test | Shape | Answers |
|---|---|---|
| **Smoke** | 1 rps, 1 min | Deploy works (every deploy, including prod) |
| **Load-lite (perf gate)** | ~T1 for ~5 min, thresholds | Regression gate before promotion |
| **Load** | T1 and T2, 30 min | Do we meet SLOs at expected peak? |
| **Stress / breakpoint** | Ramp until the knee | Where and **how** it breaks (graceful vs data loss) |
| **Spike** | T1 → 5× instantly | Autoscaling reaction time; error window |
| **Backlog dump** (S) | Few connections, large N | MLLP serial-ACK ceiling; backpressure |
| **Dependency failure** | Load + sink slow/down; kill a worker/exporter pod; Aurora failover (if available) | Queue absorbs; DLQ works; nothing lost |
| **Soak** *(optional)* | Moderate load, ~2 h | Leaks, pool exhaustion, queue drift |

---

## 5. Bottleneck hypotheses (predicted before measuring)

Ranked by my expected order of failure. The report fills the last two columns.

| # | Hypothesis | Expected signature | Mitigation to test | Measured? | Confirmed? |
|---|---|---|---|---|---|
| 1 | **Aurora**: `pods × pool` exceeds connection limits; ACU scaling lags | `queue_oldest_age` rises, worker timeouts, "too many connections" | Batch inserts, pool cap, PgBouncer/RDS Proxy, ACU min/max | Local only (Docker Postgres, not Aurora): see §3.4 | **Not confirmed as the first limit.** Worker CPU (Python parse, GIL) hit first; DB scaled to >= 1,400 ingest/s with 3 processes. Aurora ACU behavior still open (staging) |
| 2 | **MLLP serial ACK** (inbound and outbound) | `export-q` grows while everything else is green; per-connection rate flat at ~1/RTT | More connections, per-destination pool, `BHS/BTS` batching, backpressure | Yes, locally (§3.4) | **Confirmed**: throughput = connections / ACK latency (43 msg/s at 1 conn, 1,470 at 32, 20 ms ACK) |
| 3 | **Autoscaling lag** (Fargate cold start, scaler polling, LB scale) | 5xx/latency only in the first 1–2 min of a spike | Higher min replicas, pre-scale, KEDA on backlog | | |
| 4 | **KMS / S3**: per-object KMS calls hit request quotas and cost; per-prefix PUT ceiling | KMS throttling; cost above estimate | Bucket Keys (already in design), prefix hashing, aggregation | | |
| 5 | **`ingest-api` CPU**: JWT verify (RS256) + JSON validation | API CPU pegged before any other resource | JWKS cache, lean validation, more pods | | |
| 6 | **Synchronous S3 durable write** dominates p99 | p99 tracks `durable_write_latency` | Keep (durability wins); tune client, pool, region-local | | |
| 7 | **Cognito** token endpoint limits | 429 at token fetch | Pre-mint tokens; never fetch per request | | |
| 8 | **Service Quotas** (new-account vCPU) | Pods stuck `Pending` | Verify/raise before P3 | | |
| 9 | **Audit stream volume** (Logs → Firehose) at high request rate | Audit lag or throttling | Batch audit events; sample non-PHI access | | |

(SQS standard queues are not expected to bottleneck; FIFO was avoided for that reason.)

---

## 6. SLOs and pass/fail thresholds

Defined before any run (†, initial):

| SLI | Threshold |
|---|---|
| `POST /v1/batches` p99 latency | < 300 ms |
| HTTP error rate (5xx + timeouts) | < 0.1 % |
| `dropped_iterations` (generator couldn't keep up) | 0 — otherwise the run is **invalid** |
| End-to-end ingest → downstream ACK p95 | < 60 s at steady state |
| Oldest queue message age (steady) | < 2 min |
| **Reconciliation invariants (§8)** | **All hold. Any violation fails the run regardless of latency.** |

k6 thresholds encode the first four as code; the load-lite subset is the pipeline gate.

**Stress termination (stop the ramp when any occurs):** p99 > 5× SLO for 2 min · error
rate > 5 % · `dropped_iterations` climbing · burn-rate ceiling reached · 30-minute cap.

---

## 7. Harness

| Piece | Tool | Notes |
|---|---|---|
| HTTP load | **k6** — `constant-arrival-rate` / `ramping-arrival-rate`, `preAllocatedVUs`/`maxVUs` sized so VUs never saturate | Thresholds → exit code → gate |
| MLLP load | Python `sender-sim` (asyncio, N connections, controllable rate/backlog) | k6 speaks HTTP; MLLP needs a real TCP client |
| Downstream simulator | `sink-sim` with latency/error/ACK-code knobs | Also drives dependency-failure tests |
| Auth | Pre-mint N Cognito tokens (long-ish validity), distribute across VUs | Avoids hitting the token endpoint |
| Data | Seeded generator; unique idempotency keys; ~1 % duplicates | Deterministic expected counts |
| Sent-ledger | JSONL per run: `idempotency_key, t_sent, status/ack` → S3 | Ground truth for reconciliation |
| Location | Separate Fargate task, same region/AZs, targets the ALB/NLB | Not inside the cluster under test |
| Observability | CloudWatch dashboards as code (USE per resource) + k6 summary JSON | One "load test" dashboard |

---

## 8. Reconciliation (run after every test, after queues drain)

Invariants:

| ID | Invariant |
|---|---|
| I1 | Every ledger entry acknowledged (`2xx`/`AA`) has a raw S3 object whose SHA-256 matches |
| I2 | Each unique idempotency key maps to **exactly one** `ingest_events` row (injected duplicates collapsed) |
| I3 | `observations` count equals the generator's expected count from the seed |
| I4 | Every export is `acked` or sits in the DLQ (accounted) — **nothing pending** after drain |
| I5 | `audit_events` ≥ number of reads issued during the run |
| I6 | No PHI-pattern matches in the run's log output (log-scan) |

Output: a pass/fail table plus the offending keys for any violation.

---

## 9. Cost model and guards

Layered controls (SPEC §8.3). **Billing data lags, so Budgets is an audit trail, not a
brake.** The brakes are architectural and in the harness.

| Guard | Mechanism |
|---|---|
| Scale ceilings | `maxReplicas` per deployment; Aurora max ACU (e.g., 4) |
| Time box | 30-minute hard cap per run; harness aborts on computed burn rate |
| Teardown | `make down` after each session; nightly dead-man's-switch destroy |
| Detection | AWS Budgets + Cost Anomaly Detection (after-the-fact) |
| Data path cost | S3 via **gateway endpoint** (free, bypasses NAT); Bucket Keys cut KMS requests |

Order of magnitude per 30-minute run: low single to low double digits of USD,
dominated by **request-priced services (SQS, KMS-if-not-bucket-keyed, Logs)** rather than
compute. Figures come from memory of list prices and **must be re-checked in the AWS
Pricing Calculator** before the first run. Target ≤ $15/run.

Pre-flight checklist per run: quotas confirmed · ceilings set · dead-man's-switch armed ·
dashboards deployed · tokens minted · ledger bucket ready · budget alert live.

---

## 10. Reporting (the interview artifact)

`docs/loadtest/REPORT-<date>.md` per campaign:

1. Environment, versions, commit SHA, ceilings, profile parameters.
2. **Predicted vs measured** table (§5 filled in).
3. Throughput-vs-latency curve with the **knee** marked.
4. Failure mode at the knee: graceful degradation or data loss? (Reconciliation result.)
5. **One optimization loop**: change → re-run → new curve → delta.
6. Cost of the run vs estimate.
7. Limits of the result (staging ≠ prod; assumptions; what wasn't tested).

---

## 11. Sequencing

| Step | Where | Output |
|---|---|---|
| L0 | dev | Scripts, sims, ledger, reconciliation; single-pod baseline → revise (†) targets |
| L1 | staging | Smoke + load-lite wired as the pipeline gate |
| L2 | staging | Load T1/T2 with reconciliation |
| L3 | staging | Spike, backlog dump, dependency failures |
| L4 | staging | Stress to the knee; fix bottleneck #1 (or the first real one); re-run |
| L5 | prod | Smoke/canary after promotion |

---

## 12. Open items

- Real `E`, largest tenant size, and monthly distribution from SatMed (aggregate only, no PHI).
- Quota values and increase turnaround for the staging account.
- AWS policy applicability for the intended request rates (this is not a DDoS simulation; confirm).
- Aurora capacity behavior at the chosen min/max ACU (`max_connections`, scale-up latency).
- Whether ALB scaling behavior at spike onset needs pre-warming or just a higher floor.
