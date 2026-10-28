// Reason waterfall (UI brief 3.3): each reason's contribution as a step from the running total,
// legitimate-use penalties as negative bars, "other" and "capped" lines, ending exactly at the score.
// The pattern-model bar expands on click to its SHAP sub-reasons. Every bar has a plain-language label.
import { ChevronDown, ChevronRight } from "lucide-react";
import { useState } from "react";
import { t } from "../i18n.js";
import { barStyle, at, shapRows, waterfall } from "../lib/waterfall.js";
import { reasonLabel } from "./Common.jsx";

const SHAP_KEY = {
  cv: "shap_cv", min_ratio: "shap_min_ratio", max_ratio: "shap_max_ratio", zero_day_share: "shap_zero_day_share", trend: "shap_trend",
  half_ratio: "shap_half_ratio", max_drop: "shap_max_drop", weekly_autocorr: "shap_weekly_autocorr", low_day_share: "shap_low_day_share",
  last_first_week_ratio: "shap_last_first_week_ratio", level_vs_peers: "shap_level_vs_peers",
  shape: "shap_shape", level_kwh: "shap_level_kwh",
};

function Row({ label, pts, kind, style, zero, onToggle, open, sub }) {
  const content = (
    <>
      <span className="wf-label">
        {onToggle ? (open ? <ChevronDown size={14} aria-hidden="true" /> : <ChevronRight size={14} aria-hidden="true" />) : null}
        <span>{label}</span>
      </span>
      <span className="wf-track" aria-hidden="true"><span className="zero" style={{ left: `${zero}%` }} /><span className={`wf-bar ${kind}`} style={style} /></span>
      <span className={`wf-pts ${kind === "neg" ? "neg" : kind === "adj" ? "adj" : ""}`}>{pts}</span>
    </>
  );
  if (onToggle) {
    return <button type="button" className={`wf-row ${sub ? "sub" : ""}`} onClick={onToggle} aria-expanded={open}>{content}</button>;
  }
  return <div className={`wf-row ${sub ? "sub" : ""} ${kind === "total" ? "total-row" : ""}`}>{content}</div>;
}

export default function Waterfall({ reasons, score, shap }) {
  const [open, setOpen] = useState(false);
  if (!reasons?.length) return <p className="muted">{t("noReasons")}</p>;
  const wf = waterfall(reasons, score);
  const zero = at(0, wf);
  const subs = shapRows(shap);
  const signed = (v) => `${v > 0 ? "+" : ""}${v.toFixed(1)}`;
  const summary = t("waterfallSummary", { score, lines: wf.rows.map((r) => `${reasonLabel(r)} ${signed(r.contribution)}`).join("; ") });
  return (
    <div className="waterfall" role="group" aria-label={t("reasonWaterfall")}>
      <p className="sr-only">{summary}</p>
      {wf.rows.map((r, i) => {
        const expandable = r.feature === "pattern_model" && subs.length > 0;
        return (
          <div key={i}>
            <Row label={reasonLabel(r)} pts={signed(r.contribution)} kind={r.kind} style={barStyle(r, wf)} zero={zero}
              onToggle={expandable ? () => setOpen((v) => !v) : undefined} open={open} />
            {expandable && open ? subs.map((s) => (
              <Row key={s.feature} sub kind={`shap ${s.positive ? "" : "neg"}`} zero={0}
                label={`${s.positive ? t("shapRaises") : t("shapLowers")}: ${SHAP_KEY[s.feature] ? t(SHAP_KEY[s.feature]) : s.text}`}
                pts={s.shap.toFixed(2)} style={{ left: 0, width: `${Math.max(s.share * 100, 2)}%` }} />
            )) : null}
          </div>
        );
      })}
      <Row label={t("riskScore")} pts={String(score)} kind="total" zero={zero} style={barStyle({ start: 0, end: score }, wf)} />
      <small>{wf.exact ? t("waterfallExact", { score }) : t("waterfallRounding")}{subs.length ? ` ${t("shapHint")}` : ""}</small>
    </div>
  );
}
