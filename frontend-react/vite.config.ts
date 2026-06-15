import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

// base '/static/' khi BUILD (FastAPI mount dist ở /static); '/' khi DEV. Proxy /api -> :8000.
export default defineConfig(({ command }) => ({
  base: command === "build" ? "/static/" : "/",
  plugins: [react()],
  resolve: { alias: { "@": path.resolve(__dirname, "src") } },
  build: { outDir: "dist", emptyOutDir: true },
  server: {
    port: 5173,
    proxy: {
      "/api": { target: "http://localhost:8000", changeOrigin: true },
      "/shared": { target: "http://localhost:8000", changeOrigin: true },
    },
  },
}));
