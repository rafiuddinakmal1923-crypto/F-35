// Light/dark theme (UI brief 1): dark "control room" by default, light for projectors and printing.
// The choice is remembered on this device and set as data-theme on <html>, which the CSS tokens follow.
import { useEffect, useState } from "react";

const KEY = "vg_theme";
const subscribers = new Set();

function stored() {
  try {
    const v = localStorage.getItem(KEY);
    return v === "light" || v === "dark" ? v : null;
  } catch {
    return null;
  }
}

let theme = stored() || "dark";

export function applyTheme() {
  if (typeof document !== "undefined") document.documentElement.dataset.theme = theme;
}

export function getTheme() {
  return theme;
}

export function setTheme(next) {
  theme = next === "light" ? "light" : "dark";
  try {
    localStorage.setItem(KEY, theme);
  } catch {
    /* storage may be blocked: the theme still applies for this visit */
  }
  applyTheme();
  subscribers.forEach((fn) => fn(theme));
}

export function useTheme() {
  const [current, setCurrent] = useState(theme);
  useEffect(() => {
    subscribers.add(setCurrent);
    return () => subscribers.delete(setCurrent);
  }, []);
  return current;
}
