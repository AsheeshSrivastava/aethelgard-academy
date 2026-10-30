# ADR 0014: React + TypeScript + Vite Learner Frontend

- **Status:** Accepted
- **Decider:** Platform Architect & Owner (Asheesh Ranjan Srivastava)
- **Date:** 2026-10-30
- **Supersedes:** ADR-0013, section 1 (zero-build single-page shell). ADR-0013's pedagogical decisions (activity sequence, concept library, Zed bridge) stay in force, updated by section 2 below.

---

## 1. Context & Problem Statement

ADR-0013 built the learner UI as a zero-build vanilla JS shell (`src/lms/web/`). The approved redesign (design canvas, 2026-10-30) asks for much more client state than that shell can hold safely:

- A lesson page with a step rail (Video, Explain, then the unit's own activities), a live code editor, an interactive terminal that pauses at `input()`, and Regenerate on every activity except Explain.
- An AXIS panel shared by every page that streams replies and reacts to the last run.
- A stage build page with several files, live requirement checks and a submission flow.
- A My progress page driven by proficiency data.

Untyped `fetch` calls in one 39 KB `app.js` already drift from the API (for example, web Verify posts `status: "Completed"` and records no evidence). The redesign would multiply that risk.

---

## 2. Decision

1. **Stack:** React 19 + TypeScript (strict) in a new `frontend/` folder at the repo root, built with Vite.
2. **Runtime stays Python-only:** `npm run build` writes to `src/lms/web/dist/`. The built files are committed. FastAPI serves `dist/` at `/` with an SPA fallback, so `uv run` remains the only command a learner or operator needs. Node is a development dependency of the frontend only.
3. **Typed contract:** TypeScript types are generated from FastAPI's `/openapi.json` (`openapi-typescript`). A backend contract change fails the frontend type check before it reaches learners. SPEC-12 is the contract.
4. **Libraries:** TanStack Router (typed routes), TanStack Query (server state), CodeMirror 6 (editor), xterm.js (terminal over the run WebSocket), native `EventSource`/fetch streaming for AXIS. No UI kit; design tokens are CSS variables taken from the canvas (teal `#0B6E6E`, IBM Plex Sans, JetBrains Mono), with light and dark themes.
5. **Routes (information architecture):**
   `/` front page → `/courses` → `/courses/:courseId` (course map) → `/units/:unitId` (unit map) → `/units/:unitId/:step` (lesson) · `/courses/:courseId/stages/:stage/build` · `/progress`. Every page below the front page has a back link to its parent.
6. **Feature modules for later additions:** live sessions (Google Meet), forums and gamification are planned. Each arrives as its own route group under `frontend/src/features/<name>/`, behind a feature flag served by `GET /api/v1/features`, with its own backend router and tables. Rules that keep them from disturbing the learning core:
   - Live sessions sit behind an `ILiveSessionProvider` port (Google Meet first), like `IAXISCompanion`; Google sign-in gets its own ADR.
   - Forums need real accounts (ADR-0015, `accounts` mode).
   - Gamification only *reads*: it subscribes to an `evidence.recorded` domain event emitted after each ledger append. Points, streaks and badges are display only and never feed `ProficiencyView` or progression decisions (ADR-0016), so the evidence stays honest and assessment stays invisible.
   - Lesson content and scenarios are data from `curriculum/` packages and roadmaps, never hardcoded in the frontend.
7. **Testing:** Vitest + Testing Library for components; Playwright end-to-end tests against the real API with `MOCK_AI=true`, so CI stays offline and zero-cost (AGENTS.md section 5).

---

## 3. Consequences

### Positive
- API drift becomes a build error, not a learner-facing bug.
- The lesson page's state (steps, exercise variants, terminal session, drafts) has a maintainable home.
- Running the platform still needs no Node, preserving the spirit of ADR-0013.

### Negative / Trade-offs
- Frontend contributors need Node and npm.
- Committed build output must be rebuilt with every frontend change; a check in CI compares `dist/` against a fresh build.
- `src/lms/web/` (current shell) is retired once the new frontend reaches parity.
