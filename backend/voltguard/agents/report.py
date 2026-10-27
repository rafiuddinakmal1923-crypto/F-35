"""Case report generator (SDD 8.1, FR-AG-01, FR-UI-05).

Trigger: an outcome of Confirmed theft (case moves to Reporting) or the assigned analyst's request.
Tools: read case, zone balance, voltage and reasons (pseudonymised); redacted notes; document
search; similar cases. The draft holds placeholders ({{HOLDER_NAME}}, {{ADDRESS}}, {{CONTACT}})
and never personal details. The assigned analyst approves the content; a manager, a different
person who neither created nor claimed the case, approves the export; only then does the case
service fill in the details, render the PDF and close the case.

REPORT_MODE: mock (template), predrafted (an assessment drafted by the model during setup,
stored per demo premise), live (the model drafts the assessment now; slow on a laptop CPU).
Only the assessment paragraph is model-written; every fact comes from the database.
"""

from __future__ import annotations

import html
import json
from datetime import datetime

import psycopg
from psycopg.types.json import Jsonb

from voltguard import config, db, storage
from voltguard.agents import guardrails, llm, rag
from voltguard.db import Caller

PLACEHOLDERS = ("{{HOLDER_NAME}}", "{{ADDRESS}}", "{{CONTACT}}")
LEGAL = {"doc_id": "esa_1990", "title": "Electricity Supply Act 1990 (Act 447)", "section": "Section 37"}


class ReportError(Exception):
    def __init__(self, status: int, code: str, message: str):
        super().__init__(message)
        self.status, self.code, self.message = status, code, message


def _facts(conn: psycopg.Connection, case_id: str) -> dict:
    case = conn.execute("SELECT * FROM inspection_case WHERE case_id = %s", (case_id,)).fetchone()
    if not case:
        raise ReportError(404, "not_found", "Case not found in your region")
    zone = conn.execute("SELECT * FROM zone_run WHERE transformer_id = %s ORDER BY run_date DESC LIMIT 1", (case["transformer_id"],)).fetchone()
    score = conn.execute("SELECT score, rank, run_date, tags FROM premise_score WHERE premise_id = %s ORDER BY run_date DESC LIMIT 1",
                         (case["premise_id"],)).fetchone()
    reasons = conn.execute("SELECT feature, contribution, reason_text FROM score_reason WHERE premise_id = %s AND run_date = %s ORDER BY rank",
                           (case["premise_id"], score["run_date"])).fetchall() if score else []
    days = conn.execute("SELECT date, gap_kwh, uncertainty_kwh, supplied_kwh FROM zone_daily_balance WHERE transformer_id = %s ORDER BY date",
                        (case["transformer_id"],)).fetchall()
    outcomes = conn.execute("SELECT visit_no, outcome, reason_tag, notes_redacted, cardinality(photo_keys) AS photos, recorded_at "
                            "FROM inspection_outcome WHERE case_id = %s ORDER BY visit_no", (case_id,)).fetchall()
    voltage = (zone["voltage"] or {}).get("premises", {}).get(case["premise_id"]) if zone and zone["voltage"] else None
    return {"case": case, "zone": zone, "score": score, "reasons": reasons, "days": days, "outcomes": outcomes, "voltage": voltage}


def _legal_sources(conn: psycopg.Connection) -> list[dict]:
    """Cite the provision from the loaded public text; by name only when the text is not loaded yet."""
    hits = [p for p in rag.search(conn, "Electricity Supply Act Section 37 offence tampering meter theft of electricity", k=8)
            if p.doc_id == LEGAL["doc_id"]]
    section = next((p for p in hits if (p.section or "") == LEGAL["section"]), None)
    if section:
        return [{**section.citation(), "excerpt": section.text[:600], "loaded": True}]
    return [{**LEGAL, "kind": "legal", "source_ref": "public text not loaded: run scripts/fetch_docs.py", "loaded": False}]


def _pct(v) -> str:
    return "n/a" if v is None else f"{v * 100:.1f}%"


def _assessment_mock(f: dict) -> str:
    z, s = f["zone"], f["score"]
    parts = [f"The transformer zone {f['case']['transformer_id']} shows an unexplained energy gap of about "
             f"{(z['gap_kwh_recent'] or 0):.0f} kWh per day ({_pct(z['gap_pct_recent'])} of supply) after technical losses and "
             f"the uncertainty margin."]
    if z["flatness_cv"] is not None and z["flatness_cv"] < 0.2:
        parts.append("The gap is nearly constant across the day, consistent with a continuous hidden load such as mining equipment.")
    if s:
        parts.append(f"Premise {f['case']['premise_id']} ranked {s['rank']} in the zone with a risk score of {s['score']}.")
    confirmed = [o for o in f["outcomes"] if o["outcome"] == "confirmed_theft"]
    if confirmed:
        parts.append("The field inspection recorded the outcome Confirmed theft; the inspection findings below describe what was found.")
    parts.append("The score ranks risk; this report presents evidence for the investigating authority and does not itself "
                 "determine whether any person committed an offence.")
    return " ".join(parts)


