-- always (idempotent: re-applied on every migrate so grant and policy changes reach existing databases)
-- Row-level security by region and least-privilege grants for the API role (FR-AD-01, SDD 9.2).
-- The API connects as voltguard_app and sets app.user_id, app.role, app.region and app.team in
-- every transaction; the database then limits every query to the caller's region, even if an
-- API check were missed. Passwords are set by `python -m voltguard migrate` from .env.

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'voltguard_app') THEN
    CREATE ROLE voltguard_app LOGIN NOSUPERUSER NOBYPASSRLS NOCREATEDB NOCREATEROLE;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'voltguard_powerbi') THEN
    CREATE ROLE voltguard_powerbi LOGIN NOSUPERUSER NOBYPASSRLS NOCREATEDB NOCREATEROLE;
  END IF;
END $$;

REVOKE ALL ON ALL TABLES IN SCHEMA public FROM PUBLIC;
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
GRANT USAGE ON SCHEMA public TO voltguard_app, voltguard_powerbi;

-- Knowledge base for RAG (SDD 8.2): approved documents and closed-case summaries, no personal details.
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'doc_chunk') THEN
    IF EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'vector') THEN
      EXECUTE 'CREATE TABLE doc_chunk (chunk_id text PRIMARY KEY, doc_id text NOT NULL, title text NOT NULL,
               version text, section text, source_ref text, role_scope text[] NOT NULL, region text NOT NULL DEFAULT ''*'',
               kind text NOT NULL DEFAULT ''document'', text text NOT NULL, embedding vector(384), embed_model text)';
    ELSE
      EXECUTE 'CREATE TABLE doc_chunk (chunk_id text PRIMARY KEY, doc_id text NOT NULL, title text NOT NULL,
               version text, section text, source_ref text, role_scope text[] NOT NULL, region text NOT NULL DEFAULT ''*'',
               kind text NOT NULL DEFAULT ''document'', text text NOT NULL, embedding real[], embed_model text)';
    END IF;
  END IF;
END $$;

-- ---------------------------------------------------------------- grants
GRANT SELECT ON transformer, meter, meter_reading, meter_monthly_reading, transformer_reading,
  account_event, district_weather, duty_roster, team, historic_outcome,
  detection_run, zone_daily_balance, zone_run, premise_feature, premise_score, score_reason, data_quality_flag,
  model_version, setting, alert, doc_chunk TO voltguard_app;
-- Premise without lat/lon: exact locations only through vg_case_contact().
GRANT SELECT (premise_id, transformer_id, region, feeder_branch, phase, distance_m, street_seq, premise_type, tariff)
  ON premise TO voltguard_app;
GRANT SELECT (case_id, visit_no, region, outcome, reason_tag, notes_redacted, photo_keys, recorded_by, recorded_at, client_ref)
  ON inspection_outcome TO voltguard_app;          -- raw notes are never read back through the API
GRANT INSERT ON inspection_outcome TO voltguard_app;
GRANT SELECT, INSERT, UPDATE ON inspection_case, case_event, dispatch_suggestion, case_report, job_run, notification TO voltguard_app;
GRANT INSERT, UPDATE ON setting, alert TO voltguard_app;
GRANT SELECT (user_id, role, region, team, display_name, active, telegram_chat_id, token_version) ON app_user TO voltguard_app;
GRANT UPDATE (token_version) ON app_user TO voltguard_app;
GRANT SELECT ON audit_log TO voltguard_app;           -- read for auditors; written only by vg_audit()
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO voltguard_app;
REVOKE ALL ON customer_pii FROM voltguard_app, voltguard_powerbi;
REVOKE ALL ON FUNCTION vg_audit(text, text, text, jsonb) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION vg_audit(text, text, text, jsonb), vg_case_contact(text), vg_report_contact(text) TO voltguard_app;
REVOKE ALL ON FUNCTION vg_case_contact(text), vg_report_contact(text) FROM PUBLIC;

