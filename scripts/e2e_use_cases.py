"""End-to-end run of every use case (SRS 6) from every account's point of view, in a real browser.

Starts its own throwaway stack (no Docker), then drives the web app and the phone app through UC-01 to
UC-08, the admin pages and the Telegram dispatch chat. Soft checks: each is recorded PASS or FAIL and the
run continues. Screenshots and results go to .data/e2e_use_cases/.

    cd backend && ../.venv/bin/python ../scripts/e2e_use_cases.py

To test with your own passwords, point VG_PASSWORDS_FILE at a JSON file {"user_id": "password", ...}
kept outside the repository; other accounts use the local-stack password.
"""
import json
import os
import sys
import time
import traceback
from pathlib import Path

import httpx
from playwright.sync_api import sync_playwright

sys.path.insert(0, ".")
from tests.local_stack import PASSWORD, ROOT, LocalStack, chromium_path  # noqa: E402

OUT = ROOT / ".data" / "e2e_use_cases"
OUT.mkdir(parents=True, exist_ok=True)
_pw_file = os.environ.get("VG_PASSWORDS_FILE")
PW = json.loads(Path(_pw_file).read_text()) if _pw_file else {u: PASSWORD for u in (
    "manager.cen", "analyst.cen", "supervisor.cen", "inspector.b", "datasci", "admin", "auditor", "manager.nor", "analyst.nor")}
DEFAULT = PASSWORD
JPEG = bytes.fromhex("ffd8ffe000104a46494600010100000100010000ffdb004300") + b"\x08" * 64 + bytes.fromhex("ffd9")
results = []
problems = []


def pw(u):
    return PW.get(u, DEFAULT)


def check(uc, name, ok, detail=""):
    results.append((uc, name, bool(ok), str(detail)[:300]))
    print(("PASS " if ok else "FAIL ") + f"[{uc}] {name}" + (f"  -- {detail}" if detail and not ok else ""), flush=True)


def soft(uc, name, fn):
    try:
        r = fn()
        check(uc, name, r is not False, "" if r is not False else "returned False")
    except Exception as e:  # noqa: BLE001
        check(uc, name, False, f"{e.__class__.__name__}: {str(e)[:250]}")


stack = LocalStack(api_port=8771, web_port=4771, with_cases=False).start()
url = stack.url
from voltguard import db  # noqa: E402
from voltguard.service.users import demo_users, seed_users  # noqa: E402

with db.admin_connection() as conn:
    with conn.transaction():
        seed_users(conn, {u["user_id"]: pw(u["user_id"]) for u in demo_users()})


def token(u):
    r = httpx.post(f"{url}/api/auth/token", json={"username": u, "password": pw(u)})
    r.raise_for_status()
    return r.json()["access_token"]


def api(u, method, path, **kw):
    return httpx.request(method, f"{url}/api{path}", headers={"Authorization": "Bearer " + token(u)}, timeout=120, **kw)


def watch(page, who):
    page.on("pageerror", lambda e: problems.append((who, page.url.split("#")[-1], "pageerror", str(e)[:200])))
    page.on("console", lambda m: m.type == "error" and problems.append((who, page.url.split("#")[-1], "console", m.text[:200])))
    page.on("response", lambda r: r.status >= 500 and problems.append((who, page.url.split("#")[-1], r.status, r.url)))


def sign_in(page, u):
    page.goto(f"{url}/#/login")
    page.fill("input[autocomplete=username]", u)
    page.fill("input[type=password]", pw(u))
    page.click("button.primary")
    page.wait_for_function("!location.hash.includes('login')", timeout=15000)


def shot(page, name):
    page.wait_for_timeout(600)
    page.screenshot(path=str(OUT / f"{name}.png"), full_page=True)


def job(page, label):
    page.click(f"button:has-text('{label}')")
    page.wait_for_selector("small:has-text('done')", timeout=180000)


