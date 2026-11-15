# REVIEW.md
Wrong in this LMS means (mark these Important):
1. Answer material (keys, hidden checks, solutions) lands in the repo.
2. Evidence turns dishonest: ledger rows edited or deleted, AI grades
   something, or a pass credits a skill it did not test.
3. AXIS breaks the Socratic rule or answers from outside the curriculum index.
4. Learner code escapes the runner (files, network, time limits).
5. A secret is written, logged or printed; a paid model call skips the cost cap.
6. Access loosens: CORS allow-list widened, or one learner reaching another's data.
7. A database change with no migration, or one that can lose learner data.
8. A check or test is skipped, weakened or faked to get green.
9. Untrusted input reaches files, the shell, SQL or a model without checks.
10. Code or tests changed with no ADR or spec named for the change.
Skip: src/lms/web/dist/, frontend/src/api/schema.d.ts, uv.lock, reference/.
At most 3 nits, marked Nit. Every finding cites file:line and says why it fails.
Start the summary with a count. If nothing is wrong, say so.
