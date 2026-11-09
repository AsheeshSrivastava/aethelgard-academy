# ADR 0020: Slotted Units, Stage Ids and Path Order

- **Status:** Accepted (2026-11-09, by the owner, as built). Proposed 2026-10-31.
- **Decider:** Platform Architect & Owner (Asheesh Ranjan Srivastava)
- **Date:** 2026-10-31
- **Governed by:** Python Subject Roadmap v4 and Backend Engineering Roadmap v3 (Table 1), Learning Method v2 Amendment A1, the roadmap conversion approved on 2026-10-31

---

## 1. Context & Problem Statement

The converted roadmaps slot Practical DSA, Git, Software Design, AI-Assisted Engineering, Networking and Database units into the Python and Backend paths. The owner chose to keep them as units of the course they sit in, not as new courses.

Each of these roadmaps numbers its own stages from 0. The app identifies a stage by `(course, stage number)` for the course map, builds, stage titles and curriculum checks. "DSA stage 0" inside Python would collide with Python Stage 0.

---

## 2. Decision

1. **Course.** DSA, GIT, SD and AAE units belong to Python. NET and DB units belong to Backend.
2. **Stage id.** A slotted stage keeps an integer id, the roadmap's stage number plus a fixed base: DSA 100, GIT 200, SD 300, AAE 400, NET 500, DB 600. So DSA stage 1 is 101. Every part of the app that keys on a stage keeps working, and no id clashes with a numbered stage.
3. **Label.** Learners never see the id. The API sends a label: "Stage 4" for a numbered stage, and the roadmap's own name for a slotted one ("DSA 0").
4. **Path order.** Table 1 of Python v4 and Backend v3 is the order of units. The catalog holds units in that order.
5. **Stage order on the course map.** Numbered stages keep number order. A slotted stage sits just before the numbered stage of the next numbered unit in Table 1. This keeps today's rule that moved units such as BE-11.1 stay under their old stage label; Table 1 places them earlier in the teaching order, and within a stage units follow Table 1.
6. **Make step credit.** The loader reads a `Make (SKILL):` part of the outcome line, using the approved wording as written. The curriculum checks report an error if the credited skill is not a target of the unit, if the unit has no Build method, or if a Build seed credits another skill (Amendment A1.3).

---

## 3. Consequences

### Positive
- No change to the stage key, the evidence ledger or the build routes.
- Adding a slotted roadmap needs one line in the base table and the course's list.

### Negative / Trade-offs
- Stage ids appear in URLs, for example `/courses/python/stages/100/build`. They are stable but not pretty.
- Backend's moved units are shown under their old stage although Table 1 teaches them earlier. Showing the same stage twice on the map would need a separate decision.

### Not decided here
- Stage builds for the slotted stages (ADR-0018). Until they exist the map shows a placeholder build.
- Cold Check timing and the stage review (ADR-0019).