def _assessment(f: dict, mode: str) -> tuple[str, str]:
    """(text, mode actually used). The model sees pseudonymised facts only, never notes with details."""
    if mode == "predrafted":
        path = config.data_root() / "predrafted" / f"{f['case']['premise_id']}.json"
        if path.exists():
            stored = json.loads(path.read_text(encoding="utf-8"))
            return guardrails.check_output(stored["assessment"]), f"predrafted ({stored.get('model', 'model')})"
        return _assessment_mock(f), "mock (no pre-drafted report for this premise)"
    if mode == "live":
        facts = {"zone": f["case"]["transformer_id"], "gap_kwh_per_day": f["zone"]["gap_kwh_recent"], "gap_share": f["zone"]["gap_pct_recent"],
                 "flatness_cv": f["zone"]["flatness_cv"], "risk_score": f["score"]["score"] if f["score"] else None,
                 "rank": f["score"]["rank"] if f["score"] else None, "reasons": [r["reason_text"] for r in f["reasons"][:3]],
                 "outcome": [o["outcome"] for o in f["outcomes"]]}
        try:
            completion = _live_assessment(facts)
        except llm.PromptBlocked:
            completion = None
        if completion:
            try:
                return guardrails.check_output(completion.text), f"live ({completion.model})"
            except guardrails.OutputBlocked:
                pass
        return _assessment_mock(f), "mock (model unavailable)"
    return _assessment_mock(f), "mock"


def _live_assessment(facts: dict):
    return llm.complete(
            "You write the assessment paragraph of an electricity revenue-protection case report. Use only the JSON facts. "
            "Describe risk and evidence; never call anyone a thief or state guilt. 120 words at most. No names or addresses.",
            json.dumps(facts, default=str), timeout=600)


def build_draft(conn: psycopg.Connection, case_id: str, mode: str | None = None) -> tuple[str, list[dict], str]:
    f = _facts(conn, case_id)
    if f["zone"] is None:
        raise ReportError(409, "no_detection", "No detection result for this case's zone")
    mode = mode or config.report_mode()
    assessment, used_mode = _assessment(f, mode)
    legal = _legal_sources(conn)
    similar = rag.similar_cases(conn, Caller("agent:report", "analyst", f["case"]["region"]), case_id)
    c, z = f["case"], f["zone"]
    start = z["gap_start"].isoformat() if z["gap_start"] else ("present since the start of the data" if z["gap_since_start"] else "not determined")
    lines = [
        f"CASE REPORT {c['case_id']} (DRAFT)",
        "",
        "1. Case summary",
        f"Case {c['case_id']}, premise {c['premise_id']}, transformer zone {c['transformer_id']} (region {c['region']}). "
        f"Case opened {c['created_at']:%Y-%m-%d} ({c['origin'].replace('_', ' ')}).",
        "",
        "2. Account holder and premise",
        f"Account holder: {PLACEHOLDERS[0]}. Address: {PLACEHOLDERS[1]}. Contact: {PLACEHOLDERS[2]}.",
        "(Filled in by the case service only when the approved report is exported.)",
        "",
        "3. Zone evidence",
        f"Unexplained energy: about {(z['gap_kwh_recent'] or 0):.0f} kWh/day ({_pct(z['gap_pct_recent'])} of supply), "
        f"uncertainty margin about {(z['uncertainty_kwh_recent'] or 0):.0f} kWh/day. Gap start: {start}. "
        f"Flatness of the hourly gap (coefficient of variation): {z['flatness_cv'] if z['flatness_cv'] is not None else 'n/a'}"
        f"{' (constant 24/7 load)' if z['flatness_cv'] is not None and z['flatness_cv'] < 0.2 else ''}.",
        "",
        "4. Premise evidence",
    ]
    if f["score"]:
        lines.append(f"Risk score {f['score']['score']} (rank {f['score']['rank']} in the zone). Main reasons:")
        lines += [f"- {r['reason_text']} ({r['contribution']:+.1f})" for r in f["reasons"] if r["feature"] not in ("other", "capped")][:3]
    if f["voltage"] and f["voltage"].get("signal_v") is not None:
        lines.append(f"Unexplained voltage at this meter: {f['voltage']['signal_v']:.2f} V; estimated hidden-load position "
                     f"{f['voltage']['tap_distance_m'] or 0:.0f} m away on the same phase and branch.")
    lines += ["", "5. Inspection findings"]
    for o in f["outcomes"]:
        note = guardrails.quote_retrieved(o["notes_redacted"]) if o["notes_redacted"] else "no notes"
        lines.append(f"Visit {o['visit_no']} ({o['recorded_at']:%Y-%m-%d}): {o['outcome'].replace('_', ' ')}"
                     f"{' / ' + o['reason_tag'] if o['reason_tag'] else ''}; {o['photos']} photo(s). Notes (redacted): {note}")
    lines += ["", "6. Assessment", assessment, "", "7. Relevant legal provisions"]
    for src in legal:
        lines.append(f"- {src['title']}, {src['section']}" + (f": \"{src['excerpt'][:400]}...\"" if src.get("loaded") else
                                                               " (cited by provision; the public text is not loaded on this system)"))
    if similar:
        lines += ["", "8. Similar past cases (redacted summaries)"]
        lines += [f"- {s['case_id']}: outcome {s['outcome'].replace('_', ' ')}" for s in similar]
    lines += ["", "Approvals: content by the assigned analyst; export by a manager (a different person)."]
    text = guardrails.check_output("\n".join(lines), presidio=False)   # free parts (assessment, notes) were checked in full
    sources = legal + [{"kind": "case_summary", "doc_id": s["case_id"], "title": f"Closed case {s['case_id']}", "section": None,
                        "source_ref": f"case:{s['case_id']}"} for s in similar] + [
        {"kind": "data", "doc_id": "zone_daily_balance", "title": f"Zone balance {c['transformer_id']}", "section": None, "source_ref": "database"},
        {"kind": "data", "doc_id": "score_reason", "title": f"Score reasons {c['premise_id']}", "section": None, "source_ref": "database"}]
    return text, sources, used_mode


