-- always (idempotent)
-- Case and report numbering, and the training labels view (FR-IW-04).

CREATE SEQUENCE IF NOT EXISTS case_seq;
CREATE SEQUENCE IF NOT EXISTS report_seq;
GRANT USAGE, SELECT ON SEQUENCE case_seq, report_seq TO voltguard_app;

-- Every outcome except No access is a training label; `origin` lets training weights correct for
-- how each case was chosen (SDD 5.4) and keeps random-sample hit rates separate (FR-ML-02).
-- security_invoker: the view runs with the caller's rights, so row-level security limits it to the
-- caller's region (FR-AD-01); without it a view runs as its owner and showed every region's labels.
CREATE OR REPLACE VIEW training_label WITH (security_invoker = true) AS
SELECT o.case_id, o.visit_no, c.premise_id, c.transformer_id, c.region, c.origin, o.outcome, o.reason_tag,
       (o.outcome = 'confirmed_theft') AS is_theft, o.recorded_at, 'live'::text AS source
FROM inspection_outcome o JOIN inspection_case c USING (case_id)
WHERE o.outcome <> 'no_access'
UNION ALL
SELECT h.case_id, 1, h.premise_id, p.transformer_id, p.region, coalesce(h.origin, 'model'), h.outcome, h.reason_tag,
       (h.outcome = 'confirmed_theft'), h.recorded_at, 'historic'::text
FROM historic_outcome h JOIN premise p USING (premise_id)
WHERE h.outcome <> 'no_access';

GRANT SELECT ON training_label TO voltguard_app;
