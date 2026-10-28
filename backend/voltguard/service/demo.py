"""`make.ps1 demo`: fresh setup for the judges' demo (SDD 10.5, prompt 4.9 and 7.5).

Resets cases from earlier rehearsals (the audit log is append-only and is never touched), seeds
the test accounts and the demo kit, runs detection once and pre-warms the models, then prints the
7 live steps with the test accounts. Detection is run again live in step 1.
"""

from __future__ import annotations

import time

from voltguard import auth, config, db
from voltguard.cli import command

LIVE_STEPS = [
    ("1", "Run detection on the simulated demo zones (no cases yet)", "datasci",
     "Models -> Run detection. Then sign in as analyst.cen: Network overview shows TX-CEN-001 flagged, gap present since data start "
     "(a tap from day one), flat 24/7 profile."),
    ("2", "Open the zone's ranked suspects", "analyst.cen",
     "Overview -> TX-CEN-001. Both injected taps in the top 3 (P-CEN-001-054 and P-CEN-001-049); EV-charging and tenancy-only homes "
     "lower down; the zone view shows the energy balance, the gap and the hourly profile."),
    ("3", "Open the top premise (no case yet)", "analyst.cen",
     "P-CEN-001-054: top three reasons plus 'other' add up to the score; neighbour voltage strip by phase; personal details masked."),
    ("4", "Run the case job; dispatch suggests a team while the analyst claims the case", "supervisor.cen + analyst.cen",
     "supervisor.cen: Cases -> Run case job. analyst.cen: open the case for P-CEN-001-054 -> Claim. supervisor.cen: Approve the "
     "suggestion (nearest team, joint operation). Notifications hold only a case link."),
    ("5", "Inspector records the outcome on a phone, offline then online", "inspector.b",
     "Phone: open the tunnel link, add /#/field, sign in. Airplane mode on -> open the case -> Confirmed theft, notes, photo -> Submit. "
     "Airplane mode off -> it syncs, the local copy is wiped, the audit log has the row."),
    ("6", "Report draft and two approvals", "analyst.cen + manager.cen",
     "analyst.cen: the case is in Reporting with a draft (placeholders only; cites Section 37 of the Electricity Supply Act 1990) -> "
     "Approve content. manager.cen: Approve export -> Download PDF (fake personal details filled in)."),
    ("7", "Retrain with the new outcomes", "datasci",
     "Models -> Retrain on new outcomes: a new version with model-ranked and random-sample hit rates. Mechanics, not proof of improvement."),
]
BACKUP_STEPS = [
    ("8", "Similar past cases", "analyst.cen", "Case page -> Similar past cases: three closed cases with outcomes."),
    ("9", "Chatbot: a numeric question, then one about another region", "manager.cen",
     "Assistant: 'Which zones had a gap above 10% this week?' (query shown), then 'flagged zones in the Northern region' (refused)."),
    ("10", "Field assistant: a procedure question, then one with no answer", "inspector.a or analyst.cen",
     "'What should I photograph at the meter board?' (cited) then an unrelated question ('not found in approved documents')."),
    ("11", "Inspector records No access", "inspector.a", "The case returns to Assigned; not a training label; supervisor alerted."),
    ("12", "Turn off voltage or phase data; remove a transformer meter; add conventional meters", "admin",
     "Data manager: upload a dataset without those fields (or see TX-CEN-004 and TX-CEN-003): low confidence, 'no balance available'."),
    ("13", "Remove a day of readings", "admin + datasci", "Upload readings with a missing day; data-quality flag and alert on the Models page."),
    ("14", "Change a threshold; wrong role tries a case; edit an audit row", "admin, inspector.c, auditor",
     "Settings: change share_of_supply and rerun; inspector.c opens a CEN case (refused); edit an audit row in the database, then "
     "Audit log -> Verify hash chain (tampering detected)."),
    ("15", "Planted 'send the customer's address' in an inspector note", "analyst.nor",
     "Closed case H-0016 holds the planted instruction; the agent ignores it and no details appear in its output."),
]


