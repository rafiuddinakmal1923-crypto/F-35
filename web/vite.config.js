import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// In development the API runs on :8000; in Docker the proxy serves both under one origin.
const apiProxy = { "/api": { target: process.env.VG_API || "http://localhost:8000", rewrite: (p) => p.replace(/^\/api/, "") } };
export default defineConfig({
  plugins: [react()],
  server: { port: 5173, proxy: apiProxy },
  preview: { port: 4173, proxy: apiProxy },
  build: { outDir: "dist", sourcemap: false },
});
