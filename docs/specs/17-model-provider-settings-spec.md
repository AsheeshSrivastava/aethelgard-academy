# SPEC-17: Model Provider Profiles, Token Counts and the Settings Page

- **Status:** Approved by the owner (2026-11-04). A session is one server run; switches within a session are counted per provider and model.
- **Governed by:** ADR-0025 (accepted 2026-11-04), ADR-0003 (provenance firewall), ADR-0009 (Socratic boundary), ADR-0010 (local-first AI), SPEC-08 (local LLM companion), AGENTS.md ("never print keys", "no paid run without a cost estimate")

---

## 1. Purpose

The owner picks which model answers AXIS from a Settings page: a local model, OpenAI or Gemini. The app records how many tokens each model used, so the owner can compare cost and answer quality, and it stops paid calls at a monthly cap of US$5.

## 2. Profiles

### 2.1 The profiles file

Profiles live in `config/providers.yaml` (committed; it holds no keys). Each profile has:

| Field | Meaning |
| :--- | :--- |
| `id` | Short name, unique, e.g. `local`, `openai`, `gemini` |
| `label` | Shown on the page |
| `kind` | `openai_compatible` or `gemini` |
| `base_url` | Address for `openai_compatible`; ignored for `gemini` |
| `model` | Model id, or `auto` (ask the server, `openai_compatible` only) |
| `key_env` | Name of the `.env` variable holding the key, e.g. `OPENAI_API_KEY`. Never the key itself |
| `paid` | `true` or `false` |
| `price_per_million` | `{input: <US$>, output: <US$>}`, required when `paid` is true |

The first version ships three profiles: `local` (Unsloth address from today's `.env`, free), `openai` (paid), `gemini` (paid, per the owner's decision, even on the free tier).

The loader rejects a file with: a duplicate `id`, an unknown `kind`, a paid profile without prices, a negative price, or a `key_env` that looks like a key rather than a variable name (anything not matching `^[A-Z][A-Z0-9_]*$`). A rejected file is an error at start, not a silent fallback.

### 2.2 The active profile

The active profile id is stored in the database (`model_settings` table, one row). With no row, the active profile is `local`. `MOCK_AI=true` still wins over everything: the app then uses the mock and the page says "Mock mode: no model is called".

## 3. Adapters

Two adapters behind `IAXISCompanion`. The port does not change.

1. **`OpenAICompatibleCompanion`** uses the official `openai` Python SDK with the profile's `base_url`. It serves `local` and `openai`. It keeps today's behaviour from SPEC-08: `auto` model discovery, `reasoning_content` handling, mock fallback for local only.
2. **`GeminiCompanion`** uses Google's `google-genai` SDK.

### 3.1 Same AXIS rules for every provider

The system prompt, the grounding passages, the Socratic guardrail, the assistance classifier and the input limits come from one shared module, used by both adapters. A test runs the same query through both adapters (with fake SDK clients) and checks they send the same system prompt and apply the same guardrail.

### 3.2 Which model answered

Each reply records the model id the provider reports in its response (OpenAI: `response.model`; Gemini: `response.model_version`), not the id we asked for. This is how the page shows which Gemini model really answers on the free API.

### 3.3 Fallback

A failing `local` call falls back to the mock, as today. A failing paid call does **not** fall back to another paid provider; it shows "AXIS is unavailable right now" and the reason class (never the key, never the raw provider message if it could echo a key).

### 3.4 Local models think off (owner request 2026-11-04)

Every local model runs with thinking off, in two layers:

1. The `local` profile sets `disable_thinking: true`. Each request then carries `chat_template_kwargs: {"enable_thinking": false}`, which llama.cpp (Unsloth Studio), vLLM and SGLang pass to chat templates such as Qwen3's. A server that does not know the field ignores it.
2. Whatever still arrives inside `<think>...</think>` is removed, for whole replies and for streamed pieces, even when a tag is split across pieces. An unclosed block is dropped. This applies to every provider.

The CLI's direct local companion also runs with thinking off.

## 4. Token counts

### 4.1 What is stored

Table `model_usage`, one row per call:

| Column | Meaning |
| :--- | :--- |
| `at` | UTC time |
| `session_id` | The server run (one id per start of the app) |
| `profile_id` | e.g. `gemini` |
| `model` | The model that answered (section 3.2) |
| `call` | `consult`, `stream`, `concept_check` or `connection_test` |
| `input_tokens`, `output_tokens` | As the provider reports them; `NULL` when not reported |
| `cost_usd` | Tokens times the profile's prices; `0` for free profiles; `NULL` when tokens are `NULL` |

Never stored: the prompt, the reply, the learner's code, any key.

### 4.2 Where counts come from

