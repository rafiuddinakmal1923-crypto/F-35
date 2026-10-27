-- VoltGuard core schema (SDD 4). Applied by `python -m voltguard migrate` as the database owner.
-- Roles: voltguard (owner: migrations and the pipeline), voltguard_app (API: row-level security
-- applies), voltguard_powerbi (read-only, rpt_ views only; see 003_reporting.sql).

CREATE EXTENSION IF NOT EXISTS pgcrypto;

DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM pg_available_extensions WHERE name = 'timescaledb') THEN
    BEGIN
      CREATE EXTENSION IF NOT EXISTS timescaledb;
    EXCEPTION WHEN OTHERS THEN
      RAISE NOTICE 'timescaledb not loadable (%), plain tables used', SQLERRM;
    END;
  END IF;
  IF EXISTS (SELECT 1 FROM pg_available_extensions WHERE name = 'vector') THEN
    CREATE EXTENSION IF NOT EXISTS vector;
  END IF;
END $$;

-- Session context set by the API in every transaction (voltguard.db.app_connection).
CREATE OR REPLACE FUNCTION vg_setting(name text) RETURNS text
LANGUAGE sql STABLE AS $$ SELECT nullif(current_setting('app.' || name, true), '') $$;

CREATE OR REPLACE FUNCTION vg_region_ok(r text) RETURNS boolean
LANGUAGE sql STABLE AS $$ SELECT vg_setting('region') = '*' OR r = vg_setting('region') $$;

-- --------------------------------------------------------------------------- 4.1 network and readings
CREATE TABLE IF NOT EXISTS transformer (
  transformer_id text PRIMARY KEY,
  region text NOT NULL,
  district text NOT NULL,
  capacity_kva double precision,
  has_dtm boolean NOT NULL,
  dtm_accuracy_class double precision,
  loss_params jsonb,
  lat double precision,
  lon double precision
);

CREATE TABLE IF NOT EXISTS premise (
  premise_id text PRIMARY KEY,
  transformer_id text NOT NULL REFERENCES transformer,
  region text NOT NULL,                       -- copied from the transformer for row-level security
  feeder_branch text,
  phase text,
  distance_m double precision,
  street_seq integer NOT NULL,
  lat double precision,                       -- exact location: only through vg_case_contact()
  lon double precision,
  premise_type text NOT NULL,
  tariff text NOT NULL
);
CREATE INDEX IF NOT EXISTS premise_tx ON premise (transformer_id);

CREATE TABLE IF NOT EXISTS meter (
  meter_id text PRIMARY KEY,
  premise_id text NOT NULL REFERENCES premise,
  region text NOT NULL,
  meter_type text NOT NULL CHECK (meter_type IN ('smart', 'conventional')),
  read_frequency text NOT NULL,
  installed_on date
);
CREATE INDEX IF NOT EXISTS meter_premise ON meter (premise_id);

CREATE TABLE IF NOT EXISTS meter_reading (
  meter_id text NOT NULL,
  ts timestamptz NOT NULL,
  kwh double precision NOT NULL,
  voltage_v double precision,
  quality_flag smallint NOT NULL DEFAULT 0,
  PRIMARY KEY (meter_id, ts)
);

CREATE TABLE IF NOT EXISTS meter_monthly_reading (
  meter_id text NOT NULL,
  month date NOT NULL,
  kwh double precision NOT NULL,
  PRIMARY KEY (meter_id, month)
);

CREATE TABLE IF NOT EXISTS transformer_reading (
  transformer_id text NOT NULL,
  ts timestamptz NOT NULL,
  kwh_supplied double precision NOT NULL,
  voltage_v double precision,
  PRIMARY KEY (transformer_id, ts)
);

DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'timescaledb') THEN
    PERFORM create_hypertable('meter_reading', 'ts', chunk_time_interval => interval '1 day', if_not_exists => true, migrate_data => true);
    PERFORM create_hypertable('transformer_reading', 'ts', chunk_time_interval => interval '7 days', if_not_exists => true, migrate_data => true);
  END IF;
