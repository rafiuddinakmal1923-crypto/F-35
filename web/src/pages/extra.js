// Pages added by later milestones (agents, models, UI upgrade). Each entry: { to, key, roles, nav, demoOnly, Component }.
import Assistant from "./Assistant.jsx";
import Backtest from "./Backtest.jsx";
import Dispatch from "./Dispatch.jsx";
import LandlordConcept from "./LandlordConcept.jsx";
import Models from "./Models.jsx";
import Validation from "./Validation.jsx";
import Weekly from "./Weekly.jsx";

export const EXTRA_PAGES = [
  { to: "/assistant", key: "assistant", roles: ["manager", "analyst", "supervisor"], nav: true, Component: Assistant },
  { to: "/weekly", key: "weekly", roles: ["manager", "supervisor"], nav: true, Component: Weekly },
  { to: "/dispatch", key: "dispatch", roles: ["supervisor", "admin"], nav: true, Component: Dispatch },
  { to: "/models", key: "models", roles: ["manager", "data_scientist"], nav: true, Component: Models },
  { to: "/validation", key: "validation", roles: ["manager", "analyst", "data_scientist"], nav: true, Component: Validation },
  { to: "/backtest", key: "backtest", roles: ["manager", "analyst", "supervisor", "data_scientist"], nav: true, Component: Backtest },
  // Concept for R2 (UI brief 3.11): reachable by link always, in the menu only in demo mode.
  { to: "/concept/landlord", key: "concept", roles: ["manager", "analyst", "supervisor"], nav: true, demoOnly: true, Component: LandlordConcept },
];
