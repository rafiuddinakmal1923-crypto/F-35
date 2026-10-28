// Solar check (FR-PS-10; Solar brief 4): each check on one line with its number and a mark (supports solar,
// points to hidden use, not seen, no data), then the verdict. Facts come from the API (`solar_check`), which
// reads the scoring run's own evidence; the wording lives in lib/solar.js. Marks pair an icon with a word,
// never colour alone.
import { CircleAlert, CircleCheck, CircleDashed, CircleMinus, Info } from "lucide-react";
import { t } from "../i18n.js";
import { checkValue, stillSuspect, verdictText } from "../lib/solar.js";

const MARK = {
  pass: { Icon: CircleCheck, cls: "ok" },
  against: { Icon: CircleAlert, cls: "warn" },
  not_seen: { Icon: CircleMinus, cls: "" },
  no_data: { Icon: CircleDashed, cls: "muted" },
};

export default function SolarCheck({ check }) {
  if (!check) return null;
  return (
    <div className="stack" style={{ gap: 8 }}>
      <small className="muted">{t("solarCheckIntro")}</small>
      <ul className="solar-checks">
        {check.checks.map((c) => {
          const { Icon, cls } = MARK[c.status] || MARK.no_data;
          return (
            <li key={c.check} className={cls}>
              <Icon size={16} aria-hidden="true" />
              <span><b>{t(`solarCheckName_${c.check}`)}</b>: {checkValue(c)} <small className="mark">({t(`solarMark_${c.status}`)})</small></span>
            </li>
          );
        })}
      </ul>
      <div className={`notice ${stillSuspect(check) ? "warn" : "ok"}`} role="status"><span><b>{verdictText(check)}</b></span></div>
      {check.follow_up === "unregistered_export" ? <div className="notice"><Info size={16} aria-hidden="true" /><span>{t("solarFollowUp")}</span></div> : null}
    </div>
  );
}
