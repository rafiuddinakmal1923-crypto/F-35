// My work (role home): what this person should act on next, each item linking to where the action is.
import { CircleCheck, ClipboardList, FileCheck, Send, TriangleAlert, Users } from "lucide-react";
import { Link } from "react-router-dom";
import { get, session } from "../api.js";
import { ErrorBox, useLoad } from "../components/Common.jsx";
import { t } from "../i18n.js";

const ICON = { report: FileCheck, case: ClipboardList, dispatch: Send, team: Users, alert: TriangleAlert };
const GREETING = {
  analyst: "Cases to claim, your open cases and reports waiting for your approval.",
  supervisor: "Dispatch suggestions to approve, overdue visits and teams on duty.",
  manager: "Exports waiting for your second approval and open alerts. The network picture is on the overview.",
};

export default function Work() {
  const { user } = session();
  const work = useLoad(() => get("/work"), [], 30000);
  const w = work.data;
  return (
    <div className="stack">
      <div>
        <h1>{t("work")}</h1>
        <small className="muted">{GREETING[user?.role]}</small>
      </div>
      <ErrorBox error={work.error} />
      {w ? (
        <div className="work-grid">
          {w.sections.map((s) => (
            <section key={s.key} className={`card work-card ${s.items.some((i) => i.urgent) ? "urgent" : ""}`}>
              <div className="row" style={{ justifyContent: "space-between" }}>
                <h2>{s.title}</h2><span className={`count-pill ${s.items.some((i) => i.urgent) ? "risk" : ""}`}>{s.items.length}</span>
              </div>
              {s.items.length ? (
                <ul className="work-list">
                  {s.items.map((i) => {
                    const Icon = ICON[i.kind] || ClipboardList;
                    return (
                      <li key={`${i.kind}-${i.title}`}>
                        <Link to={i.link}><Icon size={16} aria-hidden="true" /><span><b>{i.title}</b><small>{i.detail}</small></span></Link>
                      </li>
                    );
                  })}
                </ul>
              ) : <p className="empty"><CircleCheck size={16} aria-hidden="true" /> Nothing waiting.</p>}
            </section>
          ))}
        </div>
      ) : null}
    </div>
  );
}