END $$;

CREATE TABLE IF NOT EXISTS account_event (
  event_id text PRIMARY KEY,
  premise_id text NOT NULL,
  event_type text NOT NULL,
  event_date date NOT NULL
);
CREATE INDEX IF NOT EXISTS account_event_premise ON account_event (premise_id);

CREATE TABLE IF NOT EXISTS district_weather (
  district text NOT NULL,
  date date NOT NULL,
  temperature_c double precision,
  sunshine_hours double precision,
  PRIMARY KEY (district, date)
);

-- Restricted (SDD 4): only the case service reads it, through the definer functions below.
CREATE TABLE IF NOT EXISTS customer_pii (
  premise_id text PRIMARY KEY,
  holder_name text NOT NULL,
  address text NOT NULL,
  contact text
);

CREATE TABLE IF NOT EXISTS duty_roster (
  team_id text NOT NULL,
  shift_date date NOT NULL,
  region text NOT NULL,
  base_lat double precision NOT NULL,
  base_lon double precision NOT NULL,
  on_duty boolean NOT NULL,
  PRIMARY KEY (team_id, shift_date)
);

-- Historic outcomes loaded from a data source (labels); live outcomes are in inspection_outcome.
CREATE TABLE IF NOT EXISTS historic_outcome (
  case_id text PRIMARY KEY,
  premise_id text NOT NULL,
  outcome text NOT NULL,
  reason_tag text,
  notes_redacted text,
  recorded_at timestamptz NOT NULL,
  origin text
);

-- --------------------------------------------------------------------------- 4.2 detection results
CREATE TABLE IF NOT EXISTS detection_run (
  run_id bigserial PRIMARY KEY,
  run_date date NOT NULL,
  started_at timestamptz NOT NULL DEFAULT now(),
  finished_at timestamptz,
  status text NOT NULL DEFAULT 'running',
  model_version text,
  data_sources jsonb,
  data_snapshot text,
  summary jsonb
);

CREATE TABLE IF NOT EXISTS zone_daily_balance (
  transformer_id text NOT NULL,
  date date NOT NULL,
  region text NOT NULL,
  run_id bigint,
  supplied_kwh double precision,
  metered_kwh double precision,
  estimated_kwh double precision,
  uncertainty_kwh double precision,
  tech_loss_kwh double precision,
  gap_kwh double precision,
  gap_pct double precision,
  over_threshold boolean,
  balance_available boolean NOT NULL,
  flagged boolean NOT NULL DEFAULT false,
  priority text,
  gap_start date,
  PRIMARY KEY (transformer_id, date)
);

-- One row per zone and run: the zone view (gap start, flatness, hourly profile, voltage strip).
CREATE TABLE IF NOT EXISTS zone_run (
  transformer_id text NOT NULL,
  run_date date NOT NULL,
  run_id bigint NOT NULL,
  region text NOT NULL,
  district text NOT NULL,
  balance_available boolean NOT NULL,
  flagged boolean NOT NULL,
  priority text,
  gap_start date,
  gap_since_start boolean,
  gap_kwh_recent double precision,
  gap_pct_recent double precision,
  uncertainty_kwh_recent double precision,
  flatness_cv double precision,
  hourly_gap_kwh jsonb,
  loss_method text,
  voltage jsonb,
  notes jsonb,
  n_premises integer,
  scored boolean NOT NULL,
  PRIMARY KEY (transformer_id, run_date)
);

CREATE TABLE IF NOT EXISTS premise_feature (
  premise_id text NOT NULL,
  run_date date NOT NULL,
  transformer_id text NOT NULL,
  region text NOT NULL,
  features jsonb NOT NULL,
  details jsonb,
  tags text[] NOT NULL DEFAULT '{}',
  PRIMARY KEY (premise_id, run_date)
);

