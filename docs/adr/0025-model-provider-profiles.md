# ADR 0025: Model Provider Profiles and a Settings Page

- **Status:** Proposed (2026-11-04), not built. Needs the owner's decisions in section 4.
- **Decider:** Platform Architect & Owner (Asheesh Ranjan Srivastava)
- **Date:** 2026-11-04
- **Governed by:** ADR-0003 (AXIS answers only from our curriculum), ADR-0010 (local-first AI), `IAXISCompanion` (provider-agnostic port), AGENTS.md ("never print keys", "no paid run without a cost estimate")

---

## 1. Context & Problem Statement

AXIS talks to one OpenAI-compatible server set in `.env` (`LOCAL_LLM_BASE_URL`, `LOCAL_LLM_MODEL`, `LOCAL_LLM_API_KEY`); `MOCK_AI=true` turns it off. Changing provider means editing `.env` and restarting. The owner wants to pick a provider in the app: OpenAI, Gemini, or a local model.

---

## 2. Proposed decision

1. **Provider profiles.** A profile is a name, a kind, a base URL, a model and the name of the environment variable holding its key. Kinds: `local` (any OpenAI-compatible server: Ollama, LM Studio, Unsloth), `openai` (OpenAI SDK), `gemini` (Google's SDK, or its OpenAI-compatible endpoint). Each kind is one adapter behind `IAXISCompanion`; nothing else in the app knows which is in use.
2. **A Settings page** lists the profiles, shows which is active and whether its key is present ("key set: yes/no"), and lets the owner switch, then tests the connection with one short call.
3. **Keys stay on the server.** Keys live only in `.env` (git-ignored) or the operating system's key store. They are never sent to the browser, never stored in the database, never written to logs, and the Settings page never displays them. The page may accept a new key once and write it to the key store, but cannot read one back.
4. **The provenance firewall does not change.** Whatever the provider, AXIS answers only from our curriculum (ADR-0003) and keeps the Socratic boundary (ADR-0009). Tests and CI still run with `MOCK_AI=true` and no keys.
5. **Paid providers are off by default.** Choosing a paid profile shows the estimated cost per question and needs the owner's confirmation; a monthly spending cap stops calls when reached.

---

## 3. Consequences

- **Privacy:** with a cloud provider, the learner's code and questions leave the machine. The Settings page must say so. Before a second learner, this needs their consent (ADR-0022 section 2.6).
- **Cost:** every AXIS question to a cloud provider costs money; the cap and estimate make that visible.
- **Results differ by model.** The Socratic guardrail and the grounding checks run after every model, so a weaker model gives weaker help, never an answer.

## 4. Owner decisions needed

1. Which providers to build first (suggested: local and OpenAI-compatible first, since OpenAI, Gemini and most local servers accept the same API; real SDKs only where needed).
2. Keys in `.env` only, or also the OS key store via the Settings page.
3. The monthly spending cap.
