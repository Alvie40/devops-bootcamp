-- Dev seed. Runs as `migrator`; FORCE RLS applies to the owner, so tenant context is set explicitly.
INSERT INTO tenants (id, name) VALUES ('11111111-1111-1111-1111-111111111111', 'dev-tenant')
  ON CONFLICT DO NOTHING;
INSERT INTO clients (client_id, tenant_id, kind) VALUES
  ('dev-device-client', '11111111-1111-1111-1111-111111111111', 'http'),
  ('dev-lab-client',    '11111111-1111-1111-1111-111111111111', 'mllp')
  ON CONFLICT DO NOTHING;
SELECT set_config('app.tenant_id', '11111111-1111-1111-1111-111111111111', false);
INSERT INTO export_destinations
  (id, tenant_id, name, host, port, max_connections, receiving_app, receiving_facility)
VALUES ('33333333-3333-3333-3333-333333333333', '11111111-1111-1111-1111-111111111111',
        'sink-sim', '127.0.0.1', 2576, 2, 'SPONSOR', 'SPONSORHQ')
ON CONFLICT DO NOTHING;
