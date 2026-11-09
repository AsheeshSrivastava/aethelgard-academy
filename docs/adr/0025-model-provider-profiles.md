# ADR 0025: Model Provider Profiles and a Settings Page

- **Status:** Accepted (2026-11-04) by the owner. Built (SPEC-17, Model settings page).
- **Decider:** Platform Architect & Owner (Asheesh Ranjan Srivastava)
- **Date:** 2026-11-04
- **Governed by:** ADR-0003 (AXIS answers only from our curriculum), ADR-0010 (local-first AI), `IAXISCompanion` (provider-agnostic port), AGENTS.md ("never print keys", "no paid run without a cost estimate")

---

## 1. Context & Problem Statement

AXIS talks to one OpenAI-compatible server set in `.env` (`LOCAL_LLM_BASE_URL`, `LOCAL_LLM_MODEL`, `LOCAL_LLM_API_KEY`); `MOCK_AI=true` turns it off. Changing provider means editing `.env` and restarting. The owner wants to pick a provider in the app: OpenAI, Gemini, or a local model.

---

## 2. Proposed decision

1. **Provider profiles.** A profile is a name, a kind, a base URL, a model and the name of the environment variable holding its key. Two adapters, both behind `IAXISCompanion`; nothing else in the app knows which is in use:
   - **OpenAI-SDK adapter** with a configurable address. It serves local models (any OpenAI-compatible server: Unsloth, Ollama, LM Studio) and OpenAI itself. Local and OpenAI are two profiles of one adapter, not two adapters.
   - **Gemini adapter** using Google's own SDK, not Gemini's OpenAI-compatible address.
2. **A Settings page** lists the profiles, shows which is active and whether its key is present ("key set: yes/no"), and lets the owner switch, then tests the connection with one short call.
3. **Keys stay on the server.** Keys live only in `.env` (git-ignored) or the operating system's key store. They are never sent to the browser, never stored in the database, never written to logs, and the Settings page never displays them. The page may accept a new key once and write it to the key store, but cannot read one back.
4. **The provenance firewall does not change.** Whatever the provider, AXIS answers only from our curriculum (ADR-0003) and keeps the Socratic boundary (ADR-0009). Tests and CI still run with `MOCK_AI=true` and no keys.
5. **Paid providers are off by default.** Choosing a paid profile shows the estimated cost per question and needs the owner's confirmation; a monthly spending cap stops calls when reached.

---

## 3. Consequences

- **Privacy:** with a cloud provider, the learner's code and questions leave the machine. The Settings page must say so. Before a second learner, this needs their consent (ADR-0022 section 2.6).
- **Cost:** every AXIS question to a cloud provider costs money; the cap and estimate make that visible.
- **Results differ by model.** The Socratic guardrail and the grounding checks run after every model, so a weaker model gives weaker help, never an answer.

## 4. Owner decisions

Decided 2026-11-04:
- **Keys stay in `.env`** for now. No key store, and the Settings page does not accept keys yet.
- **Gemini gets its own adapter**, using Google's SDK, not the OpenAI-compatible address.
- **Local models and OpenAI share one OpenAI-SDK adapter** with a configurable address.
- **AXIS rules are identical across providers**: same prompt, same Socratic guardrail, same grounding checks.
- **Which Gemini model answers on the free API** is checked when this is built, by a real test call, never assumed; the Settings page's connection test shows the model that answered.
- The work runs in its own thread (work sequence, phase 2c).

Decided 2026-11-04 (second round):
- **Build all three in this phase:** local, Gemini and OpenAI.
- **Monthly spending cap: US$5.** When reached, AXIS stops calling paid providers until the next calendar month.
- **Gemini counts as paid**, like OpenAI, even on the free tier: it needs the confirmation and counts toward the cap.
- **Token counts are recorded**: input and output tokens per session, by model, so the owner can compare cost and answer quality across providers. Only the counts the provider reports are stored, never the prompt or reply text in this table. When a provider reports no counts (some local servers), the row says "not reported" rather than guessing.
