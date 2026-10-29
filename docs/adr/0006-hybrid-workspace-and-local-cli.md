# ADR 0006: Hybrid Learner Workspace: Local CLI with Zed / VS Code + Cloud Sandbox Fallback

- **Status:** Accepted
- **Decider:** Lead Educational Engineer & Systems Architect (Asheesh Ranjan Srivastava)
- **Date:** 2026-10-30

---

## 1. Context & Problem Statement

Traditional online programming platforms isolate learners inside embedded browser editors. When learners transition to real-world development, they encounter severe friction managing local interpreters, virtual environments, dependency managers, and terminal tooling.

Conversely, forcing complete beginners to solve operating system PATH and interpreter configuration issues on Day 1 causes immediate cognitive fatigue and dropout.

The platform requires an onboarding model that:
1. Provides zero-friction instant code execution on Day 1.
2. Transitions learners to configuring and owning their real developer environment on their local machine.
3. Supports modern high-performance editors (specifically **Zed** and **VS Code**).

---

## 2. Decision

We adopt a **Graduated Hybrid Workspace Architecture**:

1. **Phase 1 (Zero-Friction Entry):**  
   New learners can execute foundational exercises in the browser-backed cloud sandbox (powered by `SubprocessRunner` / `DockerRunner`).
2. **Phase 2 (Local Workspace Ownership):**  
   Learners initialize a real developer workspace on their local workstation powered by:
   - **`uv`:** Fast, single-binary Python and virtualenv management via `pyproject.toml`.
   - **Editor Choice:** First-class documentation and settings templates for **Zed** (high-performance, Rust-native, built-in LSP) and **VS Code**.
   - **LMS CLI (`lms`):** A lightweight local CLI providing:
     - `lms pull <unit_id>`: Pulls exercise starter files, carried-forward data context, and tests.
     - `lms verify`: Runs deterministic local tests via `pytest` and transmits observable telemetry into the platform's **Evidence Ledger**.

---

## 3. Consequences

### Positive
- **Authentic Engineering Mastery:** Learners develop tactile confidence in real terminals, git workflows, package managers (`uv`), and modern IDEs (Zed / VS Code).
- **FinOps & Compute Scaling:** Offloads repetitive test execution compute from platform servers to the learner's workstation.
- **Offline Capable:** Learners can study and write code on transit or in intermittent connectivity environments, syncing progress when back online.

### Trade-offs / Mitigations
- Requires maintaining the `lms` CLI tool and local starter templates. Mitigated by packaging the CLI directly within the existing `lms` Python package.