-- Sign-in lookup: the password hash is not readable by the API role, only checkable through this.
CREATE OR REPLACE FUNCTION vg_user_auth(p_user text)
RETURNS TABLE (user_id text, role text, region text, team text, password_hash text, token_version integer, active boolean)
LANGUAGE sql SECURITY DEFINER SET search_path = public AS $$
  SELECT user_id, role, region, team, password_hash, token_version, active FROM app_user WHERE user_id = p_user
$$;
REVOKE ALL ON FUNCTION vg_user_auth(text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION vg_user_auth(text) TO voltguard_app;

-- ---------------------------------------------------------------- row-level security
CREATE OR REPLACE FUNCTION vg_enable_region_rls(t text) RETURNS void LANGUAGE plpgsql AS $$
BEGIN
  EXECUTE format('ALTER TABLE %I ENABLE ROW LEVEL SECURITY', t);
  EXECUTE format('DROP POLICY IF EXISTS region_limit ON %I', t);
  EXECUTE format('CREATE POLICY region_limit ON %I TO voltguard_app USING (vg_region_ok(region)) WITH CHECK (vg_region_ok(region))', t);
END $$;

SELECT vg_enable_region_rls(t) FROM unnest(ARRAY[
  'transformer', 'premise', 'meter', 'duty_roster', 'zone_daily_balance', 'zone_run', 'premise_feature', 'premise_score',
  'score_reason', 'data_quality_flag', 'case_event', 'inspection_outcome', 'dispatch_suggestion', 'case_report',
  'notification', 'team']) AS t;

-- Inspectors see only their team's cases, inside their region.
ALTER TABLE inspection_case ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS region_limit ON inspection_case;
CREATE POLICY region_limit ON inspection_case TO voltguard_app
  USING (vg_region_ok(region) AND (vg_setting('role') <> 'inspector' OR assigned_team = vg_setting('team')))
  WITH CHECK (vg_region_ok(region));

ALTER TABLE meter_reading ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS region_limit ON meter_reading;
CREATE POLICY region_limit ON meter_reading TO voltguard_app
  USING (EXISTS (SELECT 1 FROM meter m WHERE m.meter_id = meter_reading.meter_id AND vg_region_ok(m.region)));

ALTER TABLE meter_monthly_reading ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS region_limit ON meter_monthly_reading;
CREATE POLICY region_limit ON meter_monthly_reading TO voltguard_app
  USING (EXISTS (SELECT 1 FROM meter m WHERE m.meter_id = meter_monthly_reading.meter_id AND vg_region_ok(m.region)));

ALTER TABLE transformer_reading ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS region_limit ON transformer_reading;
CREATE POLICY region_limit ON transformer_reading TO voltguard_app
  USING (EXISTS (SELECT 1 FROM transformer t WHERE t.transformer_id = transformer_reading.transformer_id AND vg_region_ok(t.region)));

ALTER TABLE account_event ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS region_limit ON account_event;
CREATE POLICY region_limit ON account_event TO voltguard_app
  USING (EXISTS (SELECT 1 FROM premise p WHERE p.premise_id = account_event.premise_id AND vg_region_ok(p.region)));

ALTER TABLE historic_outcome ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS region_limit ON historic_outcome;
CREATE POLICY region_limit ON historic_outcome TO voltguard_app
  USING (EXISTS (SELECT 1 FROM premise p WHERE p.premise_id = historic_outcome.premise_id AND vg_region_ok(p.region)));

ALTER TABLE alert ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS region_limit ON alert;
CREATE POLICY region_limit ON alert TO voltguard_app USING (region = '*' OR vg_region_ok(region)) WITH CHECK (true);

ALTER TABLE doc_chunk ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS role_scope ON doc_chunk;
CREATE POLICY role_scope ON doc_chunk TO voltguard_app
  USING (vg_setting('role') = ANY (role_scope) AND (region = '*' OR vg_region_ok(region)));

ALTER TABLE app_user ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS same_region ON app_user;
CREATE POLICY same_region ON app_user TO voltguard_app USING (vg_region_ok(region) OR region = '*' OR user_id = vg_setting('user_id'));
