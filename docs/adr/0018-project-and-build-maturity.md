# ADR 0018: Project and Build Maturity in the Learning Path

- **Status:** Proposed (2026-10-31)
- **Decider:** Platform Architect & Owner (Asheesh Ranjan Srivastava)
- **Date:** 2026-10-31
- **Governed by:** Projects & Capstones Integration Layer v1 (P0 to P4 ladder), ADR-0016 (Cold Check), ADR-0019 (stage review unlocks the stage build), Learning Method v2 Amendment A1

---

## 1. Context & Problem Statement

The roadmaps now name three kinds of build work: Make steps inside units, one build per stage, and course projects carried over from the supporting roadmaps (Practical DSA, Software Design, Database, AI-Assisted Engineering). The app only knows stage builds (ADR-0016, `curriculum/<course>/builds/`). The Projects & Capstones Integration Layer defines a P0 to P4 maturity ladder but nothing in the app maps build work onto it, so a learner cannot tell an exercise from a portfolio claim.

---

## 2. Decision

1. **One ladder.** Every piece of build work carries a maturity label from the Projects & Capstones Integration Layer:

   | Work | Where it lives | Maturity |
   | --- | --- | --- |
   | Make step | a unit's Build activity | P0 |
   | Stage build | one per stage, unlocks when the learner passes the stage review (ADR-0019) | P1 |
   | Course project | one per course or supporting roadmap that has one | P2 |
   | Portfolio project | a P2 project promoted after owner review | P3 |
   | Capstone | end of the whole path, integrates several courses | P4 |

2. **Every stage has a build**, including the stages of the supporting roadmaps (DSA 0 and 1, GIT 0 to 2, SD 0 and 1, AAE 0, NET 0, DB 0 and 1). A supporting roadmap's stage build may be the next Python or Backend stage build when the units sit inside it; the build spec then lists both.
3. **Course projects** are the integration stages of the old supporting roadmaps (DSA-5.5, SD-8.4, DB Stage 12, AAE Stage 16), as named in each converted roadmap under "Course project". They unlock when the course's last stage build passes.
4. **Promotion is a review, never automatic.** P2 to P3 and P3 to P4 need the owner's review against the layer's Gate C. Finishing a project is evidence of the artifact, not of proficiency.
5. **Evidence stays localized.** A build or project produces evidence only for the skills named in its spec. A maturity label never raises a skill estimate by itself.
6. **Data:** the build spec gains `maturity` (P0 to P4) and `kind` (`stage-build`, `course-project`, `capstone`). Existing stage builds default to P1.

---

## 3. Consequences

### Positive
- The learner sees one ladder from first exercise to capstone, and what each step is worth.
- Units that target a skill at Own already need a stage build (curriculum check `own-needs-stage-build`); this ADR says what that build is.

### Negative / Trade-offs
- The supporting roadmaps add 11 stages, each needing a stage build, on top of the Python, Backend and AI Engineering stage builds not yet written.
- Course projects need an owner review step that the app does not have yet.

### Not decided here
- The capstone's content and whether it spans Python, Backend and AI Engineering.