- OpenAI SDK: `usage.prompt_tokens`, `usage.completion_tokens`. When streaming, the request sets `stream_options={"include_usage": true}` and reads the last chunk. A local server that ignores this gives `NULL`.
- Gemini: `usage_metadata.prompt_token_count`, `usage_metadata.candidates_token_count`.

A paid call whose counts are missing is costed at its `max_tokens` limit, so the cap can never be undercounted, and the row is marked `estimated`.

### 4.3 Session

A session is one run of the server, from start to stop. The page shows totals for the current session and for the current calendar month, grouped by profile and model: calls, input tokens, output tokens, cost.

## 5. Paid providers and the cap

1. **Off by default.** The active profile starts as `local`.
2. **Switching to a paid profile** shows its prices, the estimated cost of one AXIS question (1,500 input tokens and 400 output tokens, times the profile's prices), and the privacy note: "Your code and questions are sent to <provider>." The owner must tick a confirmation before the switch saves. The server refuses a switch to a paid profile without `confirm_paid: true`.
3. **Monthly cap: US$5**, set as `MONTHLY_CAP_USD` in code with this value, shown on the page. Before every paid call, the server adds this month's `cost_usd` to the worst-case cost of the call (`max_tokens` output plus the input it is about to send). If that passes the cap, the call is not made: AXIS says "The monthly AI budget is used up. Switch to the local model or wait until next month." Month boundaries are UTC.
4. Free profiles are never blocked by the cap.

## 6. API

All under `/api/v1/settings/models`. Local learner only, as other settings routes.

| Route | Does |
| :--- | :--- |
| `GET /` | Profiles (id, label, kind, base_url, model, paid, prices, `key_set: true/false`), active id, mock mode flag, cap, month spend |
| `PUT /active` | Body `{profile_id, confirm_paid}`. 404 unknown id, 409 key not set, 409 paid without confirmation |
| `POST /test` | One short call to the active profile ("Reply with the word ready."). Returns `{ok, model_answered, latency_ms, input_tokens, output_tokens}` or `{ok: false, reason}`. Counts toward usage and the cap |
| `GET /usage` | Session and month totals by profile and model (section 4.3) |

No route returns, accepts or logs a key. `key_set` is computed with `bool(os.environ.get(key_env))` and nothing else about the key leaves the server.

## 7. Settings page

New page `/settings/models`, linked from the main navigation.

1. A card per profile: label, model, address (local only), "Free" or the prices, "Key set: yes/no". The active profile is marked.
2. "Use this" on each card. For a paid profile, a confirmation panel with the cost estimate, the privacy note and a tick box (section 5.2).
3. "Test connection" on the active profile, showing "Answered by <model> in <n> ms" and the token counts, or the reason it failed.
4. A usage table: this session and this month, by profile and model: calls, input tokens, output tokens, cost. Plus "Spent this month: $x of $5".
5. In mock mode, the cards show but switching is disabled, with "Mock mode is on (MOCK_AI=true)".

## 8. Tests (written first)

- Profile loader: each rejection in 2.1; a good file loads.
- Shared rules: both adapters send the same system prompt for the same query; the Socratic guardrail strips code from both.
- OpenAI-compatible adapter: reads usage from a normal reply and from a streamed reply's last chunk; records the model the server reports; `NULL` counts when the server sends none; local falls back to mock, paid does not.
- Gemini adapter: reads `usage_metadata` and `model_version` from a fake client.
- Usage store: rows, session and month totals, cost from prices, `estimated` when counts are missing.
- Cap: a call that would pass $5 is refused before the SDK is called; free profiles are never refused; a new month resets.
- API: `key_set` without leaking the key (the key string appears in no response body); switch rules (404, 409 no key, 409 no confirmation); mock mode disables switching.
- Key safety: with a fake key in the environment, no response, log line or `model_usage` row contains it.
- Frontend: cards, confirmation panel, test result, usage table, mock-mode notice.

All tests run offline with `MOCK_AI=true` and no keys; SDK clients are faked.

## 9. Real check (owner runs it)

After the build, with the owner's keys in `.env`: one connection test to each profile. For Gemini this records which model answers on the free API. Estimated cost: under US$0.01 in total. The owner runs it, per AGENTS.md.

### 9.1 Results, 2026-11-04 (run at the owner's "go")

Total cost: about US$0.00002.

| Asked | Answered | Input / output tokens | Note |
| :--- | :--- | :--- | :--- |
| `gpt-6-luna` | `gpt-6-luna` | 22 / 4 | about 6 s |
| `gemini-3.8-flash` | none | none | listed for the key, but a server error on two tries |
| `gemini-3.6-flash` | `gemini-3.6-flash` | 14 / 13 (thinking included) | 28 s on the first try |

Finding: Gemini's thinking tokens are billed as output, so they are now added to the output count. The Gemini profile uses `gemini-3.6-flash`.

## 10. Out of scope

Entering keys on the page, an OS key store, per-learner providers, automatic quality scoring.
