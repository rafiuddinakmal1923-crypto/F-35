# VoltGuard AI R0: review and end-to-end test report

Date: 2026-10-27 · Branch `claude/practical-clarke-t5uwrc` · Data: simulated only, fake personal details only.

## 1. Does the build meet the SRS and SDD?

**Yes for every functional requirement.** All 45 Must, Should and Could requirements (FR-DI, ZD, PS, UI,
IW, ML, AG, AD) are built. Each one has at least one automated test named after it (see `TRACEABILITY.md`).
The gaps are all non-functional requirements that a laptop prototype cannot show.

| Area | SRS / SDD goal | Status |
| --- | --- | --- |
| Zone detection | Energy balance with an uncertainty margin, flag rule, gap start, flatness, no-balance zones | Met |
| Premise scoring | 0–100 risk score, voltage locator, three reasons that add up, legitimate-use tags, risk wording only | Met |
| Dashboard | Overview, zone, premise and case pages; masking; filters; PDF export | Met |
| Inspection workflow | Case job, manual cases, supervisor-only assignment, outcomes, status flow, random sample | Met |
| Models | Retrain with versions, model-ranked vs random-sample hit rates, drift and missing-data alerts | Met |
| AI agents | Report draft with placeholders and two approvals, dispatch, chatbot, field assistant, similar cases, no autonomous action | Met. The chatbot now draws charts (this round) |
| Messaging (SRS 5.1–5.2) | "A Telegram bot in R0" | **Was one-way only; now a working dispatch bot** (this round) |
| Administration and audit | Role and region limits, tamper-evident audit log, thresholds without code changes | Met |
| NFR-16 device security | Encrypted phone store, wipe, **remote sign-out** | Remote sign-out existed only as an API call; **now a button** (this round) |
| NFR-01, 03, 05, 06 | 100k meters in 2 h, 99% uptime, scale-out, TLS and single sign-on | Not testable in R0 (see the efficiency rating: detection fits in time, but memory needs zone batching) |
| NFR-09 | Every held-out theft in the top 5% | 18/18 in ranked zones, 18/24 overall (small partial bypasses sit inside the uncertainty margin) |
| NFR-10 | Real hit rate beats TNB's baseline | R1 only (needs TNB data) |

## 2. End-to-end test: every use case, every account

A browser drove the real web app (desktop and phone sizes) using the team's own accounts and passwords.
The passwords were seeded into a throwaway local stack and never stored in the repository. Every check was
also confirmed through the API where it matters (refusals, masking).

**Result: 68 of 68 checks passed** after the fixes in section 3. The first run passed 63 of 65: two checks
failed because of the test script (the manager is shown no premise ranking by design; a stale "done" label),
and it found the bugs listed below.

| Use case | Account(s) | What was checked | Result |
| --- | --- | --- | --- |
| Sign-in | all 9 listed accounts | Each signs in with its password and lands on its home page; a wrong password is refused | 19/19 |
| UC-01 Review leaking zones | manager.cen, manager.nor | CEN sees only CEN zones in gap order, with no premise IDs; district and date filters; NOR sees only NOR; CEN zone refused to NOR | 6/6 |
| UC-02 Investigate a zone | analyst.cen, analyst.nor | Zone view, ranked suspects, premise reasons add up, details masked, no-balance zone marked, other region refused, manual case | 6/6 |
| UC-03 Assign an inspection | supervisor.cen, analyst.cen | Case job, random sample from flagged zones only, analyst cannot assign, claim, nearest-team approval with joint-operation warning, message holds a link only, manual assignment, **approval from the Telegram chat** | 8/8 |
| UC-04 Inspect and record | inspector.b (phone) | Assigned case with address and warning, offline outcome with photo synced later, personal details typed into notes stored redacted, field assistant with source, disconnection refused, no access to zones, status to Reporting, **Accept in the Messages tab**, wipe after remote sign-out | 10/10 |
| UC-05 Case report | analyst.cen, manager.cen | Draft with placeholders citing Section 37, analyst approval, three similar cases, manager's second approval, PDF download | 3/3 |
| UC-06 Analyst chatbot | manager.cen | Answers built from the rows, other region refused, **charts drawn**, query shown | 2/2 |
| UC-07 Retrain and compare | datasci | Detection run, retrain records a version with both hit rates, no personal details | 3/3 |
| UC-08 Review access | auditor | Log and hash-chain check, every action type logged, no access to cases or zones | 4/4 |
| Admin | admin | Settings editable (not by analysts), data manager, bad upload rejected with a report, no personal details, remote sign-out | 6/6 |
| Language | manager.cen | Bahasa Melayu switch | 1/1 |

