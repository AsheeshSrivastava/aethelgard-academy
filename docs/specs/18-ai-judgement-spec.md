# SPEC-18: AI Judgement of Written Explanations

- **Governed by:** ADR-0026 (this design), ADR-0025 / SPEC-17 (provider profiles), ADR-0022 (interaction log), ADR-0021 (answers private)
- **Date:** 2026-11-08
- **First user:** the CO-6 concept check (`POST /api/v1/explain`). README, ADR and spec feedback reuse it later (ADR-0024).

---

## 1. The rubric (private)

`<LMS_ANSWERS_DIR>/<course>/<unit folder>/concept_check.json`:

```json
{ "unit_id": "PY-0.4",
  "ideas": [ { "id": "returns-text", "text": "input() always gives back text (a string), whatever is typed." },
             { "id": "math-needs-numbers", "text": "..." } ] }
```

- 2 or 3 ideas. `id` is a short slug, unique in the file. `text` is what the idea is, in plain words; it is shown to the learner **after** they answer, beside met or missed.
- The public `meta.json` `concept_check` keeps only `prompt`. A public `concept_check` holding `rubric`, `solid_keywords` or `ideas` is a `concept-check-answers-public` error, and a guard test scans every public `meta.json`.
- A unit with a prompt but no private rubric gets the warning `concept-check-rubric-missing`.

## 2. The verdict (shared)

```text
AiJudgement {
  status: "judged" | "not_judged",
  verdict: "Solid" | "Shaky" | null,          # null when not judged
  ideas: [ { id, text, met: bool } ],         # empty when not judged
  feedback: str | null,                        # the model's one or two sentences
  model: str | null,                           # the model that answered, as the provider reports it
  reason: null | "ai_off" | "no_rubric" | "cap_reached" | "provider_refused" | "no_answer" | "unreadable_reply",
  message: str,                                # plain words for the learner (section 4)
  interaction_id: str | null                   # the logged judgement, for a dispute
}
```

- **Solid** when every idea is met; otherwise **Shaky**. The code decides this from the per-idea answers, never the model's own overall view.
- `ExplainResponse` returns `AiJudgement` plus `unit_id` and `evidence_logged`.

## 3. The judging call

- The **judging model** is the profile chosen under Settings, "Judging model" (SPEC-17 section 7); unset, the active chat profile.
- System prompt: judge only whether each listed idea is shown in the learner's explanation, in any wording; ignore spelling and grammar; never add new requirements; reply only with JSON `{"ideas": [{"id": "...", "met": true}], "feedback": "..."}`. The feedback speaks to the learner, names what is missing in plain words, and never gives a code solution (ADR-0009).
- Temperature 0 where the profile sends one; a fixed output-token limit.
- The reply is checked: valid JSON, every rubric id exactly once, `met` a boolean, `feedback` a non-empty string of at most 400 characters. Anything else is `unreadable_reply`.
- With `MOCK_AI=true` the offline mock judges deterministically: an idea is met when the explanation contains a whole word from the idea's `text` of 5 or more letters. Its model name is `offline-mock`. Tests and CI use it; it is never used when a real profile is set.

## 4. Not judged

| `reason` | When | `message` |
| --- | --- | --- |
| `ai_off` | No profile can be called (no key set, nothing configured) | AI is off, so this was not judged. Your answer is saved; try again when AI is on. |
| `no_rubric` | The unit has no private rubric | This concept check has no marking guide yet, so it was not judged. |
| `cap_reached` | The monthly spending cap is reached | The monthly AI budget is used up, so this was not judged. |
| `provider_refused` | Quota, rate limit, or the key was refused (HTTP 401, 403, 429, or the SDK's equivalent) | The AI provider refused the request (quota, rate limit or key). This was not judged. |
| `no_answer` | Connection error, timeout, or a server error | The AI provider did not answer. This was not judged; try again in a moment. |
| `unreadable_reply` | The reply failed the checks in section 3 | The AI's reply could not be read, so this was not judged. |

- Not judged writes **no** ledger entry. The interaction log records the attempt with the reason. The error text from the provider is never shown and never logged beyond its class name; keys are never logged.

## 5. Evidence

- `CONCEPT_CHECK_WRITES_EVIDENCE = True` (owner option A). A judged verdict writes one CO-6 entry, Strong for Solid, Weak for Shaky. `demonstration_context` names the judging model; `observed_reasoning` lists the ideas met and missed.
- Set to `False` (option C), a verdict writes nothing and `evidence_logged` is false.
- Judged or not, the Cold Check clock is checked as before; it only moves when evidence exists.

## 6. Disputes

- `POST /api/v1/learners/me/judgements/{interaction_id}:dispute` → `204`. Logs `judgement_disputed` with the disputed interaction id. Unknown or another learner's id → `404`. It never changes the verdict or the ledger.

## 7. Frontend: the AI judgement component

Shown under the concept check after an answer:

- **Judged:** the verdict (Solid or Shaky), each idea with met or missed, the feedback, then a small line "Judged by AXIS (<model>). AI can be wrong." and a "This seems wrong" button. After a click: "Thanks. Noted for review." The button works once.
- **Not judged:** the plain message from section 4, no verdict, no button.
- The component takes an `AiJudgement` and an optional dispute handler, so other screens reuse it.

## 8. Settings

- Settings page: "Judging model", a choice of the configured profiles plus "Same as AXIS chat". Stored like the active profile. A paid profile needs the same confirmation as for chat (SPEC-17 section 5).
- `GET /api/v1/settings/models` includes `judge_profile_id` (null = same as chat); `PUT /api/v1/settings/models/judge` with `{profile_id: str | null, confirm_paid: bool}`.

## 9. Tests (written first)

1. Rubric loading: private file joined; public rubric fields refused; missing rubric warned.
2. Verdict rule: all met → Solid; any missed → Shaky; the model's own "overall" is ignored.
3. Reply checks: each malformed reply → `unreadable_reply`.
4. Each failure class maps to its `reason`; none writes evidence; none falls back to keywords.
5. Judged writes one tagged CO-6 entry; with the switch off, none.
6. The mock judges deterministically.
7. Dispute: logged, 204; unknown id 404; verdict and ledger unchanged.
8. Judging model: unset uses chat; set uses that profile; paid needs confirmation.
9. Frontend: judged view with ideas, annotation and one-time dispute; not-judged view with message and no button.
10. Guard: no public `meta.json` holds rubric, keywords or ideas.
