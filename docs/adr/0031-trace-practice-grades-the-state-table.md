# ADR 0031: Trace practice grades the state table

- **Status:** Proposed. Owner decision 2026-11-12: option (b), "its own PR now, practice Trace items only".
- **Decider:** Platform Architect & Owner (Asheesh Ranjan Srivastava)
- **Date:** 2026-11-12
- **Governed by:** ADR-0016 (evidence and grading; no AI grades an exercise), ADR-0021 (private answer material)
- **Spec:** SPEC-13 section 4 (`trace`), SPEC-12 section 4 (Exercise and Attempt)

---

## 1. Context & Problem Statement

The roadmap's CO-2 outcome for PY-0.1 is "fills in a state table step by step and explains any mismatch". A trace item's private key already holds the table (`line_states`), but the grader compares only the printed lines (`expected_output`). So CO-2 evidence today is one or two printed lines, and a learner can get them right by running the code in their head loosely, without tracking each name.

The Stage 0 round 2 Cold Check review (2026-11-12) found this. The owner chose to grade the table now, on practice items only.

## 2. Decision

1. **Practice trace items grade the state table** when their key has `line_states`. Cold Check trace items keep the output-only rule for now.
2. **Served:** the item lists the rows to fill as `state_rows: [{line, names}]`. Line numbers and names give nothing away; values stay private.
3. **Attempt:** a new optional field, `trace_states: [{line, state: {name: text}}]`.
4. **Pass:** the output lines are right and every cell is right. Cells are compared as text, forgivingly: ends trimmed, runs of spaces read as one, and one pair of quotes around the value removed. So `waiting`, `"waiting"` and `'waiting'` all match `"waiting"`, and `1` matches `1`.
5. **Feedback:** a score of cells right out of cells, and a reveal of the full table after the attempt (as today for output).
6. **Evidence is unchanged.** A pass writes the same entry as before. Only what counts as a pass changes.

## 3. Alternatives considered

- **Grade the table on Cold Check items too.** Deferred. It changes gated results, and the Cold Check screen and its retry rules (SPEC-16) would need the same input. Practice comes first, so learners meet the table before any gate.
- **Type-strict cells** (`"1"` is not `1`). Rejected at Understand: the PY-0.1 goal is following state, not writing literals. Types are tested by PY-0.4's predict items.
- **Grade the table only, not the output.** Rejected: printing is part of the trace (CO-1 overlap is intended).

## 4. Consequences

- CO-2 practice evidence now requires following each name, which matches the roadmap outcome.
- Every practice trace seed should carry `line_states` for each line that changes a name. Seeds without them keep working on the output-only rule.
- The table never shows a learner the values before they answer, so the private-answer rule (ADR-0021) holds.
- **Known limit:** Cold Check CO-2 evidence is still output-only. A follow-up can extend the table to Cold Check items once practice shows it works.
