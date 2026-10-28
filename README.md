# VoltGuard AI (R0 prototype)

VoltGuard turns a transformer energy-gap alert into a ranked, explained list of the premises
most likely responsible, then supports inspection, reporting and model learning. Team F-35,
Hackspire Lumina, Domain 1. Requirements: `VoltGuard_SRS.md`; design: `VoltGuard_SDD.md`;
build brief: `VoltGuard_ClaudeCode_Prompt.md`.

**New here? Start with [`HOW_TO_RUN.md`](HOW_TO_RUN.md)**: set-up, accounts, everyday commands,
troubleshooting, and how to share the app with a public `https://` link instead of `localhost`.

**R0 runs on simulated data and fake personal details only.** Scores rank risk; they never say
that anyone stole electricity, and people decide after inspection.

## Quick start (Windows laptop)

1. Install Docker Desktop (WSL 2 backend). Move its disk image to D:
   (Docker Desktop -> Settings -> Resources -> Advanced -> Disk image location), so the database
   volume and images live on D: too.
2. Give WSL 2 enough memory: create `%UserProfile%\.wslconfig` with

   ```
   [wsl2]
   # 16 GB laptop: leave about 4 GB for Windows (8 GB laptop: memory=6GB)
   memory=12GB
   swap=8GB
   ```

   Keep comments on their own line, and check the file is not saved as `.wslconfig.txt`.

   then run `wsl --shutdown` and restart Docker Desktop. With 8 GB RAM use the small model
   (`LLM_MODEL=phi3.5`) or `LLM_MODE=mock`.
3. In PowerShell, from the repository folder:

   ```powershell
   .\make.ps1 demo      # .env with generated secrets, build, database, seed, detection, printed demo steps
   ```

   Open http://localhost:8080 and sign in with an account printed by `make.ps1 demo` (passwords
   are generated into `.env`, which is never committed). If another program already uses port 8080
   (for example an Oracle database listener) or 15432, set `WEB_PORT` or `DB_HOST_PORT` in `.env`. `.\make.ps1 help` lists every target; the
   same targets exist in the `Makefile` for Git Bash, WSL or Linux.
4. Optional language model: `.\make.ps1 models` pulls `LLM_MODEL` (Qwen2.5-7B-Instruct, about
   4.7 GB) into the `ollama_models` Docker volume and the embedding model into
   `D:\VoltGuard\models\hf`; then set `LLM_MODE=ollama` in `.env`. Without it the app runs in mock
   mode (a "mock" badge shows).
5. Optional GPU: with an NVIDIA GPU and a current driver, `make.ps1` (and the `Makefile`) add
   `docker-compose.gpu.yml` automatically, so Ollama runs on the GPU; check with
   `docker compose exec ollama nvidia-smi`, and set `VG_GPU=0` to force CPU. When you run
   `docker compose` by hand, add `-f docker-compose.yml -f docker-compose.gpu.yml`. On a GPU the
   live model drafts the report assessment fast enough for the demo, so `REPORT_MODE=live` works,
   with `predrafted` as the fallback.

All bulky files live under `DATA_ROOT` (default `D:/VoltGuard`): datasets, uploads, photos, PDFs,
logs, the audit anchor, MLflow runs and the pattern models. PostgreSQL and the Ollama models sit
in named Docker volumes, which are on D: once Docker's disk image is there (a ~5 GB model loads
slowly through a Windows-drive bind mount).

| Service (lite profile, default) | Role |
| --- | --- |
| `db` | PostgreSQL 16 + TimescaleDB + pgvector, row-level security by region |
| `api` | FastAPI: pipeline, case service, agents, job scheduler (APScheduler), audit anchor |
| `web` | React case pages, Data manager, inspector PWA (`/#/field`) |
| `ollama` | Local open-weight language model |
| `proxy` | Caddy: one entry point (port 8080) for web and API; the only exposed service |

`docker compose --profile full up -d` adds Airflow, Keycloak, MinIO, Celery/Redis, MLflow and
Prometheus/Grafana to show the R1 architecture; the app keeps using the lite implementations
(`DEVIATIONS.md`).

## Telegram dispatch bot

Dispatch runs through a Telegram bot (SRS 5.1–5.2):
1. A new case sends the supervisor a **dispatch suggestion** with *Approve / Reject*.
2. Approval sends the team the **assignment** with *Accept / On my way / Can't attend*.
3. *Can't attend* tells the supervisors to reassign.
4. Reminders and escalations arrive in the same chats.

Rules:
- Every press runs as the linked person, under their role and region.
- Every press is written to the case history and the audit log.
- Each message is answered once.
- Messages carry a case ID and link only.

- **Without a bot token** (default) the bot runs inside the app: **Dispatch** page for supervisors
  (also remote sign-out of a lost inspector phone), **Messages** tab in the inspector app.
