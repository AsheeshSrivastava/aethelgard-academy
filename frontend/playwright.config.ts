import { tmpdir } from "node:os";
import { join } from "node:path";

import { defineConfig } from "@playwright/test";

const PORT = 8123;

// End-to-end tests run against the real API with no AI and a throwaway database (ADR-0014).
export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false,
  workers: 1,
  reporter: "list",
  use: {
    baseURL: `http://127.0.0.1:${PORT}`,
    channel: "chrome",
    screenshot: "only-on-failure",
  },
  webServer: {
    command: `uv run --no-sync uvicorn lms.api.app:app --port ${PORT} --log-level warning`,
    cwd: "..",
    url: `http://127.0.0.1:${PORT}/api/v1/health`,
    reuseExistingServer: false,
    timeout: 60_000,
    env: {
      MOCK_AI: "true",
      LMS_DB_PATH: join(tmpdir(), `lms-e2e-${Date.now()}.db`),
    },
  },
});