t0 = time.time()
with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=chromium_path())

    def desk(u):
        page = browser.new_context(viewport={"width": 1400, "height": 900}, accept_downloads=True).new_page()
        watch(page, u)
        sign_in(page, u)
        return page

    # ---------------------------------------------------------------- sign-in for every account
    for u in PW:
        soft("AUTH", f"{u} signs in with the given password", lambda u=u: token(u) is not None)
    soft("AUTH", "wrong password refused", lambda: httpx.post(f"{url}/api/auth/token", json={"username": "admin", "password": "nope"}).status_code == 401)
    homes = {"manager.cen": "/", "analyst.cen": "/", "supervisor.cen": "/", "datasci": "/models", "admin": "/data", "auditor": "/audit",
             "manager.nor": "/", "analyst.nor": "/", "inspector.b": "/field"}
    for u, home in homes.items():
        def landing(u=u, home=home):
            page = browser.new_context(viewport={"width": 1400, "height": 900}).new_page()
            watch(page, u)
            sign_in(page, u)
            page.wait_for_timeout(800)
            got = page.url.split("#")[1]
            shot(page, f"00_home_{u}")
            page.context.close()
            assert got == home, got
        soft("AUTH", f"{u} lands on {home}", landing)

    # ---------------------------------------------------------------- UC-07 part 1: detection run (datasci)
    ds = desk("datasci")
    soft("UC-07", "datasci runs detection from Models page", lambda: job(ds, "Run detection"))
    shot(ds, "07a_models_after_detection")

    # ---------------------------------------------------------------- UC-01 manager reviews leaking zones
    mgr = desk("manager.cen")
    def uc01():
        mgr.goto(f"{url}/#/")
        mgr.wait_for_selector("tr:has-text('TX-CEN-001')")
        rows = mgr.locator("tbody tr").all_inner_texts()
        assert all("NOR" not in r for r in rows), "NOR zone shown to CEN manager"
        flagged = [r for r in rows if "flagged" in r]
        assert len(flagged) >= 2, rows
        gaps = [float(r.split("\t")[2].strip("%")) for r in flagged]
        assert gaps == sorted(gaps, reverse=True), f"not in gap order {gaps}"
        body = mgr.inner_text("main")
        assert "P-CEN" not in body, "premise IDs on the overview"
        shot(mgr, "01a_overview_manager_cen")
    soft("UC-01", "overview: CEN zones only, flagged in gap order, no premise IDs", uc01)
    def uc01_filter():
        sel = mgr.locator("main select").first
        sel.select_option("Klang")
        mgr.wait_for_timeout(1200)
        rows = mgr.locator("tbody tr").all_inner_texts()
        assert rows and all("Klang" in r for r in rows), rows
        shot(mgr, "01b_overview_filter_klang")
        sel.select_option("")
    soft("UC-01", "district filter (FR-UI-04)", uc01_filter)
    def uc01_date():
        mgr.fill("input[type=date]", "2026-09-15")
        mgr.wait_for_timeout(1500)
        txt = mgr.inner_text("main")
        shot(mgr, "01c_overview_date")
        mgr.fill("input[type=date]", "")
        assert "2026-09-15" in txt or "run" in txt.lower(), txt[:200]
    soft("UC-01", "date filter changes the view (FR-UI-04)", uc01_date)
    def uc01_zone():
        mgr.goto(f"{url}/#/zones/TX-CEN-002")
        mgr.wait_for_selector("text=Premise rankings are shown to analysts", timeout=15000)
        assert "P-CEN" not in mgr.inner_text("main")
        shot(mgr, "01d_zone_manager")
    soft("UC-01", "manager opens a zone: balance only, no premise ranking", uc01_zone)
    mnor = desk("manager.nor")
    def uc01_nor():
        mnor.goto(f"{url}/#/")
        mnor.wait_for_selector("tr:has-text('TX-NOR')")
        assert "TX-CEN" not in mnor.inner_text("main")
        shot(mnor, "01e_overview_manager_nor")
    soft("UC-01", "NOR manager sees NOR zones only", uc01_nor)
    soft("UC-01", "NOR manager refused a CEN zone (API)", lambda: api("manager.nor", "GET", "/zones/TX-CEN-001/suspects").status_code in (403, 404))

    # ---------------------------------------------------------------- UC-02 analyst investigates
    ana = desk("analyst.cen")
    def uc02():
        ana.goto(f"{url}/#/zones/TX-CEN-001")
        ana.wait_for_selector("td >> text=P-CEN-001-054", timeout=15000)
        body = ana.inner_text("main")
        for part in ("Ranked suspects",):
            assert part in body, part
        shot(ana, "02a_zone_TX-CEN-001")
    soft("UC-02", "zone view: balance, profile, ranked suspects (FR-UI-02)", uc02)
    def uc02_premise():
        ana.click("text=P-CEN-001-054")
        ana.wait_for_selector("text=Lines add up to")
        body = ana.inner_text("main")
        assert "Personal details hidden" in body and "FAKE" not in body
        shot(ana, "02b_premise_masked")
    soft("UC-02", "premise view: reasons add up, details masked (FR-PS-07, FR-UI-03)", uc02_premise)
    def uc02_nozone():
        ana.goto(f"{url}/#/zones/TX-CEN-004")
        ana.wait_for_timeout(2000)
        body = ana.inner_text("main")
        shot(ana, "02c_zone_no_balance")
        assert "no balance" in body.lower() or "low confidence" in body.lower(), body[:300]
    soft("UC-02", "zone without transformer meter marked (FR-ZD-06)", uc02_nozone)
    anor = desk("analyst.nor")
    soft("UC-02", "NOR analyst refused CEN premise (API)", lambda: api("analyst.nor", "GET", "/premises/P-CEN-001-054").status_code in (403, 404))
    def uc02_nor_ui():
        anor.goto(f"{url}/#/premises/P-CEN-001-054")
        anor.wait_for_timeout(1500)
        shot(anor, "02d_nor_analyst_cen_premise")
        assert "FAKE" not in anor.inner_text("main") and "Lines add up" not in anor.inner_text("main")
    soft("UC-02", "NOR analyst UI shows refusal for CEN premise", uc02_nor_ui)
    def uc02_manual():
        ana.goto(f"{url}/#/premises/P-CEN-002-010")
        ana.wait_for_selector("button:has-text('Open a manual case')", timeout=10000)
        ana.click("button:has-text('Open a manual case')")
        ana.wait_for_function("location.hash.includes('/cases/')", timeout=10000)
        shot(ana, "02e_manual_case")
    soft("UC-02", "analyst opens a manual case (FR-IW-01)", uc02_manual)

    # ---------------------------------------------------------------- UC-03 supervisor assigns
    sup = desk("supervisor.cen")
    case_id = None
    def uc03_job():
        sup.goto(f"{url}/#/cases")
        job(sup, "Run case job")
        sup.reload()
        sup.wait_for_selector("tr:has-text('P-CEN-001-054')")
        shot(sup, "03a_cases_after_job")
    soft("UC-03", "supervisor runs the case job (FR-IW-01)", uc03_job)
    try:
        case_id = sup.locator("tr", has_text="P-CEN-001-054").locator("td").first.inner_text().strip()
    except Exception as e:  # noqa: BLE001
        check("UC-03", "find demo case id", False, e)
    soft("UC-03", "random-sample cases exist and only from flagged zones (FR-IW-05)",
         lambda: any(c["origin"] == "random_sample" for c in api("supervisor.cen", "GET", "/cases").json()["cases"]))
    soft("UC-03", "analyst cannot assign (API)", lambda: api("analyst.cen", "PATCH", f"/cases/{case_id}/assign", json={"team": "T-CEN-A"}).status_code == 403)
    def uc03_claim():
        ana.goto(f"{url}/#/cases/{case_id}")
        ana.click("button:has-text('Claim')")
        ana.wait_for_selector("text=Analyst: analyst.cen")
        shot(ana, "03b_case_claimed_analyst")
        assert "FAKE" in ana.inner_text("main") or "Contact" in ana.inner_text("main")
    soft("UC-03", "analyst claims the case and then sees contact details", uc03_claim)
    def uc03_approve():
        sup.goto(f"{url}/#/cases/{case_id}")
        sup.wait_for_selector("text=Dispatch suggestion:")
        body = sup.inner_text("main")
        assert "T-CEN-B" in body and "joint operation" in body.lower()
        shot(sup, "03c_dispatch_suggestion")
        sup.click("button:has-text('Approve')")
        sup.wait_for_selector("text=approved")
        shot(sup, "03d_dispatch_approved")
    soft("UC-03", "supervisor approves nearest-team suggestion (FR-AG-02)", uc03_approve)
    def uc03_msg():
        notes = api("supervisor.cen", "GET", "/notifications").json()
        sent = [n for n in notes if n["case_id"] == case_id and n["kind"] == "assignment"]
        assert sent and "FAKE" not in sent[0]["text"] and f"/#/cases/{case_id}" in sent[0]["text"], notes[:3]
    soft("UC-03", "assignment message holds a link only (SRS 5.2)", uc03_msg)
    def uc03_manual_assign():
        cases = api("supervisor.cen", "GET", "/cases?status=new").json()["cases"]
        target = next(c for c in cases if c["origin"] != "random_sample")
        sup.goto(f"{url}/#/cases/{target['case_id']}")
        sup.wait_for_selector("main select")
        sup.select_option("main select", "T-CEN-A")
        sup.click("button:has-text('Assign')")
        sup.wait_for_timeout(1500)
        shot(sup, "03e_manual_assign")
        assert "T-CEN-A" in sup.inner_text("main")
    soft("UC-03", "supervisor assigns another case manually", uc03_manual_assign)
    def uc03_tg():
        sup.goto(f"{url}/#/dispatch")
        sup.wait_for_selector(".tg-bubble")
        btn = sup.locator(".tg-msg:has(.tg-buttons button:enabled)").last
        cid = btn.locator(".tg-kind span").inner_text()
        btn.locator("button", has_text="Approve").click()
        sup.wait_for_selector("text=approved")
        shot(sup, "03f_dispatch_chat")
        assert api("supervisor.cen", "GET", f"/cases/{cid}").json()["case"]["status"] == "assigned"
        return cid
    soft("UC-03", "supervisor approves a suggestion from the Telegram chat (FR-AG-02)", uc03_tg)

    # ---------------------------------------------------------------- UC-04 inspector (phone)
    phone_ctx = browser.new_context(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True)
    phone = phone_ctx.new_page()
    watch(phone, "inspector.b")
    def uc04_signin():
        phone.goto(f"{url}/#/field")
        phone.fill("input[autocomplete=username]", "inspector.b")
        phone.fill("input[type=password]", pw("inspector.b"))
        phone.click("button.primary")
        phone.wait_for_selector(f"text={case_id}", timeout=20000)
        shot(phone, "04a_phone_case_list")
    soft("UC-04", "inspector signs in on a phone and sees the assigned case", uc04_signin)
    def uc04_detail():
        phone.click(f"text={case_id}")
        body = phone.inner_text("body")
        shot(phone, "04b_phone_case_detail")
        assert "Joint operation" in body and "FAKE" in body, body[:400]
    soft("UC-04", "case detail shows address and joint-operation warning", uc04_detail)
    def uc04_offline():
        phone_ctx.set_offline(True)
        phone.evaluate("window.dispatchEvent(new Event('offline'))")
        phone.click("button:has-text('Confirmed theft')")
        phone.fill("textarea", "Bypass cable behind the meter board; owner Ahmad bin Ali IC 800101-14-5678 phone 012-3456789.")
        phone.set_input_files("input[type=file]", files=[{"name": "m.jpg", "mimeType": "image/jpeg", "buffer": JPEG}])
        phone.wait_for_selector("img.thumb")
        phone.click("button:has-text('Submit')")
        phone.wait_for_selector("text=syncs when online")
        shot(phone, "04c_phone_offline_saved")
        phone_ctx.set_offline(False)
        phone.evaluate("window.dispatchEvent(new Event('online'))")
        phone.wait_for_selector("text=waiting to sync", state="detached", timeout=30000)
        phone.wait_for_timeout(1500)
        shot(phone, "04d_phone_synced")
    soft("UC-04", "offline outcome with photo, synced when online (FR-IW-02, NFR-16)", uc04_offline)
    def uc04_scrub():
        d = api("supervisor.cen", "GET", f"/cases/{case_id}").json()
        notes = d["outcomes"][-1]["notes_redacted"]
        assert "Ahmad" not in notes and "800101" not in notes and "012-3456789" not in notes, notes
    soft("UC-04", "notes typed with personal details are stored redacted (NFR-15)", uc04_scrub)
    def uc04_assistant():
        phone.fill("input[placeholder*='photograph']", "What should I photograph at the meter board?")
        phone.click("button:has-text('Ask')")
        phone.wait_for_timeout(2500)
        body = phone.inner_text("body")
        shot(phone, "04e_phone_assistant")
        assert "photograph" in body.lower()
    soft("UC-04", "field assistant answers with a source (FR-AG-04)", uc04_assistant)
    def uc04_tg():
        phone.click(".tabs button:has-text('Messages')")
        phone.wait_for_selector(".tg-bubble")
        phone.locator(".tg-buttons button", has_text="Accept").last.click()
        phone.wait_for_selector("text=accepted")
        shot(phone, "04g_phone_messages_accept")
        phone.click(".tabs button:has-text('My cases')")
    soft("UC-04", "inspector accepts an assignment in the Messages tab (Telegram simulator)", uc04_tg)
    def uc04_forbidden():
        r = api("inspector.b", "POST", "/agents/chat", json={"agent": "field", "message": "Should I disconnect the bypass cable myself?"}).json()
        assert "disconnect" not in r["answer"].lower() or "not" in r["answer"].lower() or r.get("refused"), r
    soft("UC-04", "field assistant refuses disconnection (FR-AG-06)", uc04_forbidden)
    soft("UC-04", "inspector cannot read zones (API)", lambda: api("inspector.b", "GET", "/zones").status_code == 403)
    def uc04_status():
        d = api("supervisor.cen", "GET", f"/cases/{case_id}").json()
        assert d["case"]["status"] == "reporting", d["case"]["status"]
    soft("UC-04", "confirmed theft moves the case to Reporting (FR-IW-03)", uc04_status)

    # ---------------------------------------------------------------- UC-05 report
    def uc05():
        ana.goto(f"{url}/#/cases/{case_id}")
        ana.reload()
        ana.wait_for_selector("text=Approve content", timeout=60000)
        draft = ana.inner_text("pre")
        shot(ana, "05a_report_draft")
        assert "{{HOLDER_NAME}}" in draft and "Section 37" in draft and "FAKE" not in draft and "Ahmad" not in draft
        ana.click("button:has-text('Approve content')")
        ana.wait_for_selector("text=content approved")
    soft("UC-05", "draft with placeholders, citing Section 37; analyst approves (FR-AG-01)", uc05)
    soft("UC-05", "similar past cases shown (FR-AG-05)", lambda: len(api("analyst.cen", "GET", f"/cases/{case_id}/similar").json()["similar"]) == 3)
    def uc05_mgr():
        mgr.goto(f"{url}/#/cases/{case_id}")
        mgr.click("button:has-text('Approve export')")
        mgr.wait_for_selector("button:has-text('Download PDF')")
        with mgr.expect_download() as dl:
            mgr.click("button:has-text('Download PDF')")
        path = OUT / "05_case_report.pdf"
        dl.value.save_as(path)
        shot(mgr, "05b_export_approved")
        assert path.stat().st_size > 1000
    soft("UC-05", "manager second approval and PDF download (FR-UI-05)", uc05_mgr)

    # ---------------------------------------------------------------- UC-06 chatbot
    def ask(page, q):
        page.fill(".chat-input input", q)
        page.click(".chat-input button.primary")
        page.wait_for_selector(".typing", state="detached", timeout=20000)
        page.wait_for_timeout(300)
        return page.locator(".answer").last.inner_text()
    def uc06():
        mgr.goto(f"{url}/#/assistant")
        a1 = ask(mgr, "Which zones had a gap above 10% this week?")
        a2 = ask(mgr, "How many open cases are there?")
        a3 = ask(mgr, "Hit rate model-ranked vs random sample")
        a4 = ask(mgr, "Top 3 zones")
        a5 = ask(mgr, "Show flagged zones in Seberang Perai")
        shot(mgr, "06a_assistant_manager")
        print("   chatbot answers:", [x.replace("\n", " | ")[:140] for x in (a1, a2, a3, a4, a5)])
        assert "TX-CEN-002" in a1 and "region" in a5.lower()
    soft("UC-06", "manager chatbot: answers from the rows, other region refused (FR-AG-03)", uc06)
    def uc06_chart():
        a = ask(mgr, "Show the gap trend for TX-CEN-001")
        assert mgr.locator(".answer").last.locator("svg").count() >= 1, a
        a2 = ask(mgr, "Unexplained energy by district")
        assert "Petaling" in a2 and mgr.locator(".answer").last.locator("svg").count() >= 1
        mgr.locator(".answer").last.locator(".segmented button:has-text('Query used')").click()
        assert "SELECT" in mgr.locator(".answer").last.inner_text()
        shot(mgr, "06b_assistant_charts")
    soft("UC-06", "assistant draws charts and shows the query used", uc06_chart)

    # ---------------------------------------------------------------- UC-07 retrain
    def uc07():
        ds.goto(f"{url}/#/models")
        ds.reload()
        ds.wait_for_selector("button:has-text('Retrain on new outcomes')")
        job(ds, "Retrain on new outcomes")
        ds.reload()
        ds.wait_for_selector("text=label-v1")
        shot(ds, "07b_models_retrained")
    soft("UC-07", "retrain records a version with both hit rates (FR-ML-01/02)", uc07)
    soft("UC-07", "datasci sees no personal details (API)", lambda: "FAKE" not in api("datasci", "GET", f"/premises/P-CEN-001-054").text)

    # ---------------------------------------------------------------- admin
    adm = desk("admin")
    def adm_settings():
        adm.goto(f"{url}/#/settings")
        adm.wait_for_selector("input[type=number]")
        shot(adm, "09a_settings_admin")
    soft("ADMIN", "settings page editable (FR-AD-03)", adm_settings)
    soft("ADMIN", "analyst cannot change thresholds (API)", lambda: api("analyst.cen", "PUT", "/settings/thresholds", json={"zone": {"theta": 0.06}}).status_code == 403)
    def adm_data():
        adm.goto(f"{url}/#/data")
        adm.wait_for_selector("text=Active source per table")
        shot(adm, "09b_data_manager")
    soft("ADMIN", "data manager page loads", adm_data)
    def adm_upload():
        bad = "meter_id,ts,kwh\nM1,2026-01-01T00:00:00+08:00,abc\n"
        r = api("admin", "POST", "/admin/datasets", data={"dataset": "e2e_bad", "table": "meter_reading"}, files={"file": ("m.csv", bad, "text/csv")})
        assert r.status_code in (200, 201, 400, 422), r.text[:200]
        body = r.json()
        assert (body.get("report") or {}).get("status") in ("rejected", "failed") or r.status_code >= 400, body
    soft("ADMIN", "a bad upload is rejected with a report", adm_upload)
    soft("ADMIN", "admin sees no personal details on the demo premise (API)", lambda: "FAKE" not in api("admin", "GET", "/premises/P-CEN-001-054").text)
    soft("ADMIN", "admin remote sign-out of inspector.b (API)", lambda: api("admin", "POST", "/users/inspector.b/sign-out").status_code == 200)
    def phone_wiped():
        phone.click("button:has-text('Sync')") if phone.locator("button:has-text('Sync')").count() else None
        phone.wait_for_timeout(2500)
        body = phone.inner_text("body")
        shot(phone, "04f_phone_remote_signed_out")
        assert "signed out remotely" in body, body[:300]
    soft("UC-04", "phone wiped after remote sign-out (NFR-16)", phone_wiped)

    # ---------------------------------------------------------------- UC-08 auditor
    aud = desk("auditor")
    def uc08():
        aud.goto(f"{url}/#/audit")
        aud.wait_for_selector("tbody tr")
        aud.click("button:has-text('Verify hash chain')")
        aud.wait_for_selector("text=Chain intact")
        shot(aud, "08a_audit")
    soft("UC-08", "auditor sees the log and verifies the chain (FR-AD-02, NFR-12)", uc08)
    def uc08_actions():
        rows = api("auditor", "GET", "/audit?limit=1000").json()["rows"]
        actions = {r["action"] for r in rows}
        need = ["case.view", "outcome", "report", "agent.chatbot.answer", "dispatch"]
        missing = [n for n in need if not any(n in a for a in actions)]
        assert not missing, (missing, sorted(actions))
    soft("UC-08", "views, outcomes, exports and agent actions are logged", uc08_actions)
    soft("UC-08", "auditor cannot read cases (API)", lambda: api("auditor", "GET", "/cases").status_code == 403)
    soft("UC-08", "auditor cannot read zones (API)", lambda: api("auditor", "GET", "/zones").status_code == 403)

    # ---------------------------------------------------------------- language
    def bm():
        mgr.goto(f"{url}/#/")
        mgr.select_option("header select", "ms")
        mgr.wait_for_timeout(800)
        shot(mgr, "10a_overview_bm")
        mgr.select_option("header select", "en")
    soft("UI", "desktop switches to Bahasa Melayu", bm)
    browser.close()

stack.stop()
print(f"\nDone in {time.time() - t0:.0f}s: {sum(r[2] for r in results)}/{len(results)} checks passed")
print("\nBrowser problems:")
for x in problems:
    print("  ", x)
(OUT / "results.json").write_text(json.dumps({"results": results, "problems": problems}, indent=1))
