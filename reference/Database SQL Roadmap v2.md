---
title: Database / SQL Roadmap v2
created-date: 2026-10-31
status: approved
approved-date: 2026-10-31
version: "2.0"
supersedes: "Database / SQL Roadmap v1 (55 units, Competency Model codes)"
governed-by: "AI-Era Programming Skills Framework v1 (27 skills); Learning Method v2 with Amendment A1 (2026-10-31)"
roadmap-role: "Supporting roadmap, slotted into the Python and Backend path"
ai-involvement: collaborative
ai-provider: Claude
tags:
  - "#claude"
---

> [!info] Provenance
> AI-drafted with Claude on 2026-10-31 at Asheesh's direction. **The scope (which units are kept, merged or dropped) and their place in the path were approved by Asheesh on 2026-10-31.** Target skills, goal levels, Methods, concept lines and outcome lines are new AI-drafted wording, checked by script against the Framework and Learning Method v2, and not yet reviewed by Asheesh. Detailed teaching tasks per unit are still to be written. The v1 file stays in `reference/` until it is moved to history.

# Database / SQL Roadmap v2

**Purpose.** Relational modelling, SQL, transactions, indexes, query plans and schema change, as needed by Backend and AI Engineering. PostgreSQL for examples.

## What changed from v1

- **Converted to the AI-Era Programming Skills Framework.** Each unit has one to three target skills from the 27, each with a goal level, a one-line concept for Explain and the CO-6 check, a Methods list (Explain first, then the main activity of each target skill) and an outcome line that can be graded without AI. The old five competencies are gone.
- **13 units replace 42 v1 units.** Small v1 units were merged into units the size of a Python unit; each unit lists the v1 units it replaces. Dropped: Owner cut 2026-10-31: DB-4.4 (window functions). Supporting: DB-2.3 (CASE and functions), DB-2.5 (RETURNING), DB-4.3 (set operations), DB-4.5 (window frames), DB-7.5 (other index types, now awareness in DB-1.4), DB-9.1, 9.2 (views). DB-12.x becomes the course project.
- **Entry rule (Learning Method Amendment A1).** No skill enters the learning path above Apply, and no skill rises more than one level from one unit to the next. Levels here are set for where these units sit in the path, after the Python units that precede them.
- **Slotted into the path.** Units are taught where the path first needs them, not as a separate course run after Python (see "Place in the path").
- **New unit IDs.** IDs restart at `DB-0.1`. The "Replaces (v1)" field maps each one to the old IDs.

## Place in the path

| Stage | Title | Taught | Units |
| --- | --- | --- | --- |
| 0 | Relational model and SQL | in Backend, before Stage 6 (persistence) | 7 |
| 1 | Schema design, transactions and performance | in Backend, before Stage 6 (persistence) | 6 |

**Course project.** DB v1 Stage 12 (integrated database engineering) becomes a course project at maturity P2: design, migrate, query and tune the relief-centre database.

## Table 1: sequence, target skills and methods

