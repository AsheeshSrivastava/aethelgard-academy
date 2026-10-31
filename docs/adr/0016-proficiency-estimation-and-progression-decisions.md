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

### C. Consequences
- Skills whose main activity is Explain (CO-3, CO-4, CO-5, CO-6) can reach Adapt on Strong Explain evidence. This is what the decision says; tune it if real learner data shows it is too easy.
