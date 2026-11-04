import { tmpdir } from "node:os";
import { join } from "node:path";

import { defineConfig } from "@playwright/test";

const PORT = 8123;

// Workers load this file too, so the path is fixed once and shared through the environment.
process.env.LMS_E2E_DB ??= join(tmpdir(), `lms-e2e-${process.pid}.db`);

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
      // Browser tests check the real waits, whatever a local .env says (ADR-0019 amendment).
      LMS_TEST_MODE: "false",
      LMS_DB_PATH: process.env.LMS_E2E_DB,
      // Hidden build checks (ADR-0021); unset, builds grade with their practice checks.
      ...(process.env.LMS_ANSWERS_DIR ? { LMS_ANSWERS_DIR: process.env.LMS_ANSWERS_DIR } : {}),
    },
  },
});
