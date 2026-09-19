#!/usr/bin/env bash
# Single-pod capacity sweep: constant arrival rate per step against one 0.5 vCPU / 1 GiB container.
# A step is only VALID if dropped_iterations == 0 (the generator kept up). Knee = first rate where
# p99 leaves the SLO or errors appear. Result feeds the per-pod sizing in docs/LOADTEST.md section 3.3.
set -uo pipefail
cd "$(dirname "$0")/.."
RATES=${RATES:-"50 100 200 400 600 800"}
DUR=${DUR:-20}
mkdir -p loadtest/out
uv run python -m clingate_sim.devauth dev-device-client 86400 >/dev/null
export TOKEN
TOKEN=$(uv run python -m clingate_sim.devauth dev-device-client 86400)
docker compose --profile baseline up -d --build --wait ingest-api >/dev/null
printf "%-8s %-10s %-9s %-9s %-9s %-8s %s\n" rate achieved p50_ms p99_ms failed dropped verdict
for r in $RATES; do
  RATE=$r STAGES="$DUR:$r" docker compose --profile baseline run --rm k6 >/dev/null 2>&1
  python3 - "$r" <<'PY'
import json, sys
rate = int(sys.argv[1])
m = json.load(open("loadtest/out/summary.json"))["metrics"]
achieved = m["http_reqs"]["rate"]
p50, p99 = m["http_req_duration"]["med"], m["http_req_duration"]["p(99)"]
failed = m["http_req_failed"].get("value", m["http_req_failed"].get("rate", 0))
dropped = m.get("dropped_iterations", {}).get("count", 0)
valid = dropped == 0
ok = valid and p99 < 300 and failed < 0.001
if ok:
    verdict = "ok"
elif not valid:
    verdict = "SATURATED (p50 rising)" if p50 > 20 else "INVALID (generator behind, inconclusive)"
else:
    verdict = "SLO BREACH"
print(f"{rate:<8} {achieved:<10.1f} {p50:<9.1f} {p99:<9.1f} {failed*100:<8.2f}% {dropped:<8} {verdict}")
PY
done
docker compose --profile baseline down >/dev/null 2>&1