| # | Unit | Stage | Targets (goal level) | Methods |
| --- | --- | --- | --- | --- |
| 1 | DB-0.1 Why databases, and the relational model | 0 | CO-6 (Apply), DE-6 (Apply) | Explain → Evaluate |
| 2 | DB-0.2 Keys and relationships | 0 | SP-2 (Adapt), CO-5 (Adapt) | Explain → Specify |
| 3 | DB-0.3 Constraints and integrity violations | 0 | VE-4 (Adapt), VE-6 (Adapt) | Explain → Debug & Validate |
| 4 | DB-0.4 SELECT, NULL and safe writes | 0 | CO-1 (Adapt), VE-6 (Adapt) | Explain → Predict → Debug & Validate |
| 5 | DB-0.5 Joins and join bugs | 0 | CO-1 (Adapt), VE-2 (Adapt), BU-2 (Adapt) | Explain → Predict → Modify → Debug & Validate |
| 6 | DB-0.6 Aggregation with GROUP BY and HAVING | 0 | BU-2 (Adapt), VE-1 (Adapt) | Explain → Modify → Debug & Validate |
| 7 | DB-0.7 Subqueries and CTEs | 0 | SP-3 (Adapt), BU-4 (Adapt) | Explain → Decompose → Modify |
| 8 | DB-1.1 Schema design and normalisation | 1 | SP-1 (Adapt), SP-2 (Adapt), DE-6 (Adapt) | Explain → Specify → Evaluate |
| 9 | DB-1.2 Transactions and ACID | 1 | CO-6 (Adapt), VE-5 (Adapt) | Explain → Debug & Validate |
| 10 | DB-1.3 Concurrency anomalies, isolation and locks | 1 | CO-1 (Adapt), VE-3 (Adapt), DE-6 (Adapt) | Explain → Predict → Debug & Validate → Evaluate |
| 11 | DB-1.4 Indexes from query patterns | 1 | DE-6 (Adapt), VE-6 (Adapt) | Explain → Evaluate → Debug & Validate |
| 12 | DB-1.5 Query plans and evidence-led tuning | 1 | VE-3 (Adapt), VE-5 (Adapt) | Explain → Debug & Validate |
| 13 | DB-1.6 Migrations and choosing storage | 1 | BU-5 (Adapt), VE-6 (Adapt), DE-6 (Adapt) | Explain → Modify → Debug & Validate → Evaluate |

The CO-6 concept check runs in every unit as part of Explain and is a target only where listed.

## Table 2: stage, unit and topics

| Stage | Unit | Topics |
| --- | --- | --- |
| 0 | DB-0.1 Why databases, and the relational model | why databases; relations, rows, columns; logical schema versus application objects; PostgreSQL and SQLite for practice |
|  | DB-0.2 Keys and relationships | primary keys; natural versus surrogate keys; foreign keys; one-to-many; unique constraints for business rules |
|  | DB-0.3 Constraints and integrity violations | NOT NULL, CHECK, DEFAULT; data types; referential actions (CASCADE, RESTRICT, SET NULL); reading integrity errors |
|  | DB-0.4 SELECT, NULL and safe writes | SELECT, WHERE, ORDER BY, LIMIT; NULL and three-valued logic; IS NULL; INSERT, UPDATE, DELETE; previewing a write with SELECT; parameterised queries |
|  | DB-0.5 Joins and join bugs | inner and left joins; join type versus relationship type; fan-out and duplicates; missing rows; anti-joins |
|  | DB-0.6 Aggregation with GROUP BY and HAVING | COUNT, SUM, AVG, MIN, MAX; GROUP BY; HAVING versus WHERE; COUNT(*) versus COUNT(column); NULLs in aggregates |
|  | DB-0.7 Subqueries and CTEs | scalar and table subqueries; EXISTS; WITH (CTEs); naming steps; checking each step alone |
| 1 | DB-1.1 Schema design and normalisation | entities and relationships from requirements; many-to-many and association tables; update, insert and delete anomalies; functional dependencies and normal forms at practical depth; denormalising for a measured need |
|  | DB-1.2 Transactions and ACID | BEGIN, COMMIT, ROLLBACK; atomicity, consistency, isolation, durability as behaviours; transactions from Python |
|  | DB-1.3 Concurrency anomalies, isolation and locks | lost updates; dirty, non-repeatable and phantom reads; isolation levels; SELECT ... FOR UPDATE; blocking and deadlocks at application depth |
|  | DB-1.4 Indexes from query patterns | what an index changes; B-tree indexes; composite index order; constraint-backed versus performance indexes; write cost; other index types (awareness) |
|  | DB-1.5 Query plans and evidence-led tuning | EXPLAIN and EXPLAIN ANALYZE; sequential scan versus index scan; estimated versus actual rows; running ANALYZE safely; one change at a time |
|  | DB-1.6 Migrations and choosing storage | migration tools (Alembic as an example); expand and contract; backfills; migrations versus deploys; testing on representative data; when document, key-value, graph or vector storage fits; pgvector (awareness) |

## Unit details

### Stage 0: Relational model and SQL

#### DB-0.1 Why databases, and the relational model

