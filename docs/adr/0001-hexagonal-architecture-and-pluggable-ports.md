# ADR 0001: Hexagonal Architecture and Pluggable Boundary Ports

- **Status:** Accepted
- **Decider:** Lead Educational Engineer & Systems Architect (Asheesh Ranjan Srivastava)
- **Date:** 2026-10-29

---

## 1. Context & Problem Statement

The platform must combine deterministic Python learning, sandboxed code execution, learner progress tracking, and AI tutoring (AXIS AI). 

If domain logic (lesson sequencing, evidence evaluation) directly imports third-party database drivers (e.g., SQLite, PostgreSQL) or vendor-specific AI SDKs (e.g., OpenAI, Anthropic, Gemini):
1. Automated unit testing becomes slow, expensive, and dependent on network connectivity.
2. The platform becomes tightly coupled to specific vendors.
3. Upgrading or changing infrastructure components requires refactoring core pedagogical logic.

---

## 2. Decision

We adopt **Hexagonal Architecture (Ports and Adapters)**:
1. **Core Domain Isolation:** `src/lms/core/` contains pure domain entities, models, and progression rules with zero third-party I/O dependencies.
2. **Abstract Protocols (Ports):** Defined in `src/lms/core/interfaces.py`:
   - `ILearnerRepository`: State & evidence persistence.
   - `ICodeRunner`: Sandboxed execution & assertion verification.
   - `IAXISCompanion`: AI pedagogical dialogue.
3. **Interchangeable Adapters:** Located in `src/lms/adapters/`:
   - Database: `sqlite_repo.py` today $\rightarrow$ `postgres_repo.py` tomorrow.
   - AI Companion: `mock_axis.py` (`MOCK_AI=true`) for instant, offline zero-token tests $\rightarrow$ Cloud frontier LLMs in production.

---

## 3. Consequences

### Positive
- **Zero API Spend in Development/Testing:** Entire test suites run in under 0.2s completely offline.
- **Independent Swappability:** Any external dependency (database, container runner, LLM provider) can be swapped without touching a single line of curriculum or progression logic.
- **High Testability:** Fast, deterministic testing of business logic via mock adapters.

### Trade-offs / Mitigations
- Requires maintaining protocol definitions and adapter translation layers (Pydantic models). Mitigated by Python's `typing.Protocol` and strict type hints.
