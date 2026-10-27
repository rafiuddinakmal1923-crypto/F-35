// Pages added by later milestones (agents, models). Each entry: { to, key, roles, nav, Component }.
import Assistant from "./Assistant.jsx";
import Dispatch from "./Dispatch.jsx";
import Weekly from "./Weekly.jsx";
import Models from "./Models.jsx";

export const EXTRA_PAGES = [
  { to: "/assistant", key: "assistant", roles: ["manager", "analyst", "supervisor"], nav: true, Component: Assistant },
  { to: "/weekly", key: "weekly", roles: ["manager", "supervisor"], nav: true, Component: Weekly },
  { to: "/dispatch", key: "dispatch", roles: ["supervisor", "admin"], nav: true, Component: Dispatch },
  { to: "/models", key: "models", roles: ["manager", "data_scientist"], nav: true, Component: Models },
];
