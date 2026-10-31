# Aethelgard frontend

React 19, TypeScript and Vite (ADR-0014). The built files go to `src/lms/web/dist/`, are committed, and FastAPI serves them at `/`, so running the platform needs no Node.

## Run it

From the repository root, with no Node needed:

```bash
uv run lms serve
```

To work on the frontend with live reload, run the API on port 8000 and, in this folder:

```bash
npm install
npm run dev
```

Then open http://localhost:5173.

## Where things are

- `src/pages/`: one file per route. `Lesson.tsx` holds the step rail, steps and Cold Check flow.
- `src/lesson/`: item forms for every SPEC-13 item type, the editor, the terminal and the AXIS panel. The editor and terminal load only on lesson pages. `wikiLinks.ts` turns `[[slug]]` into concept links (SPEC-14).
- `e2e/`: browser tests. The 24-hour wait is simulated by moving a timestamp in the throwaway test database, so the app has no test backdoor.

## Commands

| Command | What it does |
| --- | --- |
| `npm run types` | Regenerates `src/api/schema.d.ts` from the API. Run it after any API change. |
| `npm run typecheck` | Checks types. A contract change fails here before it reaches a learner. |
| `npm test` | Component tests with Vitest. |
| `npm run build` | Typechecks, then builds into `src/lms/web/dist/`. Commit the result. |
| `npm run e2e` | Browser tests against the real API, with `MOCK_AI=true` and a throwaway database. Run `npm run build` first. It uses your installed Chrome. |
