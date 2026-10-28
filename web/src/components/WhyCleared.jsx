// "Why cleared" (UI brief 3.5): for homes with a legitimate explanation (rooftop solar, EV charging,
// metered mining, vacancy), why they were not ranked high. Facts come from the scoring run itself.
import { BatteryCharging, Cpu, DoorOpen, Sun } from "lucide-react";
import { t } from "../i18n.js";

const ICON = { solar: Sun, ev_charging: BatteryCharging, metered_mining: Cpu, vacancy: DoorOpen };
const pc = (v) => (v == null ? "–" : `${Math.round(Math.abs(v) * 100)}%`);
// A home that exports at midday reads below zero, so its daytime drop can pass 100%: say so instead.
const dropPc = (v) => (v != null && v > 1.005 ? t("dropNetExport") : pc(v));

export function clearedText(item) {
  const f = item.facts || {};
  if (item.kind === "solar") {
    const parts = [];
    if (f.night_basis || (f.day_drop != null && f.night_drop != null)) parts.push(t("whySolarDay", { day: dropPc(f.day_drop), night: pc(f.night_drop) }));
    if (f.sun_corr != null && f.sun_corr <= -0.2) parts.push(t("whySolarSun"));
    else if (f.shape_corr != null && f.shape_corr >= 0.7) parts.push(t("whySolarShape"));
    if (f.export) parts.push(t("whySolarExport"));
    parts.push(f.registered_on ? t("whySolarRegistered", { date: f.registered_on }) : t("whySolarUnregistered"));
    return parts.join(" ");
  }
  if (item.kind === "ev_charging") return t("whyEv", { share: pc(f.ev_night_share) });
  if (item.kind === "metered_mining") return t("whyMining", { above: pc(f.above_similar_share) });
  if (item.kind === "vacancy") return t("whyVacancy");
  return "";
}

export default function WhyCleared({ items }) {
  if (!items?.length) return null;
  return (
    <div className="stack" style={{ gap: 8 }}>
      {items.map((item) => {
        const Icon = ICON[item.kind] || Sun;
        return (
          <div key={item.kind} className="notice ok">
            <Icon size={18} aria-hidden="true" />
            <span><b>{t(`cleared_${item.kind}`)}</b><br />{clearedText(item)}</span>
          </div>
        );
      })}
      <small className="muted">{t("whyNote")}</small>
    </div>
  );
}
