import React from "react";
import { createRoot } from "react-dom/client";
// Self-hosted fonts (no network needed, so the demo works offline): Space Grotesk for numbers, scores
// and headings, IBM Plex Sans for body text. Latin subsets only.
import "@fontsource/ibm-plex-sans/latin-400.css";
import "@fontsource/ibm-plex-sans/latin-500.css";
import "@fontsource/ibm-plex-sans/latin-600.css";
import "@fontsource/space-grotesk/latin-500.css";
import "@fontsource/space-grotesk/latin-600.css";
import "@fontsource/space-grotesk/latin-700.css";
import App from "./App.jsx";
import { applyTheme } from "./theme.js";
import "./styles.css";

applyTheme();
createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