def draft_for_case(conn: psycopg.Connection, caller: Caller, case_id: str, trigger: str = "request") -> dict:
    case = conn.execute("SELECT * FROM inspection_case WHERE case_id = %s", (case_id,)).fetchone()
    if not case:
        raise ReportError(404, "not_found", "Case not found in your region")
    if trigger == "request" and (caller.role != "analyst" or case["assigned_analyst"] != caller.user_id):
        raise ReportError(403, "forbidden", "Only the case's assigned analyst asks for a report draft")
    if case["status"] != "reporting":
        raise ReportError(409, "conflict", "Reports are drafted for cases in Reporting (after Confirmed theft)")
    existing = conn.execute("SELECT * FROM case_report WHERE case_id = %s AND status <> 'export_approved' ORDER BY created_at DESC LIMIT 1",
                            (case_id,)).fetchone()
    if existing:
        return existing
    text, sources, mode = build_draft(conn, case_id)
    n = conn.execute("SELECT nextval('report_seq') AS n").fetchone()["n"]
    report_id = f"R-{datetime.now().year}-{n:04d}"
    row = conn.execute("""INSERT INTO case_report (report_id, case_id, region, draft_text, sources, mode, created_by)
                          VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING *""",
                       (report_id, case_id, case["region"], text, Jsonb(sources), mode, "agent:report")).fetchone()
    conn.execute("INSERT INTO case_event (case_id, region, actor, event_type, detail) VALUES (%s, %s, 'agent:report', 'report_drafted', %s)",
                 (case_id, case["region"], Jsonb({"report_id": report_id, "mode": mode, "trigger": trigger})))
    db.audit(conn, "agent:report", "agent.report.draft", f"report:{report_id}", {"case_id": case_id, "mode": mode, "requested_by": caller.user_id})
    return row


def _report(conn, report_id: str) -> tuple[dict, dict]:
    report = conn.execute("SELECT * FROM case_report WHERE report_id = %s", (report_id,)).fetchone()
    if not report:
        raise ReportError(404, "not_found", "Report not found in your region")
    case = conn.execute("SELECT * FROM inspection_case WHERE case_id = %s", (report["case_id"],)).fetchone()
    return report, case


def get_report(conn, caller: Caller, report_id: str) -> dict:
    report, case = _report(conn, report_id)
    if not ((caller.role == "analyst" and case["assigned_analyst"] == caller.user_id) or caller.role in ("manager", "supervisor")):
        raise ReportError(403, "forbidden", "Only the case's analyst, a supervisor or a manager reads the report")
    db.audit(conn, caller.user_id, "report.view", f"report:{report_id}", None)
    return report


