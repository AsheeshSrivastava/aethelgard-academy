/// <reference types="vitest/config" />
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// Built files go where FastAPI serves them, so `uv run` stays the only runtime (ADR-0014).
export default defineConfig({
  plugins: [react()],
  build: {
    outDir: "../src/lms/web/dist",
    emptyOutDir: true,
  },
  server: {
    port: 5173,
    proxy: {
      "/api": { target: "http://127.0.0.1:8000", ws: true },
    },
  },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: "./src/test/setup.ts",
    include: ["src/**/*.test.{ts,tsx}"],
    testTimeout: 15000, // Room for several 5 s condition waits on a busy machine

  },
});