- **With a real bot:**
  1. Telegram → @BotFather → `/newbot` → copy the token.
  2. Set `TELEGRAM_BOT_TOKEN=...` in `.env`, then run `docker compose up -d api`.
  3. Each supervisor (**Dispatch → Link Telegram**) and inspector (phone app **Messages → Link Telegram**)
     gets a code and sends `/start CODE` to the bot.

  Other commands: `/mycases`, `/whoami`, `/unlink`, `/help`. Pressing a button in Telegram or in the app
  gives the same result.

## Public link for judges (Cloudflare Tunnel)

- Judging: a stable hostname. Easiest: create a tunnel in the Cloudflare dashboard with public hostname
  -> `http://proxy:80`, put `TUNNEL_TOKEN` and `TUNNEL_HOSTNAME` in `.env`, run `.\make.ps1 tunnel-token`
  (step by step in `HOW_TO_RUN.md`). Alternative: copy `deploy/cloudflared/config.example.yml` to
  `config.yml` (git-ignored), fill it in, run `.\make.ps1 tunnel-named`. `.\make.ps1 tunnel-stop` ends sharing.
- Testing: `.\make.ps1 tunnel` starts a quick tunnel (random trycloudflare.com address, no account,
  no uptime guarantee, no server-sent events: the app polls). It writes the address to
  `PUBLIC_BASE_URL` so case links in messages work, and refuses to restart a running tunnel: a new
  address breaks the phone's saved sign-in, its offline cases and every link already sent.
- Only the proxy is exposed; the database, Ollama and admin ports are not. `/api/metrics` and the
  API docs are blocked at the proxy.
- Optional Cloudflare Access: in the Cloudflare dashboard (Zero Trust -> Access -> Applications)
  add a self-hosted application for the tunnel hostname with a policy allowing only the judges'
  e-mail addresses (one-time PIN login).
- Keep the laptop on, plugged in, with sleep disabled during judging (`DEMO.md`).

## Data modes

The detection pipeline reads only the canonical tables (`backend/voltguard/data/canonical.py`).
`config/data_sources.yaml` picks the source per table; switching is a config change plus
`.\make.ps1 pipeline`, with no code changes.

| Mode | What it uses | Needs |
| --- | --- | --- |
| Offline (default, used for the demo) | Built-in synthetic tropical household profiles; pattern model trained on synthetic SGCC-style windows | Nothing to download |
| Public datasets | London smart-meter profiles (also as canonical tables), SGCC theft data for the pattern model, data.gov.my monthly seasonality | `.\make.ps1 fetch` (Kaggle API key for SGCC and London; prints manual steps when a download fails), then `python -m voltguard convert` |
| Uploads | Your own files in `DATA_ROOT/uploads/<dataset>/` (then `.\make.ps1 ingest -Dataset <name>`) or the admin Data manager page | `data/uploads/README.md`, templates and `schema.yaml` |

Voltages are generated by the load-flow model, because the open datasets hold kWh only, so R0
shows that the voltage locator works on physics-consistent data, not on TNB meters (SRS AS-3).

## Development and tests

```bash
python3 -m venv .venv && .venv/bin/pip install -r backend/requirements.txt
cd backend
../.venv/bin/python -m voltguard train-models   # pattern model + autoencoder (under a minute)
../.venv/bin/python -m pytest                    # 100 tests, named after SRS IDs; DB tests start a throwaway PostgreSQL
../.venv/bin/python -m pytest -m e2e             # 3 browser tests: demo steps 1-7, page speed, the inspector app (needs Node, Chromium)
../.venv/bin/python ../scripts/e2e_use_cases.py  # 68 browser checks: every use case from every account (docs/REVIEW_AND_TEST_REPORT.md)
../.venv/bin/python -m tests.local_stack --cases # whole stack without Docker: web on :4173 (Linux, PostgreSQL 16 binaries)
```

`python -m voltguard --help` lists the commands (simulate, tune, simreport, migrate, seed,
pipeline, ingest, retrain, snapshot, demo, ...). Results: `reports/simulation_report.md`
(held-out and stress tests) and `reports/backtest_report.md` (`scripts/backtest.py`).

## Status: what works, what does not, what needs TNB

**Works (tested; see `TRACEABILITY.md`)**: data layer with adapters, upload validation, versions
and source switching; zone balance with uncertainty margin, gap start, flatness, conventional
meters and no-meter zones; voltage locator; features, legitimate-use and rooftop-solar tags;
additive score with reasons that add up; PostgreSQL with row-level security, column grants and
personal details only through the case service; sign-in, remote sign-out and audit hash chain
with daily anchors; case job with random sample, claims, supervisor-only assignment, outcomes and
status rules; dispatch suggestions, reminders and escalations; inspector PWA with an encrypted
offline store that is wiped; report drafts with placeholders, two approvals and PDF export;
region-limited chatbot whose answers come with a chart, the table and the query used; Telegram
dispatch bot with buttons (in-app simulator without a token); field assistant with citations or "not found"; similar cases; notes
scrubber with Malaysian recognisers; agent guardrails; retraining with versions and both hit
rates; monitoring alerts; zone-level Power BI views and CSV snapshot; the 7 live demo steps in a
browser (about 20 s automated, mock mode).

