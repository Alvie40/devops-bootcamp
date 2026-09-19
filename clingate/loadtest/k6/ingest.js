// Open-model load against POST /v1/batches. Arrival rate is fixed, not VU-driven, so a slow
// system cannot slow the generator down and hide its own latency (coordinated omission).
// Env: TARGET, TOKEN (pre-minted; never fetch a token per request), RATE (start rps),
//      STAGES ("60:50,60:100,60:200" = duration_s:target_rps list for a ramp).
import http from 'k6/http';
import { check } from 'k6';

const TARGET = __ENV.TARGET || 'http://localhost:8000';
const TOKEN = __ENV.TOKEN;
const RATE = parseInt(__ENV.RATE || '50');
const stages = (__ENV.STAGES || `60:${RATE}`).split(',').map((s) => {
  const [d, t] = s.split(':');
  return { duration: `${d}s`, target: parseInt(t) };
});

export const options = {
  summaryTrendStats: ['avg', 'med', 'p(90)', 'p(95)', 'p(99)', 'max'],
  scenarios: {
    ingest: {
      executor: 'ramping-arrival-rate',
      startRate: RATE,
      timeUnit: '1s',
      preAllocatedVUs: Math.max(100, RATE), // ~1 s of in-flight requests per rps; avoids VU-init stalls
      maxVUs: 2000,
      stages,
    },
  },
  thresholds: {
    'http_req_duration{expected_response:true}': ['p(99)<300'],
    http_req_failed: ['rate<0.001'],
    dropped_iterations: ['count==0'], // generator could not keep up: the run is INVALID
  },
};

function body(id) {
  const now = new Date().toISOString();
  const obs = [];
  for (let i = 0; i < 30; i++) {
    obs.push({ code: '8867-4', system: 'LOINC', value: 60 + (i % 50), unit: '/min', observed_at: now });
  }
  return JSON.stringify({
    schema_version: '1', batch_id: id, device_id: `dev-${__VU}`, subject_ref: `subj-${__VU}`,
    sequence: __ITER, sent_at: now, observations: obs,
  });
}

export default function () {
  const id = `k6-${__VU}-${__ITER}-${Date.now()}`;
  const res = http.post(`${TARGET}/v1/batches`, body(id), {
    headers: {
      Authorization: `Bearer ${TOKEN}`,
      'Idempotency-Key': id,
      'Content-Type': 'application/json',
    },
  });
  check(res, { 'accepted (202)': (r) => r.status === 202 });
}
