-- always (idempotent)
-- Pseudonymised, zone-level reporting views for the manager dashboard (SDD 4.2, FR-UI-01, NFR-07, NFR-11).
-- No premise IDs, premise locations or personal details. Power BI connects as voltguard_powerbi,
-- which can read these views and nothing else; in R0 every manager sees all regions at zone level.

CREATE OR REPLACE VIEW rpt_zone_latest AS
SELECT z.transformer_id AS zone, z.region, z.district, z.run_date, z.flagged, z.priority, z.balance_available,
       round((z.gap_pct_recent * 100)::numeric, 2) AS gap_pct, round(z.gap_kwh_recent::numeric, 1) AS gap_kwh_per_day,
       round(z.uncertainty_kwh_recent::numeric, 1) AS uncertainty_kwh_per_day, round(z.flatness_cv::numeric, 3) AS flatness_cv,
       (z.flatness_cv < 0.2) AS flat_24_7, z.gap_start, z.gap_since_start, z.n_premises,
       round(t.lat::numeric, 3) AS zone_lat, round(t.lon::numeric, 3) AS zone_lon,     -- transformer position, ~100 m precision
       (SELECT count(*) FROM inspection_case c WHERE c.transformer_id = z.transformer_id AND c.status <> 'closed') AS open_cases,
       -- Value at risk (UI brief 3.1), flagged zones only, always an estimate: the gap above the uncertainty
       -- margin x 30 days, in RM when an admin has set the tariff (config/tariffs.yaml, copied into `setting`).
       v.excess_kwh_per_day, round(v.excess_kwh_per_day * 30, 0) AS excess_kwh_per_month_estimate,
       round(v.excess_kwh_per_day * 30 * (SELECT (s.value->>'rm_per_kwh')::numeric FROM setting s WHERE s.key = 'tariff'), 0)
         AS rm_at_risk_per_month_estimate
FROM zone_run z JOIN transformer t USING (transformer_id)
CROSS JOIN LATERAL (SELECT CASE WHEN z.flagged AND z.balance_available
                                THEN round(greatest(coalesce(z.gap_kwh_recent, 0) - coalesce(z.uncertainty_kwh_recent, 0), 0)::numeric, 1)
                           END AS excess_kwh_per_day) v
WHERE z.run_date = (SELECT max(run_date) FROM zone_run);

CREATE OR REPLACE VIEW rpt_zone_daily AS
SELECT b.transformer_id AS zone, b.region, t.district, b.date, round(b.supplied_kwh::numeric, 1) AS supplied_kwh,
       round((b.metered_kwh + coalesce(b.estimated_kwh, 0))::numeric, 1) AS metered_and_estimated_kwh,
       round(b.tech_loss_kwh::numeric, 1) AS technical_loss_kwh, round(b.gap_kwh::numeric, 1) AS gap_kwh,
       round(b.uncertainty_kwh::numeric, 1) AS uncertainty_kwh, round((b.gap_pct * 100)::numeric, 2) AS gap_pct,
       b.over_threshold, b.balance_available
FROM zone_daily_balance b JOIN transformer t USING (transformer_id);

CREATE OR REPLACE VIEW rpt_case_counts AS
SELECT c.region, t.district, c.transformer_id AS zone, c.status, c.origin, date_trunc('week', c.created_at)::date AS week, count(*) AS cases
FROM inspection_case c JOIN transformer t USING (transformer_id)
GROUP BY 1, 2, 3, 4, 5, 6;

-- Built on the base tables, not on training_label: that view runs with the caller's rights (region
-- limits for app users), which the Power BI role does not have on the tables below it.
CREATE OR REPLACE VIEW rpt_outcomes AS
WITH labels AS (
  SELECT c.region, c.transformer_id, c.origin, o.outcome, o.recorded_at
  FROM inspection_outcome o JOIN inspection_case c USING (case_id) WHERE o.outcome <> 'no_access'
  UNION ALL
  SELECT p.region, p.transformer_id, coalesce(h.origin, 'model'), h.outcome, h.recorded_at
  FROM historic_outcome h JOIN premise p USING (premise_id) WHERE h.outcome <> 'no_access')
SELECT l.region, t.district, CASE WHEN l.origin = 'random_sample' THEN 'random sample' ELSE 'model-ranked' END AS inspections,
       l.outcome, date_trunc('month', l.recorded_at)::date AS month, count(*) AS outcomes
FROM labels l JOIN transformer t USING (transformer_id)
GROUP BY 1, 2, 3, 4, 5;

-- Fairness monitoring (NFR-11): flag rate by area. Housing tenure (owner or renter) is not in the
-- R0 data; the view gains a tenure column when the billing source provides it.
CREATE OR REPLACE VIEW rpt_flag_rates AS
SELECT z.region, z.district, count(*) AS zones, sum(z.flagged::int) AS flagged_zones,
       round(avg(z.flagged::int)::numeric * 100, 1) AS zone_flag_rate_pct,
       (SELECT count(*) FROM inspection_case c JOIN transformer t USING (transformer_id)
          WHERE t.region = z.region AND t.district = z.district AND c.origin = 'model') AS model_cases_opened,
       (SELECT count(*) FROM inspection_case c JOIN transformer t USING (transformer_id)
          WHERE t.region = z.region AND t.district = z.district AND c.origin = 'random_sample') AS random_sample_cases
FROM zone_run z WHERE z.run_date = (SELECT max(run_date) FROM zone_run)
GROUP BY z.region, z.district, z.run_date;

CREATE OR REPLACE VIEW rpt_network_kpis AS
SELECT run_date, count(*) AS zones, sum(flagged::int) AS flagged_zones, sum((NOT balance_available)::int) AS zones_without_balance,
       round(sum(CASE WHEN flagged THEN gap_kwh_recent ELSE 0 END)::numeric, 0) AS flagged_gap_kwh_per_day,
       (SELECT count(*) FROM inspection_case WHERE status <> 'closed') AS open_cases
FROM zone_run WHERE run_date = (SELECT max(run_date) FROM zone_run) GROUP BY run_date;

REVOKE ALL ON ALL TABLES IN SCHEMA public FROM voltguard_powerbi;
GRANT SELECT ON rpt_zone_latest, rpt_zone_daily, rpt_case_counts, rpt_outcomes, rpt_flag_rates, rpt_network_kpis TO voltguard_powerbi;
-- Not granted to voltguard_app: views run with their owner's rights and so bypass row-level security.
REVOKE ALL ON rpt_zone_latest, rpt_zone_daily, rpt_case_counts, rpt_outcomes, rpt_flag_rates, rpt_network_kpis FROM voltguard_app;
