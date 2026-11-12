# ADR 0016: Proficiency Estimation and Progression Decisions over the Whole Ledger

- **Status:** Accepted (2026-10-30). Thresholds marked *tunable* approved as starting values.
- **Decider:** Platform Architect & Owner (Asheesh Ranjan Srivastava)
- **Date:** 2026-10-30
- **Governed by:** `Proficiency & Progression System v1`, ADR-0004, ADR-0009

---

## 1. Context & Problem Statement

`core/progression.py::evaluate_progression()` decides from `evidence_entries[-1]` only. That contradicts the Proficiency & Progression System's safeguards:

- *No automatic overwrite:* one weak attempt must not erase an established estimate, and one lucky answer must not justify a big promotion.
- *Contradictory evidence creates uncertainty:* keep the estimate as **provisional** and record the conflict.

It also never returns **Accelerate** or **Rebuild**, stores no *current proficiency*, and has no API, so the redesigned My progress page, course map and unit map cannot show anything real.

The owner decided on 2026-10-30 that evidence from regenerated exercises counts at full strength, and added a delayed **Cold Check** per unit that gates the stage build (section 2.7).

---

## 2. Decision

### 2.1 Two outputs, kept separate
- **Current proficiency** per learner × skill: `level` (Understand | Apply | Adapt | Own | none) and `confidence` (provisional | supported).
- **Progression decision** per learner × unit (and per skill within it): Progress | Accelerate | Strengthen | Rebuild, or the operational state Undecided, plus a one-sentence reason and the ledger entry ids it used.

Both are derived, deterministic, and recomputed from the append-only ledger (ADR-0010: no LLM in this path). A `skill_proficiency` table caches the result; it can always be rebuilt from the ledger.

### 2.2 Which evidence counts
- Entries for the skill within the recency window: the last 10 entries or 90 days, whichever is smaller (*tunable*).
- `SUPPLIED_REASONING` entries are learning evidence, not proficiency evidence: they never raise a level.
- `INSUFFICIENT` entries are ignored for levels.
- Authored and regenerated exercises count equally. Repeating the *same* exercise variant counts once.

### 2.3 Level rules (a level needs its own rule plus every lower rule)
| Level | Qualifying entry |
| --- | --- |
| Understand | Moderate or Strong, any category, assistance ≤ small hint |
| Apply | Moderate or Strong **Perform / Solve**, assistance ≤ small hint |
| Adapt | Strong **Diagnose / Judge / Transfer** on a variant the learner had not seen, assistance ≤ syntax lookup |
| Own | Strong, assistance none, in a stage build or other realistic context |

### 2.4 Confidence
- **Supported:** at least 2 qualifying entries from different exercises (*tunable*), at least one of them a passed Cold Check (section 2.7), and no newer contradicting entry.
- **Provisional:** exactly 1 qualifying entry, no passed Cold Check yet, or a newer weak entry at that level.
- *No automatic overwrite:* one newer weak entry turns a supported level provisional; it does not lower it. Two consecutive weak entries at that level lower it by one (*tunable*).

### 2.5 Decision against the unit's target level
| Decision | When |
| --- | --- |
| Accelerate | Current level is above the target and supported |
| Progress | Current level meets the target and is supported |
| Strengthen | Current level meets the target but is provisional, or is one below the target with qualifying evidence present |
| Rebuild | Two or more consecutive Shaky concept checks for the unit, or three or more weak entries below the target with no qualifying entry (*tunable*) |
| Undecided | No qualifying or contradicting evidence yet; the response names the smallest next probe (an activity of the unit) |

A unit's decision is the weakest decision among its target skills (Rebuild < Strengthen < Undecided < Progress < Accelerate).