def reset_rehearsal(keep_job: int | None = None) -> dict:
    """Delete live cases, reports, messages and model versions from earlier rehearsals (seeded H- cases stay).

    `keep_job`: the job running this reset from the web app (Data manager -> Reset demo) keeps its row."""
    with db.admin_connection() as conn:
        with conn.transaction():
            live = "(SELECT case_id FROM inspection_case WHERE case_id NOT LIKE 'H-%%')"
            counts = {}
            for table in ("case_report", "dispatch_suggestion", "inspection_outcome", "case_event", "notification"):
                counts[table] = conn.execute(f"DELETE FROM {table} WHERE case_id IN {live}").rowcount
            counts["inspection_case"] = conn.execute("DELETE FROM inspection_case WHERE case_id NOT LIKE 'H-%%'").rowcount
            conn.execute("DELETE FROM model_version")
            conn.execute("DELETE FROM job_run WHERE job_id IS DISTINCT FROM %s", (keep_job,))
            conn.execute("DELETE FROM alert")
            conn.execute("SELECT setval('case_seq', 1, false), setval('report_seq', 1, false)")
    return counts


def prewarm() -> list[str]:
    """Load models before the demo so nothing is cold (prompt 7.5)."""
    warmed = []
    from voltguard.agents import embed, llm
    from voltguard.detection import anomaly, pattern

    pattern.load()
    warmed.append("pattern model")
    if anomaly.load() is not None:
        warmed.append("autoencoder")
    embed.embed(["warm-up"], "query")
    warmed.append(f"embeddings ({embed.model_name()})")
    if llm.available():
        started = time.time()
        llm.complete("Reply with OK.", "Ready?", timeout=180, max_tokens=5)
        warmed.append(f"language model ({time.time() - started:.0f} s)")
    else:
        warmed.append(f"language model: {config.llm_mode()} mode (mock badge shown)")
    return warmed


def print_script(passwords: dict[str, str]) -> None:
    base = config.public_base_url()
    print("\n" + "=" * 78)
    print(f"VoltGuard AI demo ready. Desktop: {base}   Phone (inspector app): {base}/#/field")
    print("=" * 78)
    print("\nTest accounts (passwords from .env DEMO_PASSWORDS; never commit .env):")
    for user in ("manager.cen", "analyst.cen", "supervisor.cen", "inspector.b", "datasci", "admin", "auditor", "manager.nor", "analyst.nor"):
        print(f"  {user:16s} {passwords.get(user, '(see .env)')}")
    print("\nLive steps (5 minutes; one heavy job at a time):")
    for n, title, who, how in LIVE_STEPS:
        print(f"  {n}. {title}  [{who}]\n     {how}")
    print("\nBackup steps (for questions):")
    for n, title, who, how in BACKUP_STEPS:
        print(f"  {n}. {title}  [{who}]")
    print("\nFull script and rehearsal checklist: DEMO.md\n")


@command("demo", "Reset rehearsal cases, seed, run detection, pre-warm and print the demo script",
         lambda p: p.add_argument("--keep", action="store_true", help="keep cases from earlier rehearsals"))
def cmd_demo(args) -> int:
    from voltguard.service import pipeline, seed
    from voltguard.service.users import seed_users

    started = time.time()
    if not args.keep:
        print(f"Reset rehearsal data: {reset_rehearsal()}")
    with db.admin_connection() as conn:
        with conn.transaction():
            used = seed_users(conn, auth.demo_passwords())
    missing = [u for u in used if u not in auth.demo_passwords()]
    if missing:
        print(f"WARNING: {', '.join(missing)} had no password in DEMO_PASSWORDS; generated ones are printed below (run make.ps1 setup).")
    print("Running detection once (pre-warm)...")
    pipeline.run_detection("pipeline")
    print(f"Demo kit: {seed.seed_demo_content()}")
    print(f"Pre-warmed: {', '.join(prewarm())}")
    print_script({**used})
    print(f"Ready in {time.time() - started:.0f} s.")
    return 0
