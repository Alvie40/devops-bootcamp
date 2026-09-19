-- Dev only. Runs once on first container start.
CREATE ROLE migrator LOGIN PASSWORD 'dev-migrator';
CREATE ROLE app_rw LOGIN PASSWORD 'dev-app';
CREATE ROLE auditor_ro LOGIN PASSWORD 'dev-auditor';
CREATE DATABASE clingate OWNER migrator;
CREATE DATABASE clingate_test OWNER migrator;