### 2.6 Cold Check (delayed retrieval)
- **What:** a short, unseen variant covering the unit's target skills, taken with no AXIS help (the AXIS panel is off; assistance is recorded as none).
- **When:** available 24 hours (*tunable*) after the learner completes the unit's last activity. The clock is a server-side timestamp comparison; no workflow engine is needed.
- **Does not block learning:** the learner can start the next unit while waiting.
- **Evidence:** a pass records a Strong entry in the activity's category at the unit's target level and is required for *supported* confidence (section 2.4). A fail records a Weak entry, sets the unit decision to **Strengthen**, and schedules a new Cold Check 24 hours later.
- **Regenerate:** offered only after an attempt, so a learner cannot reroll for an easier variant before trying.
- **Stage build gate:** a stage's build (script or mini-project) unlocks only when every unit in that stage has a passed Cold Check.

### 2.7 API
`GET /api/v1/learners/me/proficiency` (SPEC-12 section 6). `evaluate_progression()` keeps its signature for the CLI but delegates to the new estimator.

---

## 3. Consequences

### Positive
- Decisions follow the governing Proficiency & Progression System instead of the last click.
- Every decision is explainable: it carries its reason and ledger entry ids, which the My progress page shows.

### Negative / Trade-offs
- Thresholds are first guesses and need tuning against real learner data.
- Existing `test_progression.py` cases that assume last-entry behaviour must be rewritten test-first.

---

## Amendment 2026-10-31: main activities and fixed answer keys

Decided by the owner after the SPEC-12 section 3.1 curriculum checks ran on all three roadmaps. The checks found 115 skill targets that could never earn their level and 41 units with no gradable Cold Check. The roadmaps stay unchanged (AGENTS.md section 4); the rules were too narrow.

### A. A skill's main activity counts for Apply and Adapt (changes section 2.3)
Learning Method v2 gives every skill one main activity ("Which activities develop which skills"), and a unit's Methods list is built from that table. Section 2.3 ignored this: `CO-1` at Apply lists Predict, which is Explain / Reason evidence, so no learner could reach the target.

An entry whose `activity` is its skill's main activity now also qualifies:

| Level | Qualifying entry (amended) |
| --- | --- |
| Apply | Moderate or Strong **Perform / Solve**, or **the skill's main activity**, assistance ≤ small hint |
| Adapt | Strong **Diagnose / Judge / Transfer**, or **the skill's main activity**, on a variant the learner had not seen, assistance ≤ syntax lookup |

- **Only the "Main activity" column counts**, not "Also helps".
- **Source:** the table in `reference/Learning Method v2.md`, read when the curriculum loads. There is no per-skill list in code.
- **Understand and Own do not change.** Own still needs a Strong, unassisted stage build.
- **The entry must name its activity.** Entries with no `activity` (older rows, concept checks recorded without one) use the original rule only. A Cold Check entry records the activity of the exercise taken, so a passed Cold Check can qualify under this rule.

### B. Fixed-answer Evaluate and Direct are gradable (changes section 2.6)
A Cold Check needs a deterministically graded activity. Evaluate and Direct now count when the exercise carries a curator-written fixed answer key, for example "choose the trustworthy output" or "pick the correct instruction". No AI grades them. The key format is defined in SPEC-13.

### C. A Cold Check counts only for what it tests (decided 2026-10-31)
190 skill targets have Explain, Specify or Decompose as their main activity, and amendment B left those activities with no machine-graded form. The owner rejected giving blanket credit at the unit's target level: a pass would then record evidence for a skill that was never tested, which a production platform cannot defend.

- **A passed Cold Check counts only for the skill it tests, through that skill's own main activity.** One item gives evidence for one skill. A unit needs an item for each target skill.
- **Explain, Specify and Decompose are Cold Check eligible through deterministic item types** defined in SPEC-13: `specify_by_tests`, `specify_contract`, `decompose_plan`, `decompose_code`, `explain_spot_flaw` and `explain_model_choice`.
- **Free-text explanation stays ungraded practice:** the CO-6 Solid/Shaky check works as before and is never part of a Cold Check. AI never grades a Cold Check.
- **Until a skill has an item, it stays provisional.** The platform says "not yet proven" rather than claiming support it cannot show.

