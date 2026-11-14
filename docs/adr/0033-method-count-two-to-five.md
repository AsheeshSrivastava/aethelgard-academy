# ADR 0033: A unit carries 2 to 5 methods

- **Status:** Proposed. Owner decision 2026-11-14: change the method-count rule from "2 to 3" to "2 to 5".
- **Decider:** Platform Architect & Owner (Asheesh Ranjan Srivastava)
- **Date:** 2026-11-14
- **Governed by:** AGENTS.md (Unit Integrity), Learning Method v2 (Methods list: Explain first, then one main activity per target skill)
- **Work sequence:** 2d.6

---

## 1. Context & Problem Statement

AGENTS.md says a unit has "2 to 3 discrete methods". The loaded curriculum (count of 2026-11-09, 296 units) does not follow that: 1 unit has 1 method (BE-7.1), 32 have 2, 126 have 3, 114 have 4, 23 have 5. The rule is broken by 137 units. Learning Method v2 sets the Methods list from the target skills (Explain, then one main activity per skill, with 1 to 3 skills), so 4 to 5 methods follow from the method itself.

## 2. Decision

1. A unit carries 2 to 5 methods, beginning with Explain and the CO-6 concept check. The unit's target skills (1 to 3) still decide which activities follow.
2. Learning Method v2 gives no count, so it needs no amendment. AGENTS.md and the glossary change from "2 to 3" to "2 to 5".
3. BE-7.1 (1 method) is the one unit outside the rule. It gets a second method when the Backend content is written (recorded exception until then).

## 3. Consequences

- The rule matches 295 of 296 units, so it is a rule again, not a known-broken one.
- New content is written to the new range. Check: a curriculum check on the method count can follow in a later PR.
- No code changes.
