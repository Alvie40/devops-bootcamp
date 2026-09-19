-- ClinGate schema v1. Run as `migrator` (table owner). Runtime role `app_rw` is subject to RLS.
-- Roles migrator / app_rw / auditor_ro are provisioned outside migrations
-- (dev: dev/postgres-init.sql; AWS: Terraform + Secrets Manager).

CREATE TABLE tenants (
  id   uuid PRIMARY KEY,
  name text NOT NULL
);

CREATE TABLE clients (
  client_id text PRIMARY KEY,               -- Cognito app client id OR cert SHA-256 fingerprint
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  kind      text NOT NULL CHECK (kind IN ('http', 'mllp')),
  enabled   boolean NOT NULL DEFAULT true
);

CREATE TABLE subjects (
  id         uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id  uuid NOT NULL REFERENCES tenants(id),
  pseudonym  text NOT NULL,                 -- no direct identifiers, ever
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, pseudonym)
);

CREATE TABLE devices (
  id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id   uuid NOT NULL REFERENCES tenants(id),
  external_id text NOT NULL,
  kind        text,
  UNIQUE (tenant_id, external_id)
);

CREATE TABLE ingest_events (
  id              uuid PRIMARY KEY,
  tenant_id       uuid NOT NULL REFERENCES tenants(id),
  client_id       text NOT NULL,
  source          text NOT NULL CHECK (source IN ('http', 'mllp')),
  idempotency_key text NOT NULL,
  raw_s3_key      text NOT NULL,
  raw_sha256      text NOT NULL,
  received_at     timestamptz NOT NULL,
  status          text NOT NULL CHECK (status IN ('accepted', 'parsed', 'quarantined', 'failed')),
  created_at      timestamptz NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, source, idempotency_key)
);

-- Partitioned by month on observed_at. A UNIQUE constraint on a partitioned table must
-- include the partition key; observed_at is deterministic per (ingest_event, seq), so
-- worker retries still collide and become no-ops.
CREATE TABLE observations (
  id              uuid NOT NULL DEFAULT gen_random_uuid(),
  tenant_id       uuid NOT NULL,
  subject_id      uuid NOT NULL,
  device_id       uuid,
  ingest_event_id uuid NOT NULL,
  seq             int  NOT NULL,
  code_system     text NOT NULL,
  code            text NOT NULL,
  value_num       numeric,
  value_text      text,
  unit            text,
  observed_at     timestamptz NOT NULL,
  received_at     timestamptz NOT NULL,
  PRIMARY KEY (id, observed_at),
  UNIQUE (tenant_id, ingest_event_id, seq, observed_at)
) PARTITION BY RANGE (observed_at);

CREATE TABLE observations_default PARTITION OF observations DEFAULT;

DO $$
DECLARE d date := date '2026-01-01';
BEGIN
  WHILE d < date '2028-01-01' LOOP
    EXECUTE format(
      'CREATE TABLE IF NOT EXISTS %I PARTITION OF observations FOR VALUES FROM (%L) TO (%L)',
      'observations_' || to_char(d, 'YYYY_MM'), d, (d + interval '1 month')::date);
    d := (d + interval '1 month')::date;
  END LOOP;
END $$;

CREATE INDEX observations_subject_time ON observations (tenant_id, subject_id, observed_at);

CREATE TABLE export_destinations (
  id                 uuid PRIMARY KEY,
  tenant_id          uuid NOT NULL REFERENCES tenants(id),
  name               text NOT NULL,
  host               text NOT NULL,
  port               int  NOT NULL,
  max_connections    int  NOT NULL DEFAULT 2,   -- the exporter's concurrency budget
  sending_app        text NOT NULL DEFAULT 'CLINGATE',
  sending_facility   text NOT NULL DEFAULT 'CLINGATE',
  receiving_app      text NOT NULL,
  receiving_facility text NOT NULL,
  tls_ca_ref         text,
  enabled            boolean NOT NULL DEFAULT true
);

CREATE TABLE exports (
  id              uuid PRIMARY KEY,
  tenant_id       uuid NOT NULL REFERENCES tenants(id),
  ingest_event_id uuid NOT NULL REFERENCES ingest_events(id),
  destination_id  uuid NOT NULL REFERENCES export_destinations(id),
  status          text NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'acked', 'failed')),
  attempts        int  NOT NULL DEFAULT 0,
  last_ack_code   text,
  acked_at        timestamptz,
  enqueued_at     timestamptz,
  created_at      timestamptz NOT NULL DEFAULT now(),
  UNIQUE (ingest_event_id, destination_id)
);

CREATE TABLE audit_events (
  id                bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  ts                timestamptz NOT NULL DEFAULT now(),
  tenant_id         uuid,
  actor_type        text NOT NULL,
  actor_id          text NOT NULL,
  action            text NOT NULL,
  resource_type     text,
  resource_id       text,
  subject_pseudonym text,
  purpose           text,
  outcome           text NOT NULL,
  request_id        text,
  source_ip         inet
);

-- Row-level security: FORCE applies it to the table owner as well.
DO $$
DECLARE t text;
BEGIN
  FOREACH t IN ARRAY ARRAY['subjects', 'devices', 'ingest_events', 'observations',
                           'export_destinations', 'exports', 'audit_events']
  LOOP
    EXECUTE format('ALTER TABLE %I ENABLE ROW LEVEL SECURITY', t);
    EXECUTE format('ALTER TABLE %I FORCE ROW LEVEL SECURITY', t);
    EXECUTE format(
      'CREATE POLICY tenant_isolation ON %I
         USING (tenant_id = nullif(current_setting(''app.tenant_id'', true), '''')::uuid)
         WITH CHECK (tenant_id = nullif(current_setting(''app.tenant_id'', true), '''')::uuid)', t);
  END LOOP;
END $$;

GRANT SELECT ON tenants, clients TO app_rw;
GRANT SELECT, INSERT, UPDATE ON subjects, devices, ingest_events, exports TO app_rw;
GRANT SELECT, INSERT ON observations TO app_rw;
GRANT SELECT ON export_destinations TO app_rw;
GRANT INSERT ON audit_events TO app_rw;       -- INSERT-only: no UPDATE/DELETE, ever
GRANT USAGE ON SEQUENCE audit_events_id_seq TO app_rw;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO auditor_ro;
