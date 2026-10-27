// Pages added by later milestones (agents, models). Each entry: { to, key, roles, nav, Component }.
import Assistant from "./Assistant.jsx";

export const EXTRA_PAGES = [
  { to: "/assistant", key: "assistant", roles: ["manager", "analyst", "supervisor"], nav: true, Component: Assistant },
];