**Does not work yet, or not shown (reported as is)**
- NFR-09 is nearly met for ranked zones and not met overall (`reports/simulation_report.md`, held-out settings,
  which now include theft hidden behind rooftop solar):
  - 26 of 27 thefts in ranked zones reach the top 5%. The miss is a 1.3% partial bypass at rank 4 in a zone
    whose top 5% is 3 homes, behind another theft in the same zone.
  - 26 of 36 thefts overall. Most of the other 9 are thefts of about 1% of supply or less, inside the
    uncertainty margin, so their zones are not flagged.
  - One zone with a 7.3% gap (TX-NOR-107) is not flagged: the gap is above the threshold on 12 of the last
    14 days, but the rule needs 7 days in a row and noise breaks the run twice.
- Rooftop solar (FR-PS-10): 0 of 18 held-out solar homes (plain, home battery, unregistered export) reach
  the top suspects; 8 of 8 solar homes that also steal and sit in ranked zones reach the top 5%.
- The live language model path (Ollama) and the real Telegram bot are implemented but were tested
  here only through mock mode, the in-app chat and a recorded Telegram API; Cloudflare tunnels were
  not run here.
- Public legal texts are not in the repository: they are saved in `DATA_ROOT/docs_rag/` (listed in
  `data/docs_rag/sources.yaml`) and indexed with `python -m voltguard index-docs`. This laptop has the
  Electricity Supply Act (Bahasa Melayu reprint), the Penal Code and Energy Commission guidelines. Two of the
  guidelines are scanned PDFs with no text layer and are skipped until an OCR'd copy is saved. On a machine
  without them, legal questions return "not found" and reports cite Section 37 by name only.
- The pattern model is trained on the real SGCC data, but it separates theft only weakly on single 28-day
  windows (held-out AUC 0.55, OI-3). Its weight in the score is small (0.065), so the ranking rests mainly
  on the zone balance, the voltage locator and the usage features.
- NFR-01 (2-hour nightly run for 100,000 meters) is measured up to 13,088 homes, not at 100,000.
  The run streams readings in meter batches and detects in zone batches (config `pipeline`), and gives
  the same results as one batch (`tests/test_pipeline_batches.py`). Measured on 4 cores, load and
  detection together:

  | Homes | Readings | Time | Peak memory |
  | --- | --- | --- | --- |
  | 6,458 | 17 million | 100 s | 2.8 GB (8.4 GB unbatched) |
  | 13,088 | 35 million | 219 s | 3.1 GB |

  At that rate 100,000 meters is about 30 minutes and 3–5 GB.
- The full profile's services are defined but not wired into the app; the `.pbix` is not built
  (layout in `powerbi/POWERBI.md`, data in `powerbi/snapshot/`).
- Fairness by housing tenure (NFR-11) needs tenure data that R0 does not have; flag rates by area
  are in `rpt_flag_rates`.
- The real-world hit rate (NFR-10) and live connections to utility systems are R1 by design.

**Open issues that need TNB input (SDD 11.2)**
- OI-1 / AS-3: do smart meters store interval voltage? (decides whether the voltage locator runs)
- OI-2: the pilot zone's current inspection hit rate (baseline for NFR-10)
- OI-8 / AS-7: phase and feeder branch per meter in the network model
- OI-9 / AS-8: transformer and cable parameters for the loss model (also narrows the uncertainty margin)
- OI-7: acceptable false-alarm rate (sets the case threshold; see the threshold sweep)
- OI-10: share of inspections for random samples
- OI-11 / AS-9: rooftop solar registrations per premise
- OI-12 and OI-4: access to past data and confirmed cases for the back-test (`scripts/backtest.py --source active`)
- OI-3, OI-5, OI-6: SGCC transfer to Malaysian homes, roster and messaging systems, GPU server for R1

## Documents

- `docs/REVIEW_AND_TEST_REPORT.md`: SRS/SDD review, end-to-end test of every use case, bugs fixed, suggestions
- `docs/UI_UX_DESIGN_REQUIREMENTS.md`: redesign requirements, tokens, screens, prompts and plugins
- `PLAN.md`: milestones and file tree
- `HANDOFF.md`: status and how to continue in a new session (with the graphify code graph in `graphify-out/`)
- `TRACEABILITY.md`: every SRS requirement mapped to code and tests (generated)
- `DEVIATIONS.md`: lite-profile, library and data swaps, with reasons
- `DEMO.md`: the demo script, backup steps and rehearsal checklist
- `MODELS.md`: models and their licences
- `powerbi/POWERBI.md`: manager dashboard layout and connection
- `data/uploads/README.md`: how to upload new datasets
