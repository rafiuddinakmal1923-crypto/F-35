// Concept for R2, opt-in only (UI brief 3.11): what a consent-based alert to a property owner could look
// like when a rented premise's zone is flagged. Mock only: simulated zone-level data, nothing is sent, no
// owner or tenant details are shown. The SRS keeps the landlord portal out of scope for R0.
import { BellRing, Lightbulb, ShieldCheck } from "lucide-react";
import { get } from "../api.js";
import { useLoad } from "../components/Common.jsx";
import { Panel } from "../components/ui.jsx";
import { t } from "../i18n.js";

export default function LandlordConcept() {
  const zones = useLoad(() => get("/zones?flagged_only=true"), []);
  const flagged = zones.data?.zones || [];
  const zone = flagged[0];
  return (
    <div className="page">
      <div className="concept-banner" role="note">
        <Lightbulb size={20} aria-hidden="true" />
        <span><b>{t("conceptBadge")}</b><br />{t("conceptIntro")}</span>
      </div>
      <h1>{t("conceptTitle")}</h1>
      <div className="panels">
        <Panel className="span-5" title={t("conceptPhone")} icon={BellRing} loading={zones.loading} error={zones.error}
          empty={zones.data && !zone} emptyText={t("noneFlagged")}>
          {zone ? (
            <div className="phone-mock" aria-label={t("conceptPhone")}>
              <small className="muted">VoltGuard · {t("conceptSender")}</small>
              <div className="sms">{t("conceptMessage", { district: zone.district, date: zones.data.run_date })}</div>
              <div className="row"><button type="button" disabled>{t("conceptAck")}</button><button type="button" disabled>{t("conceptStop")}</button></div>
              <small className="muted">{t("conceptNothingSent")}</small>
            </div>
          ) : null}
        </Panel>
        <Panel className="span-7" title={t("conceptRules")} icon={ShieldCheck}>
          <ul className="limits">
            {["conceptRule1", "conceptRule2", "conceptRule3", "conceptRule4", "conceptRule5"].map((k) => <li key={k}><ShieldCheck size={16} aria-hidden="true" />{t(k)}</li>)}
          </ul>
          <small className="muted">{t("conceptScope")}</small>
        </Panel>
      </div>
    </div>
  );
}