- **Objective:** Can explain why applications use a database and reason in terms of tables, rows, columns and keys.
- **The concept (Explain):** A table holds facts as rows with the same columns; the database keeps them correct and shared.
- **Target skills:** CO-6 to Apply; DE-6 to Apply
- **Methods:** Explain → Evaluate
- **Outcome (measured at unit end):** CO-6: explains rows, columns and keys in their own words, and why a table is not a list of Python objects. DE-6: chooses a database over JSON files for a stated need, with the reason.
- **Topics:** why databases; relations, rows, columns; logical schema versus application objects; PostgreSQL and SQLite for practice
- **Prerequisites:** PY-8.2 | **Importance:** Foundational | **Replaces (v1):** DB-0.1, DB-0.2, DB-0.3

#### DB-0.2 Keys and relationships

- **Objective:** Can choose primary, foreign and unique keys that give rows a stable identity and encode relationships.
- **The concept (Explain):** A key says what makes a row unique; a foreign key says which row another row belongs to.
- **Target skills:** SP-2 to Adapt; CO-5 to Adapt
- **Methods:** Explain → Specify
- **Outcome (measured at unit end):** SP-2: specifies primary, foreign and unique keys for households, people and applications, with example rows including edge cases. CO-5: sketches the relationships.
- **Topics:** primary keys; natural versus surrogate keys; foreign keys; one-to-many; unique constraints for business rules
- **Prerequisites:** DB-0.1 | **Importance:** Core | **Replaces (v1):** DB-1.1, DB-1.2, DB-1.3

#### DB-0.3 Constraints and integrity violations

- **Objective:** Can use constraints and types so the database rejects bad data, and read the errors it raises.
- **The concept (Explain):** Constraints let the database refuse bad data, so the application cannot forget to check it.
- **Target skills:** VE-4 to Adapt; VE-6 to Adapt
- **Methods:** Explain → Debug & Validate
- **Outcome (measured at unit end):** VE-4: reads constraint-violation errors and names the rule broken. VE-6: tries inserts and deletes that should fail and confirms the database rejects them.
- **Topics:** NOT NULL, CHECK, DEFAULT; data types; referential actions (CASCADE, RESTRICT, SET NULL); reading integrity errors
- **Prerequisites:** DB-0.2 | **Importance:** Core | **Replaces (v1):** DB-1.4, DB-1.5, DB-1.6

#### DB-0.4 SELECT, NULL and safe writes

- **Objective:** Can write correct basic queries, reason about NULL, and change data safely.
- **The concept (Explain):** NULL means unknown, so comparisons with it are neither true nor false.
- **Target skills:** CO-1 to Adapt; VE-6 to Adapt
- **Methods:** Explain → Predict → Debug & Validate
- **Outcome (measured at unit end):** CO-1: predicts row counts of queries that meet NULLs. VE-6: runs an UPDATE inside a transaction and checks the affected rows before committing.
- **Topics:** SELECT, WHERE, ORDER BY, LIMIT; NULL and three-valued logic; IS NULL; INSERT, UPDATE, DELETE; previewing a write with SELECT; parameterised queries
- **Prerequisites:** DB-0.2 | **Importance:** Core | **Replaces (v1):** DB-2.1, DB-2.2, DB-2.4

#### DB-0.5 Joins and join bugs

- **Objective:** Can join related tables correctly and diagnose duplicate or missing rows caused by joins.
- **The concept (Explain):** A join pairs rows by a condition; the relationship decides how many rows come out.
- **Target skills:** CO-1 to Adapt; VE-2 to Adapt; BU-2 to Adapt
- **Methods:** Explain → Predict → Modify → Debug & Validate
- **Outcome (measured at unit end):** CO-1: predicts row counts of inner and left joins. VE-2: finds why an AI-written report double counts. BU-2: brings the query up to the report spec, mapping each edit to a spec line.
- **Topics:** inner and left joins; join type versus relationship type; fan-out and duplicates; missing rows; anti-joins
- **Prerequisites:** DB-0.4 | **Importance:** Core | **Replaces (v1):** DB-3.1, DB-3.2, DB-3.3

#### DB-0.6 Aggregation with GROUP BY and HAVING

