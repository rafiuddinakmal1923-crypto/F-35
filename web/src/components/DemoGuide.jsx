// Guided demo (UI brief 3.8; DEMO_MODE only): a floating panel that walks through the 7 live steps of
// SDD 10.5. Each step has a one-line narration, a button that signs in as the right test account and opens
// the right page, and a check mark once the API reports its pass criterion met.
import { CheckCircle2, Compass, Play, RotateCcw, X } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { get, pollJob, post, session, signInDemo } from "../api.js";
import { t } from "../i18n.js";

function fill(page, s) {
  if (page.includes("{case}") && !s.case) return "/cases";
  if (page.includes("{premise}") && !s.premise) return `/zones/${s.zone}`;
  return page.replace("{zone}", s.zone).replace("{premise}", s.premise || "").replace("{case}", s.case || "");
}

export default function DemoGuide() {
  const [open, setOpen] = useState(() => { try { return sessionStorage.getItem("vg_guide") === "open"; } catch { return false; } });
  const [status, setStatus] = useState(null);
  const [busy, setBusy] = useState(null);
  const [error, setError] = useState(null);
  const navigate = useNavigate();
  const { user } = session();

  const load = useCallback(() => get("/demo/status").then(setStatus).catch(() => {}), []);
  useEffect(() => {
    load();
    const timer = setInterval(load, open ? 5000 : 30000);
    return () => clearInterval(timer);
  }, [load, open, user?.user_id]);
  useEffect(() => { try { sessionStorage.setItem("vg_guide", open ? "open" : "closed"); } catch { /* blocked */ } }, [open]);

  async function go(step) {
    setError(null);
    setBusy(step.step);
    try {
      if (step.role === "inspector") {
        navigate(`/field?demo=${encodeURIComponent(step.user)}`);
        return;
      }
      let s = status;
      if (session().user?.user_id !== step.user) {
        await signInDemo(step.user);
        s = await get("/demo/status");
        setStatus(s);
      }
      navigate(fill(step.page, s));
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(null);
    }
  }

  async function reset() {
    setError(null);
    setBusy("reset");
    try {
      const started = await post("/admin/demo/reset");
      const job = await pollJob(started.job_id, () => {}, 1000);
      if (job.status !== "done") throw new Error(job.error?.split("\n")[0] || t("jobFailed"));
      await load();
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(null);
    }
  }

  const steps = status?.steps || [];
  const done = steps.filter((s) => s.done).length;
  const next = steps.find((s) => !s.done)?.step;
  return (
    <>
      <button type="button" className="primary demo-guide-btn" onClick={() => setOpen((v) => !v)} aria-expanded={open} aria-controls="demo-guide">
        <Compass size={18} aria-hidden="true" />{t("demoGuide")} {steps.length ? `${done}/${steps.length}` : ""}
      </button>
      {open ? (
        <section id="demo-guide" className="demo-guide" aria-label={t("demoGuide")}>
          <div className="row between">
            <h2>{t("demoGuide")}</h2>
            <button type="button" className="icon-btn" onClick={() => setOpen(false)} aria-label={t("close")}><X size={16} /></button>
          </div>
          <small className="muted">{t("demoGuideIntro")}</small>
          <ol className="guide-steps">
            {steps.map((s) => (
              <li key={s.step} className={`guide-step ${s.done ? "done" : s.step === next ? "next" : ""}`}>
                <span className="n" aria-hidden="true">{s.done ? <CheckCircle2 size={16} /> : s.step}</span>
                <div>
                  <b>{t(`guide${s.step}Title`)}</b>
                  <p>{t(`guide${s.step}Say`)}</p>
                  <small className="muted">{t("guidePass")}: {t(`guide${s.step}Pass`)}</small>
                  <div className="row" style={{ marginTop: 6 }}>
                    <button type="button" className={s.step === next ? "primary" : ""} onClick={() => go(s)} disabled={busy != null}>
                      <Play size={14} aria-hidden="true" />{t("guideGo", { who: s.user })}
                    </button>
                    <span className={`pill ${s.done ? "ok" : "neutral"}`}>{s.done ? t("guideDone") : t("guideNotYet")}</span>
                  </div>
                </div>
              </li>
            ))}
          </ol>
          {user?.role === "admin" ? (
            <button type="button" onClick={reset} disabled={busy != null}><RotateCcw size={15} aria-hidden="true" />{busy === "reset" ? t("resetting") : t("resetDemo")}</button>
          ) : <small className="muted">{t("resetHint")}</small>}
          {error ? <div className="notice error" role="alert">{error}</div> : null}
        </section>
      ) : null}
    </>
  );
}