Automated suite: 91 non-browser tests (plus the 3 browser tests) pass. That includes 7 new Telegram tests,
6 chart tests and 3 regression tests.

## 3. Bugs found and fixed

| # | Bug | Effect | Fix |
| --- | --- | --- | --- |
| 1 | The voltage chart marked a "hidden load" position on every phase/branch line, even where the drop was only noise | Misleading: all nine lines appeared to have a tap | Marked only where the fitted drop is above `voltage.min_drop_v` |
| 2 | The usage chart drew a broken line (browser error) for monthly-read meters, and joined gaps | Empty or wrong chart on some premises | Gaps break the line; the page says the meter has no daily readings |
| 3 | The usage chart's first day was a partial day | A false dip at the left edge | The window now starts at local midnight |
| 4 | A reason read "estimated hidden load is about 0 m from this premise" | Awkward wording | "…at or right next to this premise" |
| 5 | Managers got "forbidden" errors loading evidence photos on the case they approve for export | Broken images; the manager cannot see the evidence they approve | Managers see photos once the content is approved, and not before |
| 6 | The manager's zone page had a silently missing section | Confusing | It now says rankings are for analysts and supervisors |
| 7 | Supervisors were never told a dispatch suggestion was waiting | They had to find it on the Cases page | A suggestion message with Approve / Reject buttons |
| 8 | Remote sign-out of a lost phone had no button | NFR-16 could not be done from the app | An "Inspector phones" card on the Dispatch page |
| 9 | The top bar overflowed on phones | Sideways scrolling | The top bar wraps |
| 10 | Chatbot answers said only "2 row(s)" | Unhelpful | A sentence built from the rows, plus a chart |
| 11 | **The photo-upload endpoint ran database work on the API's event loop.** When it waited for the audit lock, the lock holder could never commit | **The whole API froze** (found when a rerun hung at the phone sync); timing-dependent, so it could hit the live demo | Endpoints are plain functions that run in worker threads; a guard test fails if any endpoint is async |
| 12 | Laptop setup: Debian 13 base image, port 5432 taken, port 8080 taken (Oracle), map tiles refused | The stack would not start on the team laptop | Debian 12 base image; `DB_HOST_PORT` and `WEB_PORT` settings; tiles send the site origin |

## 4. Remaining unfinished task: done

**Telegram dispatch bot.** The bot works in both modes:
- **Real Telegram**, when `TELEGRAM_BOT_TOKEN` is set: it sends messages and polls for button presses.
- **In-app simulator** otherwise: the Dispatch page for supervisors and the Messages tab on the phone.

Both modes run the same code for each button press. How it works:
1. A new case: the supervisor gets *Dispatch suggestion* with **Approve / Reject**.
2. Approve: the assigned team gets *New inspection* with **Accept / On my way / Can't attend**.
3. Can't attend: the supervisor gets *Cannot attend; please reassign*.
4. Reminders and escalations arrive in the same chats.
5. Linking a real chat: Dispatch → **Link Telegram** gives a code; send `/start CODE` to the bot.
   Other commands: `/mycases`, `/whoami`, `/unlink`, `/help`.
6. Rules:
   - Each press runs as the linked person, with their role and region.
   - Each press is recorded in the case history and the audit log.
   - Each message can be answered once.
   - No message ever holds a name or address.

Setting up a real bot:
1. In Telegram, talk to @BotFather → `/newbot` → copy the token.
2. Put the token in `.env` as `TELEGRAM_BOT_TOKEN=...`.
3. Run `docker compose up -d api`.
4. Each supervisor and inspector links their chat from the app.

## 5. Suggested improvements

### Usability (high value, low effort first)
1. **Global search** (zone, premise or case ID) in the top bar; analysts type IDs all day.
2. **"My work" home page per role:**
   - supervisor: suggestions waiting, overdue cases, teams on duty;
   - analyst: unclaimed cases, reports to approve;
   - manager: exports to approve.
3. **Badges on the menu** (Dispatch 3, Cases 5) and a notification bell that uses the same messages as the bot.
4. **Shorter suspect table:**
   - top 10 by default, then "show all";
   - the reason as a one-line chip, with the full text on hover;
   - sticky table headers.
5. **A case timeline**, with icons per event (created, suggested, approved, accepted, on the way, visited,
   report, closed) and the Telegram actions shown on it.
6. **Plain-language help for every figure:**
   - "± u" → "uncertainty";
   - "CV 0.16" → "flat 24/7 load";
   - a "?" tooltip on each KPI.