def approve_content(conn, caller: Caller, report_id: str) -> dict:
    report, case = _report(conn, report_id)
    if caller.role != "analyst" or case["assigned_analyst"] != caller.user_id:
        raise ReportError(403, "forbidden", "Only the case's assigned analyst approves the content")
    if report["status"] != "draft":
        raise ReportError(409, "conflict", f"Report is already {report['status'].replace('_', ' ')}")
    row = conn.execute("UPDATE case_report SET status = 'content_approved', content_approved_by = %s, content_approved_at = now() "
                       "WHERE report_id = %s RETURNING *", (caller.user_id, report_id)).fetchone()
    db.audit(conn, caller.user_id, "report.approve_content", f"report:{report_id}", None)
    return row


def render_html(report: dict, contact: dict | None) -> str:
    text = report["draft_text"].replace(" (DRAFT)", "")
    for placeholder, key in zip(PLACEHOLDERS, ("holder_name", "address", "contact")):
        text = text.replace(placeholder, (contact or {}).get(key) or "[not on record]")
    body = "".join(f"<h2>{html.escape(line)}</h2>" if line[:2].rstrip(".").isdigit() and line[1:3] == ". " else
                   f"<p>{html.escape(line)}</p>" if line else "" for line in text.splitlines()[1:])
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
body{{font-family:Helvetica,Arial,sans-serif;font-size:11pt;color:#111;line-height:1.4}} h1{{font-size:16pt;margin:0 0 4px}}
h2{{font-size:12pt;margin:16px 0 4px;border-bottom:1px solid #999}} p{{margin:3px 0}} .meta{{color:#555;font-size:9pt}}
</style></head><body><h1>{html.escape(text.splitlines()[0])}</h1>
<p class="meta">Exported {datetime.now():%Y-%m-%d %H:%M}. Content approved by {html.escape(report['content_approved_by'] or '')};
export approved by {html.escape(report['export_approved_by'] or '')}. R0 prototype: simulated data and fake personal details.</p>
{body}</body></html>"""


def approve_export(conn, caller: Caller, report_id: str) -> dict:
    """Second approval (manager, a different person); fills in the details, renders the PDF, closes the case."""
    report, case = _report(conn, report_id)
    if caller.role != "manager":
        raise ReportError(403, "forbidden", "Only a manager gives the export approval")
    if report["status"] != "content_approved":
        raise ReportError(409, "conflict", "Export needs the content approval first")
    if caller.user_id in (report["content_approved_by"], case["created_by"], case["assigned_analyst"]):
        raise ReportError(403, "forbidden", "The export approver must differ from the content approver and from whoever created or claimed the case")
    report = conn.execute("UPDATE case_report SET status = 'export_approved', export_approved_by = %s, export_approved_at = now() "
                          "WHERE report_id = %s RETURNING *", (caller.user_id, report_id)).fetchone()
    contact = conn.execute("SELECT * FROM vg_report_contact(%s)", (report_id,)).fetchone()
    from voltguard import pdf

    data, engine = pdf.html_to_pdf(render_html(report, dict(contact) if contact else None))
    key = storage.put("pdfs", data, ".pdf")
    report = conn.execute("UPDATE case_report SET pdf_key = %s WHERE report_id = %s RETURNING *", (key, report_id)).fetchone()
    conn.execute("UPDATE inspection_case SET status = 'closed', closed_at = now() WHERE case_id = %s", (case["case_id"],))
    conn.execute("INSERT INTO case_event (case_id, region, actor, event_type, detail) VALUES (%s, %s, %s, 'report_exported', %s)",
                 (case["case_id"], case["region"], caller.user_id, Jsonb({"report_id": report_id, "engine": engine})))
    conn.execute("INSERT INTO case_event (case_id, region, actor, event_type, detail) VALUES (%s, %s, %s, 'closed', NULL)",
                 (case["case_id"], case["region"], caller.user_id))
    db.audit(conn, caller.user_id, "report.approve_export", f"report:{report_id}", {"pdf_engine": engine})
    return report


def get_pdf(conn, caller: Caller, report_id: str) -> bytes:
    report, case = _report(conn, report_id)
    if not ((caller.role == "analyst" and case["assigned_analyst"] == caller.user_id) or caller.role == "manager"):
        raise ReportError(403, "forbidden", "Only the case's analyst or a manager downloads the PDF")
    if report["status"] != "export_approved" or not report["pdf_key"]:
        raise ReportError(409, "conflict", "Export is blocked until both approvals are given")
    db.audit(conn, caller.user_id, "report.download", f"report:{report_id}", None)
    return storage.get("pdfs", report["pdf_key"])
