# ADR 0015: Learner Identity and Sessions

- **Status:** Accepted in part (2026-10-30). Now: items 3, 4 (`local-single` only), 5, 6, 7. Deferred until the app is ready (owner decision): items 1 and 2 and `accounts` mode.
- **Decider:** Platform Architect & Owner (Asheesh Ranjan Srivastava)
- **Date:** 2026-10-30

---

## 1. Context & Problem Statement

The platform has no identity. The web UI hardcodes `default_learner` in every ledger and progress call, and `ILearnerRepository.get_learner()` returns a stub. CORS is configured with `allow_origins=["*"]` together with `allow_credentials=True`, which browsers reject for credentialed requests and which would be unsafe if they did not.

The evidence ledger is the platform's core asset (ADR-0004). Evidence attributed to the wrong learner, or to anyone who can reach the API, makes every proficiency decision meaningless. The production mandate (AGENTS.md section 1) requires real multi-tenant operation later.

---

## 2. Decision

1. **Learners are real records:** a `learners` table (`learner_id` UUID, `display_name`, `email` unique, `password_hash`, `created_at`). Passwords are hashed with `hashlib.scrypt` from the standard library (no new dependency).
2. **Server-side sessions:** a `sessions` table (`session_id` random 256-bit, `learner_id`, `created_at`, `expires_at`). The browser holds only an `HttpOnly`, `SameSite=Lax`, `Secure` (outside localhost) cookie.
3. **`/me` routes:** learner-scoped endpoints use `/api/v1/learners/me/...`. The server resolves the learner from the session; a client can never name another learner's id.
4. **Local single-learner mode:** `LMS_AUTH_MODE=local-single` (the default for development) signs every request in as one local learner, so offline development and the CLI keep working with no sign-in step. `LMS_AUTH_MODE=accounts` enables sign-in.
5. **CORS:** origins come from `LMS_ALLOWED_ORIGINS` (comma-separated). No wildcard when credentials are allowed.
6. **CLI parity:** the `lms` CLI reads the same local learner in `local-single` mode, so CLI and web evidence stay in one ledger (ADR-0006).
7. **Migration:** existing `default_learner` rows are re-keyed to the local learner's UUID once, by a one-shot migration with a dry-run flag.

**Phasing (owner decision, 2026-10-30):** sign-in is added when the app is ready. Until then the platform runs in `local-single` mode only, but every learner-scoped route already uses `/learners/me/...` and CORS already uses `LMS_ALLOWED_ORIGINS`, so turning on `accounts` later needs no frontend change and no second data migration.

Out of scope here: organisations/tenants, roles (instructor, admin), SSO. Each gets its own ADR when needed.

---

## 3. Consequences

### Positive
- Every evidence entry has a trustworthy owner.
- Development and CI keep zero setup in `local-single` mode.

### Negative / Trade-offs
- Password reset and email verification are not covered; acceptable while sign-in is local.
- Session storage adds a table and an expiry sweep.
