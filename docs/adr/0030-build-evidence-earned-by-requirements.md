# ADR 0030: Build evidence is earned by named requirements

- **Status:** Proposed. Owner decision 2026-11-12: option (b), "add requirements so the build earns them", and DE-3 stays, tied to the ownership note, with the learner told what the note must contain.
- **Decider:** Platform Architect & Owner (Asheesh Ranjan Srivastava)
- **Date:** 2026-11-12
- **Governed by:** ADR-0016 (evidence and the Own rule), ADR-0021 (private answer material), ADR-0028 (documents and review evidence)
- **Spec:** SPEC-15 (sections 2.1 and 5)

---

## 1. Context & Problem Statement

A passed build writes one Strong `Build` evidence entry for every skill in its `proves` list (SPEC-15 section 3). Nothing ties a proved skill to a requirement that tests it. A review of the Stage 0 build (2026-11-12) found that two of its four proved skills were claimed, not earned:

- **VE-4** ("read and fix your own errors"): no requirement involves an error.
- **CO-2** ("order, state and output"): the script reads input and prints it, with no state that changes.
- **DE-3** ("own the reasoning"): earned only by an ownership note of at least 20 characters. The learner was not told what the note should say.

Build evidence weighs heavily in the ledger, and it is the only route to Own. An entry that a requirement did not earn breaks the ledger's promise of "what this learner can really do". Every automated check passed, because none of them asked whether a proved skill was tested.

## 2. Decision

1. **A requirement names the skills it earns.** `requirements[]` gains an optional `skills: [skill_id]`.
2. **Every proved skill must be earned.** Each `proves[].skill_id` must appear in the `skills` of at least one requirement. A new curriculum check, `build-proof-unearned` (error), reports a proved skill that no requirement names.
3. **A requirement may only name proved skills.** A skill in a requirement's `skills` that is not in `proves` is `build-skill-unproved` (error), so a typo cannot satisfy rule 2 for the wrong skill.
4. **Evidence writing is unchanged.** A build passes only when every requirement is met, so each proved skill already has its earning requirements met when the entry is written.
5. **Stage 0 build** earns VE-4 with a planted bug to fix and a README note on the error, and CO-2 with a ticket counter whose value changes. DE-3 stays tied to the ownership note. The note's prompt says what it must contain. Its content is not machine-checked; that is recorded as a known limit (section 4).

## 3. Alternatives considered

- **(a) Drop VE-4 and CO-2 from `proves`.** Honest and fast, but the build then shows less than Stage 0 teaches. Kept as the fallback if the content cannot land before the pilot.
- **(c) Keep the claims and record a known limit.** Rejected: it keeps entries in the ledger that nothing earned.
- **Write evidence per requirement instead of per build.** Rejected for now: it changes the ledger's shape and the Own rule (ADR-0016), for a gain that rule 2 already secures.

## 4. Consequences

- The check catches an unearned claim before any learner sees the build.
- `skills` is authored data. A requirement can still be tagged with a skill it tests weakly. The check proves a link exists, not that the link is strong. Curator review stays responsible for the strength.
- **Known limit (DE-3):** the ownership note is checked for length only. Whether it really names what the learner wrote, what a tool helped with, and what they checked is not machine-checkable today.
- Changing the Stage 0 build changes its private checks and reference solution (listed in the PR, committed to the private repo separately).