CREATE TABLE IF NOT EXISTS premise_score (
  premise_id text NOT NULL,
  run_date date NOT NULL,
  transformer_id text NOT NULL,
  region text NOT NULL,
  run_id bigint NOT NULL,
  model_version text NOT NULL,
  score integer NOT NULL CHECK (score BETWEEN 0 AND 100),
  rank integer NOT NULL,
  confidence text NOT NULL CHECK (confidence IN ('high', 'low')),
  tags text[] NOT NULL DEFAULT '{}',
  smart boolean NOT NULL DEFAULT true,
  PRIMARY KEY (premise_id, run_date)
);
CREATE INDEX IF NOT EXISTS premise_score_zone ON premise_score (transformer_id, run_date, rank);

CREATE TABLE IF NOT EXISTS score_reason (
  premise_id text NOT NULL,
  run_date date NOT NULL,
  rank smallint NOT NULL,
  region text NOT NULL,
  feature text NOT NULL,
  contribution double precision NOT NULL,
  reason_text text NOT NULL,
  PRIMARY KEY (premise_id, run_date, rank)
);

CREATE TABLE IF NOT EXISTS data_quality_flag (
  meter_id text NOT NULL,
  date date NOT NULL,
  run_date date NOT NULL,
  premise_id text,
  transformer_id text,
  region text NOT NULL,
  completeness double precision NOT NULL,
  PRIMARY KEY (meter_id, date, run_date)
);

-- --------------------------------------------------------------------------- 4.3 cases and learning
CREATE TABLE IF NOT EXISTS inspection_case (
  case_id text PRIMARY KEY,
  premise_id text NOT NULL REFERENCES premise,
  transformer_id text NOT NULL,
  region text NOT NULL,
  origin text NOT NULL CHECK (origin IN ('model', 'random_sample', 'manual')),
  status text NOT NULL CHECK (status IN ('new', 'assigned', 'visited', 'reporting', 'closed')),
  score_at_creation integer,
  assigned_analyst text,
  assigned_team text,
  created_by text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  assigned_at timestamptz,
  reminded_at timestamptz,
  escalated_at timestamptz,
  closed_at timestamptz,
  joint_operation boolean NOT NULL DEFAULT false
);
CREATE UNIQUE INDEX IF NOT EXISTS one_open_case_per_premise ON inspection_case (premise_id) WHERE status <> 'closed';

CREATE TABLE IF NOT EXISTS case_event (
  event_id bigserial PRIMARY KEY,
  case_id text NOT NULL REFERENCES inspection_case,
  region text NOT NULL,
  ts timestamptz NOT NULL DEFAULT now(),
  actor text NOT NULL,
  event_type text NOT NULL,
  detail jsonb
);
CREATE INDEX IF NOT EXISTS case_event_case ON case_event (case_id, ts);

CREATE TABLE IF NOT EXISTS inspection_outcome (
  case_id text NOT NULL REFERENCES inspection_case,
  visit_no integer NOT NULL,
  region text NOT NULL,
  outcome text NOT NULL CHECK (outcome IN ('confirmed_theft', 'false_alarm', 'inconclusive', 'no_access')),
  reason_tag text,
  notes text,                                 -- raw: never read by agents, search or the model
  notes_redacted text,
  photo_keys text[] NOT NULL DEFAULT '{}',
  recorded_by text NOT NULL,
  recorded_at timestamptz NOT NULL DEFAULT now(),
  client_ref text,                            -- offline submission id, makes re-sync idempotent
  PRIMARY KEY (case_id, visit_no)
);
CREATE UNIQUE INDEX IF NOT EXISTS outcome_client_ref ON inspection_outcome (client_ref) WHERE client_ref IS NOT NULL;

CREATE TABLE IF NOT EXISTS dispatch_suggestion (
  case_id text PRIMARY KEY REFERENCES inspection_case,
  region text NOT NULL,
  suggested_team text NOT NULL,
  distance_km double precision,
  joint_operation boolean NOT NULL DEFAULT false,
  rationale text,
  status text NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected')),
  decided_by text,
  decided_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS case_report (
  report_id text PRIMARY KEY,
  case_id text NOT NULL REFERENCES inspection_case,
  region text NOT NULL,
  draft_text text NOT NULL,                   -- placeholders only, never personal details
  sources jsonb,
  mode text,
  status text NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'content_approved', 'export_approved')),
  created_by text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  content_approved_by text,
  content_approved_at timestamptz,
  export_approved_by text,
  export_approved_at timestamptz,
  pdf_key text
);