- **Objective:** Can summarise data with GROUP BY and HAVING and check the totals.
- **The concept (Explain):** GROUP BY turns many rows into one row per group; HAVING filters the groups.
- **Target skills:** BU-2 to Adapt; VE-1 to Adapt
- **Methods:** Explain → Modify → Debug & Validate
- **Outcome (measured at unit end):** BU-2: brings a draft per-centre totals query up to its spec. VE-1: writes checks on empty groups and NULLs that a plausible wrong query would fail.
- **Topics:** COUNT, SUM, AVG, MIN, MAX; GROUP BY; HAVING versus WHERE; COUNT(*) versus COUNT(column); NULLs in aggregates
- **Prerequisites:** DB-0.5 | **Importance:** Core | **Replaces (v1):** DB-3.4, DB-3.5

#### DB-0.7 Subqueries and CTEs

- **Objective:** Can split a complex question into named query steps and keep the query readable.
- **The concept (Explain):** A CTE names one step of a question so the next step can use it.
- **Target skills:** SP-3 to Adapt; BU-4 to Adapt
- **Methods:** Explain → Decompose → Modify
- **Outcome (measured at unit end):** SP-3: splits a report question into named CTE steps, each checkable alone. BU-4: rewrites a nested query as CTEs without changing its result.
- **Topics:** scalar and table subqueries; EXISTS; WITH (CTEs); naming steps; checking each step alone
- **Prerequisites:** DB-0.6 | **Importance:** Core | **Replaces (v1):** DB-4.1, DB-4.2

### Stage 1: Schema design, transactions and performance

#### DB-1.1 Schema design and normalisation

- **Objective:** Can turn a requirement into tables and relationships, spot anomalies, and denormalise only for a shown need.
- **The concept (Explain):** Store each fact once, so a change happens in one place.
- **Target skills:** SP-1 to Adapt; SP-2 to Adapt; DE-6 to Adapt
- **Methods:** Explain → Specify → Evaluate
- **Outcome (measured at unit end):** SP-1 and SP-2: turns a requirement into tables, keys and relationships, stating open questions. DE-6: finds an update anomaly and decides whether to normalise or keep a denormalised copy, with the reason.
- **Topics:** entities and relationships from requirements; many-to-many and association tables; update, insert and delete anomalies; functional dependencies and normal forms at practical depth; denormalising for a measured need
- **Prerequisites:** DB-0.3 | **Importance:** Core | **Replaces (v1):** DB-5.1, DB-5.2, DB-5.3, DB-5.4, DB-5.5

#### DB-1.2 Transactions and ACID

- **Objective:** Can group related changes into one transaction and explain what ACID guarantees.
- **The concept (Explain):** A transaction is all or nothing: either every change in it happens or none does.
- **Target skills:** CO-6 to Adapt; VE-5 to Adapt
- **Methods:** Explain → Debug & Validate
- **Outcome (measured at unit end):** CO-6: explains atomicity and durability with their own example and a non-example. VE-5: proves a two-table update is all or nothing by forcing a failure halfway.
- **Topics:** BEGIN, COMMIT, ROLLBACK; atomicity, consistency, isolation, durability as behaviours; transactions from Python
- **Prerequisites:** DB-0.4 | **Importance:** Core | **Replaces (v1):** DB-6.1, DB-6.2

#### DB-1.3 Concurrency anomalies, isolation and locks

- **Objective:** Can recognise concurrency anomalies and choose an isolation level or lock from the correctness need.
- **The concept (Explain):** Two transactions running at once can each be correct alone and wrong together.
- **Target skills:** CO-1 to Adapt; VE-3 to Adapt; DE-6 to Adapt
- **Methods:** Explain → Predict → Debug & Validate → Evaluate
- **Outcome (measured at unit end):** CO-1: predicts the result of two concurrent bookings for the last slot. VE-3: reproduces a lost update. DE-6: picks an isolation level or row lock, with the trade-off.
- **Topics:** lost updates; dirty, non-repeatable and phantom reads; isolation levels; SELECT ... FOR UPDATE; blocking and deadlocks at application depth
- **Prerequisites:** DB-1.2 | **Importance:** Core | **Replaces (v1):** DB-6.3, DB-6.4, DB-6.5