The sentence in section 2.6 that a pass records an entry "at the unit's target level" is read with this rule: the entry is for the tested skill only.

### E. Evidence counts per seed (decided 2026-10-31)
Section 2.2 said repeating the same exercise variant counts once. Name variants of one seed differ only on the surface, so they count as the same exercise. Repeats of a seed count once, and the newest result is the one kept, so a learner who fails and then succeeds is judged on where they are now.

### F. The decision asks about the target level (2026-10-31)
With amendment A, one Strong entry can reach a level above a unit's target while the target itself is fully supported. The confidence of the highest level must not hide that. Progress needs support **at the target level**. Accelerate still needs support at the higher level.

### D. Consequences
- Skills whose main activity is Explain (CO-3, CO-4, CO-5, CO-6) can reach Adapt on Strong Explain evidence. This is what the decision says; tune it if real learner data shows it is too easy.
- Authoring grows: every target skill needs a Cold Check item, so up to 190 targets need the new item types.
- One Strong, unassisted entry on a main activity meets the Understand, Apply and Adapt rules at once, so it reaches Adapt straight away. It stays provisional until a second exercise and a passed Cold Check, so it decides Strengthen, not Accelerate.

## Amendment 2026-10-31: stage review

ADR-0019 changes section 2.6. A stage build no longer opens because every unit passed its Cold Check: a passed stage review opens it. When a stage has no unseen item for a review, the old rule still applies (SPEC-16 section 3.4).

## Amendment 2026-11-04: reset markers (owner, options 1b.1 A and 1b.2 A)

1. **The ledger is never deleted.** A reset writes a marker (`progress_reset`: learner, scope, time) and keeps every entry.
2. **Per unit.** A unit's decision, the activities it counts as tried, and its row on My progress use only evidence recorded at or after that unit's latest reset. Other units keep their own evidence, even when they share a skill. On My progress, a skill row uses evidence after the latest reset among the units in view that target it.
3. **Lifetime levels are unchanged.** Anything not tied to one unit (the ledger list, rechecks, a future skills page) still reads the whole ledger.
4. **Stage review.** "Restart stage review" clears that stage's review rounds and result and writes a marker for the stage. The build closes again until the review is passed (ADR-0019). Rechecks already earned are kept.
5. **My skills (approved 2026-11-04).** A "My skills" page shows each of the framework's 27 skills once, grouped by its five areas, with its level from the whole ledger across every course. Skills belong to the framework, not to a course, so the page is never grouped by stage. The decision labels stay on My progress, explained there (SPEC-12 section 6.1).

## Amendment 2026-11-12: a repeated concept check counts once (owner)

### G. Every concept check is an exercise with its own id (changes section 2.2 and amendment E)
The CO-6 concept check was recorded with no exercise or seed id, so section 2.2's "repeating the same exercise counts once" never applied to it. The same answer submitted twice counted as two qualifying exercises, which proves memory, not understanding.

1. **Id.** A concept check's evidence carries the id of the prompt that was answered: `<unit>/explain/v<n>`, for example `PY-0.1/explain/v1`. Today each unit has one prompt (`v1`); more prompts get `v2`, `v3` and so on.
2. **Repeats count once.** As in amendment E, repeats of one concept-check prompt count once, and the newest result is the one kept. The second piece of support for a level must come from a different exercise: another activity of the unit, another prompt, or the Cold Check.
3. **Older rows.** The ledger is append-only, so rows written before this amendment are not changed. When a concept check (a CO-6 Explain entry) has no exercise or seed id, the estimator reads it as `<unit>/explain/v1`. This corrects existing learner history without rewriting it.
4. **Rebuild is unchanged.** "Two or more consecutive Shaky concept checks" (section 2.5) still counts every attempt, because a run of Shaky answers is a warning sign even when the prompt repeats.