CREATE TABLE IF NOT EXISTS model_version (
  version_id text PRIMARY KEY,
  trained_at timestamptz NOT NULL DEFAULT now(),
  data_snapshot text,
  metrics jsonb,
  active boolean NOT NULL DEFAULT false,
  notes text
);

-- --------------------------------------------------------------------------- 4.4 knowledge, users, audit
CREATE TABLE IF NOT EXISTS app_user (
  user_id text PRIMARY KEY,
  role text NOT NULL CHECK (role IN ('manager', 'analyst', 'supervisor', 'inspector', 'data_scientist', 'admin', 'auditor', 'pipeline')),
  region text NOT NULL,
  team text,
  display_name text,
  password_hash text NOT NULL,
  token_version integer NOT NULL DEFAULT 0,  -- bumped by remote sign-out (NFR-16)
  active boolean NOT NULL DEFAULT true,
  telegram_chat_id text
);

CREATE TABLE IF NOT EXISTS team (
  team_id text PRIMARY KEY,
  name text NOT NULL,
  region text NOT NULL
);

CREATE TABLE IF NOT EXISTS setting (
  key text PRIMARY KEY,
  value jsonb NOT NULL,
  changed_by text NOT NULL,
  changed_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS job_run (
  job_id bigserial PRIMARY KEY,
  kind text NOT NULL,
  status text NOT NULL DEFAULT 'queued' CHECK (status IN ('queued', 'running', 'done', 'failed')),
  started_by text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  started_at timestamptz,
  finished_at timestamptz,
  progress text,
  result jsonb,
  error text
);

CREATE TABLE IF NOT EXISTS alert (
  alert_id bigserial PRIMARY KEY,
  ts timestamptz NOT NULL DEFAULT now(),
  kind text NOT NULL,
  severity text NOT NULL DEFAULT 'warning',
  region text NOT NULL DEFAULT '*',
  message text NOT NULL,
  detail jsonb,
  acknowledged_by text
);

-- Outbound messages (Telegram or console). The text holds a case ID and link only.
CREATE TABLE IF NOT EXISTS notification (
  notification_id bigserial PRIMARY KEY,
  ts timestamptz NOT NULL DEFAULT now(),
  case_id text,
  region text NOT NULL,
  recipient text NOT NULL,
  kind text NOT NULL,
  channel text NOT NULL,
  text text NOT NULL,
  status text NOT NULL DEFAULT 'sent'
);

CREATE TABLE IF NOT EXISTS audit_log (
  log_id bigserial PRIMARY KEY,
  ts timestamptz NOT NULL DEFAULT clock_timestamp(),
  user_id text NOT NULL,
  action text NOT NULL,
  object_ref text,
  detail jsonb,
  prev_hash text NOT NULL,
  row_hash text NOT NULL
);

-- The canonical text each row hash covers; voltguard.audit.verify recomputes it independently.
CREATE OR REPLACE FUNCTION vg_audit_text(prev text, id bigint, t timestamptz, u text, a text, o text, d jsonb) RETURNS text
LANGUAGE sql IMMUTABLE AS $$
  SELECT concat_ws('|', prev, id::text, to_char(t AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.US"Z"'), u, a, coalesce(o, ''), coalesce(d::text, ''))
$$;

-- Append one hash-chained row (NFR-12). Serialised with an advisory lock so the chain never forks.
CREATE OR REPLACE FUNCTION vg_audit(p_user text, p_action text, p_object text, p_detail jsonb) RETURNS bigint
LANGUAGE plpgsql SECURITY DEFINER SET search_path = public AS $$
DECLARE
  v_prev text;
  v_id bigint;
  v_ts timestamptz := clock_timestamp();
BEGIN
  PERFORM pg_advisory_xact_lock(7340012);
  SELECT row_hash INTO v_prev FROM audit_log ORDER BY log_id DESC LIMIT 1;
  v_prev := coalesce(v_prev, repeat('0', 64));
  v_id := nextval(pg_get_serial_sequence('audit_log', 'log_id'));
  INSERT INTO audit_log (log_id, ts, user_id, action, object_ref, detail, prev_hash, row_hash)
  VALUES (v_id, v_ts, p_user, p_action, p_object, p_detail, v_prev,
          encode(sha256(convert_to(vg_audit_text(v_prev, v_id, v_ts, p_user, p_action, p_object, p_detail), 'UTF8')), 'hex'));
  RETURN v_id;
END $$;

CREATE OR REPLACE FUNCTION vg_case_is_open(s text) RETURNS boolean
LANGUAGE sql IMMUTABLE AS $$ SELECT s IN ('new', 'assigned', 'visited', 'reporting') $$;

-- Personal details and exact location of a case (FR-UI-03, SRS 2.2): only on an open case, for
-- its assigned analyst, a supervisor of its region and the inspectors of its assigned team.
-- Every call is written to the audit log. Returns no row when the caller may not see them.
CREATE OR REPLACE FUNCTION vg_case_contact(p_case text)
RETURNS TABLE (holder_name text, address text, contact text, lat double precision, lon double precision)
LANGUAGE plpgsql SECURITY DEFINER SET search_path = public AS $$
DECLARE
  c inspection_case%ROWTYPE;
  v_role text := vg_setting('role');
  v_user text := vg_setting('user_id');
  v_ok boolean := false;
BEGIN
  SELECT * INTO c FROM inspection_case WHERE case_id = p_case;
  IF NOT FOUND OR NOT vg_case_is_open(c.status) THEN
    RETURN;
  END IF;
  v_ok := (v_role = 'analyst' AND c.assigned_analyst = v_user AND vg_region_ok(c.region))
       OR (v_role = 'supervisor' AND vg_region_ok(c.region))
       OR (v_role = 'inspector' AND c.assigned_team IS NOT NULL AND c.assigned_team = vg_setting('team') AND vg_region_ok(c.region));
  IF NOT v_ok THEN
    RETURN;
  END IF;
  PERFORM vg_audit(v_user, 'pii.view', 'case:' || p_case, jsonb_build_object('role', v_role));
  RETURN QUERY
    SELECT p.holder_name, p.address, p.contact, pr.lat, pr.lon
    FROM customer_pii p JOIN premise pr USING (premise_id)
    WHERE p.premise_id = c.premise_id;
END $$;

-- Personal details for an approved report's PDF (FR-UI-05): only after both approvals, for the
-- case's assigned analyst or a manager of its region.
CREATE OR REPLACE FUNCTION vg_report_contact(p_report text)
RETURNS TABLE (holder_name text, address text, contact text)
LANGUAGE plpgsql SECURITY DEFINER SET search_path = public AS $$
DECLARE
  r case_report%ROWTYPE;
  c inspection_case%ROWTYPE;
  v_role text := vg_setting('role');
  v_user text := vg_setting('user_id');
BEGIN
  SELECT * INTO r FROM case_report WHERE report_id = p_report;
  IF NOT FOUND OR r.status <> 'export_approved' THEN
    RETURN;
  END IF;
  SELECT * INTO c FROM inspection_case WHERE case_id = r.case_id;
  IF NOT ((v_role = 'analyst' AND c.assigned_analyst = v_user) OR v_role = 'manager') OR NOT vg_region_ok(c.region) THEN
    RETURN;
  END IF;
  PERFORM vg_audit(v_user, 'pii.export', 'report:' || p_report, jsonb_build_object('role', v_role));
  RETURN QUERY SELECT p.holder_name, p.address, p.contact FROM customer_pii p WHERE p.premise_id = c.premise_id;
END $$;
