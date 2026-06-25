import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "node:path";

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  // GitHub Pages serves the site at https://<user>.github.io/<repo>/
  base: process.env.VITE_BASE_PATH || "/UAQI-Project/",
  server: {
    port: 5173,
    host: true,
    proxy: {
      "/api": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },
    },
  },
  build: {
    // Put built assets in dist/ at the repo root, ready for GitHub Pages
    outDir: "dist",
    sourcemap: false,
    chunkSizeWarningLimit: 1500,
  },
});