"""CLI commands that need the database (registered on `python -m voltguard`)."""

from __future__ import annotations

import json

from voltguard import audit, db
from voltguard.cli import command


@command("migrate", "Create or update the database schema, roles and row-level security")
def cmd_migrate(args) -> int:
    applied = db.migrate()
    print("Applied: " + (", ".join(applied) if applied else "nothing new"))
    return 0


@command("pipeline", "Load the active sources into the database and run detection (no cases)")
def cmd_pipeline(args) -> int:
    from voltguard.service import pipeline

    summary = pipeline.run_detection("pipeline")
    print(json.dumps(summary, indent=2, default=str))
    return 0


@command("seed-users", "Create the test accounts from config/demo.yaml (passwords from DEMO_PASSWORDS)")
def cmd_seed_users(args) -> int:
    from voltguard import auth
    from voltguard.service.users import seed_users

    given = auth.demo_passwords()
    with db.admin_connection() as conn:
        with conn.transaction():
            used = seed_users(conn, given)
    for user, password in used.items():
        note = "" if user in given else "   (generated now: not in .env; add it to DEMO_PASSWORDS to keep it)"
        print(f"  {user:16s} {password}{note}")
    return 0


@command("anchor", "Copy the latest audit hash outside the database (normally daily)")
def cmd_anchor(args) -> int:
    print(audit.write_anchor() or "Audit log is empty")
    return 0


@command("verify-audit", "Recompute the audit hash chain and compare it with the anchors")
def cmd_verify_audit(args) -> int:
    result = audit.verify()
    print(json.dumps(result.as_dict(), indent=2))
    return 0 if result.ok else 3


@command("seed", "Test accounts, demo data and detection, closed cases, RAG index and the pre-drafted report")
def cmd_seed(args) -> int:
    from voltguard.service import pipeline, seed

    cmd_seed_users(args)
    pipeline.run_detection("pipeline")
    print(json.dumps(seed.seed_demo_content(), indent=2, default=str))
    return 0


@command("index-docs", "Re-index the approved documents and closed-case summaries for RAG")
def cmd_index_docs(args) -> int:
    from voltguard.agents import rag

    print(f"Indexed {rag.index_documents()} document passages and {rag.index_case_summaries()} case summaries")
    return 0


@command("fetch-models", "Download the embedding model (multilingual-e5-small, ONNX) into HF_HOME")
def cmd_fetch_models(args) -> int:
    from voltguard.agents import embed

    try:
        print(f"Embedding model in {embed.download()}")
    except Exception as exc:  # offline: the hashing fallback keeps RAG working
        print(f"Could not download the embedding model ({exc.__class__.__name__}); the hashing fallback stays in use.")
    return 0


@command("retrain", "Retrain the label model on inspection outcomes and record a new version")
def cmd_retrain(args) -> int:
    from voltguard.service import learning

    print(json.dumps(learning.retrain("data_scientist"), indent=2, default=str))
    return 0


REPORT_VIEWS = ("rpt_network_kpis", "rpt_zone_latest", "rpt_zone_daily", "rpt_case_counts", "rpt_outcomes", "rpt_flag_rates")


@command("snapshot", "Export the zone-level rpt_ views to CSV for Power BI (default powerbi/snapshot/)",
         lambda p: p.add_argument("--out", default=None))
def cmd_snapshot(args) -> int:
    from pathlib import Path

    from voltguard import config

    out = Path(args.out) if args.out else config.REPO_ROOT / "powerbi" / "snapshot"
    out.mkdir(parents=True, exist_ok=True)
    with db.admin_connection() as conn:
        for view in REPORT_VIEWS:
            # Booleans as true/false (COPY writes t/f), which Power BI reads as logical values.
            cols = conn.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = %s ORDER BY ordinal_position",
                                (view,)).fetchall()
            select = ", ".join(f"{c['column_name']}::text AS {c['column_name']}" if c["data_type"] == "boolean" else c["column_name"] for c in cols)
            with (out / f"{view}.csv").open("wb") as fh, conn.cursor().copy(f"COPY (SELECT {select} FROM {view}) TO STDOUT WITH (FORMAT csv, HEADER true)") as cp:
                for block in cp:
                    fh.write(block)
            print(f"  {view:20s} -> {out / (view + '.csv')}")
    return 0
