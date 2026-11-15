# CLAUDE.md

Project rules, purpose and workflow live in AGENTS.md (loaded below).
@AGENTS.md

## Stack
- Backend: Python 3.14, FastAPI, managed with uv (src/lms, tests/).
- Frontend: React + TypeScript + Vite (frontend/).

## Checks (run from the repo root)
- Backend tests:     uv run pytest -q
- Backend lint:      uv run ruff check
- Frontend types:    cd frontend && npm run typecheck
- Frontend tests:    cd frontend && npm test

## Order
Decision, ADR, spec, tests, code. Name the ADR and spec section before
writing a test or code (see Build order in AGENTS.md).

## Done means shown
Run every check that covers your change and paste the output
before saying a change is done. If a check fails, say so.

## Review
- Every change goes in through a GitHub PR to main; CI must pass. The owner merges.
- Before opening a PR: /code-review, then /security-review. At most 3 review rounds.
- REVIEW.md says what counts as a real problem in this repo.