7. **Toasts and confirmations:**
   - "Case C-2026-0006 assigned to Team B";
   - an undo for a mistaken reject, within 10 seconds.
8. **Skeleton loaders and empty states** that say what to do next ("No open cases. Run the case job").
9. **Phone app:**
   - larger tap targets;
   - "Navigate" (open the address in Google Maps / Waze);
   - "Call the supervisor";
   - a camera button with photo count and size;
   - a clear offline banner.
10. **Accessibility:**
    - keyboard focus rings;
    - ARIA labels on charts;
    - contrast check on chips;
    - all labels in BM (several page texts are English-only today).

### Features
1. **Map upgrade:**
   - zones drawn by gap size and colour;
   - a cluster view for the whole region;
   - an offline tile fallback;
   - a heat layer of the gap over time (zone level only).
2. **What-if on Settings:** preview how many zones would be flagged with a new threshold before saving.
3. **Weekly manager digest** (PDF or Telegram): flagged zones, kWh recovered, hit rates, overdue cases.
4. **Estimated value at risk:** kWh/day × tariff → RM/month per zone and per case, for prioritising (tariff
   table from TNB).
5. **Inspector route planning** for several cases in one day (nearest-neighbour order), shown in the phone app.
6. **Chatbot:**
   - follow-up questions ("and last month?");
   - pinning a chart to a personal dashboard;
   - more templates (recovered energy, overdue cases by team, time to visit).
7. **Telegram:**
   - a photo upload from Telegram into the case (encrypted, then deleted from the chat);
   - location sharing on "On my way".
8. **Data quality page:** meters with missing days, clock errors, duplicates, with a trend.
9. **Zone batching in the nightly run.** Needed for 100,000 meters (see the efficiency rating) and an
   incremental daily load.
10. **Single sign-on (Keycloak) and TLS** in the full profile, for NFR-06 in R1.

## 6. How to repeat the test

```bash
cd backend
../.venv/bin/python -m pytest -q          # 100 tests, about 8 minutes
../.venv/bin/python -m pytest -m e2e -q   # browser tests (Chromium)
../.venv/bin/python ../scripts/e2e_use_cases.py   # the 68-check run of section 2; screenshots in .data/e2e_use_cases/
```

With your own passwords: `VG_PASSWORDS_FILE=/path/outside/repo/passwords.json` (a JSON object of user to password).

## 7. Second round (after the review): what was added and rechecked

| Item | Status | Where |
| --- | --- | --- |
| Route planner | Done: visiting order (within 15% of the best order, 3% on average, on random sets of six stops), phone route card with Navigate, supervisor map | `agents/route.py`, `GET /route`, `tests/test_route.py` |
| Weekly manager summary | Done: page, PDF, Monday message | `service/digest.py`, `GET /weekly`, `tests/test_digest.py` |
| Usability | Done: "my work" home and badges, global ID search, help on every figure, top-10 suspects, case stepper and icon timeline, cases board, phone bottom tabs | `service/work.py`, `web/src` |
| UI redesign | Done to `docs/UI_UX_DESIGN_REQUIREMENTS.md` (tokens, Inter, icons, KPI sparklines, score rings, sign-in page, dark mode); no sideways scrolling at 360 px on any page | `web/src` |
| 100,000 meters (NFR-01) | Batched run: peak memory 2.8 GB at 6,458 homes (was 8.4 GB) and 3.1 GB at 13,088 homes, 219 s, same results as one batch; extrapolated 100,000 meters is about 30 min | `service/pipeline.py`, `tests/test_pipeline_batches.py` |
| Power BI | Prepared: theme, DAX measures, build prompt for Claude on the laptop; the `.pbix` needs Power BI Desktop on Windows | `powerbi/` |
| Bugs found this round | Chat buttons stayed pressable after a decision made on the case page; the route card hid the case links on the phone; dark-mode menu contrast; phone tab bar layout; "1 stops" | Fixed, with tests where the behaviour is server-side |

**Alignment recheck.**
- Every addition keeps the SRS and SDD rules: role and region limits, masking, audit, risk-only wording,
  people decide, and messages hold a case ID and link only.
- It is listed in `DEVIATIONS.md` ("Additions after the R0 review").
- The one new outward flow is the Navigate buttons, which hand coordinates to Google Maps or Waze when an
  inspector taps them. This is flagged there for TNB to decide in R1.

**Final run (second round):**
- 100 non-browser tests pass;
- 3 browser tests pass;
- the end-to-end use-case run passes 68 of 68 checks on the redesigned app.