#### DB-1.4 Indexes from query patterns

- **Objective:** Can choose indexes, including column order, from the queries an application runs.
- **The concept (Explain):** An index is a sorted copy of some columns that lets the database skip rows; it costs space and write time.
- **Target skills:** DE-6 to Adapt; VE-6 to Adapt
- **Methods:** Explain → Evaluate → Debug & Validate
- **Outcome (measured at unit end):** DE-6: chooses an index, including column order, for three queries, and says what it costs. VE-6: checks with EXPLAIN that each index is used, including on a query it should not help.
- **Topics:** what an index changes; B-tree indexes; composite index order; constraint-backed versus performance indexes; write cost; other index types (awareness)
- **Prerequisites:** DB-0.7 | **Importance:** Core | **Replaces (v1):** DB-7.1, DB-7.2, DB-7.3, DB-7.4

#### DB-1.5 Query plans and evidence-led tuning

- **Objective:** Can read a basic query plan and improve a slow query one measured change at a time.
- **The concept (Explain):** SQL says what you want; the plan shows how the database will get it.
- **Target skills:** VE-3 to Adapt; VE-5 to Adapt
- **Methods:** Explain → Debug & Validate
- **Outcome (measured at unit end):** VE-3: reads EXPLAIN ANALYZE for a slow query, states one hypothesis, and changes one thing. VE-5: shows the timing and plan before and after, with results unchanged.
- **Topics:** EXPLAIN and EXPLAIN ANALYZE; sequential scan versus index scan; estimated versus actual rows; running ANALYZE safely; one change at a time
- **Prerequisites:** DB-1.4 | **Importance:** Core | **Replaces (v1):** DB-8.1, DB-8.2, DB-8.3, DB-8.4

#### DB-1.6 Migrations and choosing storage

- **Objective:** Can change a schema without losing data meaning, check the change on representative data, and choose the right kind of storage for a need.
- **The concept (Explain):** A migration changes a live schema in small steps that existing data and code can survive.
- **Target skills:** BU-5 to Adapt; VE-6 to Adapt; DE-6 to Adapt
- **Methods:** Explain → Modify → Debug & Validate → Evaluate
- **Outcome (measured at unit end):** BU-5: writes a migration in small reversible steps. VE-6: checks it against representative data, including NULLs and old rows. DE-6: chooses between relational tables, a document store and a vector store for three needs.
- **Topics:** migration tools (Alembic as an example); expand and contract; backfills; migrations versus deploys; testing on representative data; when document, key-value, graph or vector storage fits; pgvector (awareness)
- **Prerequisites:** DB-1.1 | **Importance:** Core | **Replaces (v1):** DB-10.1, DB-10.2, DB-10.3, DB-11.1, DB-11.2

## Skill coverage (target skills, this roadmap)

13 units carry 30 targets: Apply 2, Adapt 28. Skills not listed are trained in the Python, Backend and AI Engineering roadmaps.

| Skill | Units | Highest level |
| --- | --- | --- |
| CO-1 | 3 | Adapt |
| CO-5 | 1 | Adapt |
| CO-6 | 2 | Adapt |
| SP-1 | 1 | Adapt |
| SP-2 | 2 | Adapt |
| SP-3 | 1 | Adapt |
| BU-2 | 2 | Adapt |
| BU-4 | 1 | Adapt |
| BU-5 | 1 | Adapt |
| VE-1 | 1 | Adapt |
| VE-2 | 1 | Adapt |
| VE-3 | 2 | Adapt |
| VE-4 | 1 | Adapt |
| VE-5 | 2 | Adapt |
| VE-6 | 4 | Adapt |
| DE-6 | 5 | Adapt |

## Decisions

1. **Scope, cuts and placement** approved by Asheesh on 2026-10-31 (review "New roadmaps: framework fit and scope").
2. **Wording still to review:** target skills, levels, concept and outcome lines.
3. **Stage builds:** every stage needs one build (owner rule). Not yet written for this roadmap.
