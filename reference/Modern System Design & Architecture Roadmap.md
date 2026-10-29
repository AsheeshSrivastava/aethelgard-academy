## How to use this roadmap

This is a 30-week learning ladder of about 10-11 hours a week. You climb six rungs, and each rung ends with an evidence gate: one piece of portfolio work that proves the skill. You don't climb until the evidence exists.

**Two tracks run in parallel every week:**

1. **Track A, system design (about 7 h):** study 3 h, design exercise 3 h, ADR or review 1 h.
2. **Track B, software and code design (about 3 h):** learn 1 h, then apply 2 h on real code: AI-generated code you review and refactor, or your own RAG repos. Examples use Python.

**Rules:**

- **Free only.** Every resource linked here is free to read or watch. Well-known paid books (_Designing Data-Intensive Applications_, _System Design Interview_, _Release It!_, _Refactoring_) are optional extras if a library has them; each week has a free substitute.
- **No-spend practice.** Run everything locally with Docker, Postgres and Redis, plus GitHub's free tier. For LLM exercises use local models through [Ollama](https://ollama.com) or a provider's free tier, and check the current limits.
- **Spec before code.** Never ask an AI to build what you haven't designed. Your design doc is the prompt.
- **Numbers over adjectives.** "p95 under 800 ms at 20 requests a second", not "fast".
- **Every design gets an ADR** (architecture decision record, one page).
- **Publish at gates, not before.** Drafts stay private; the public repo only gets gate-quality work.
- **The last week of each rung is its evidence week.** If you fall behind, shrink the exercises, never the gate.

## The ladder at a glance

[embed: node/2b3b183d-d296]

Each diamond is a published artifact you must have before starting the next rung; the weeks inside each rung are detailed below.

## Rung 1 (Weeks 1-5): Reason about a system

**You can:** given a feature request, estimate load, design the API and data model, and defend the trade-offs in writing. In code, you can read AI-generated code and tidy it without changing behavior.

**Gate 1 (end of Week 5):** Design doc #1 (URL shortener) plus a refactor case study, published in a public `design-notes` repo.

### Week 1: Networking, HTTP and APIs

- **System:** client/server, DNS, TCP, HTTP, TLS, REST, idempotency, pagination. Read the networking and API sections of the [System Design Primer](https://github.com/donnemartin/system-design-primer) and watch Hussein Nasser's free backend videos on HTTP and TCP. Do: write an OpenAPI spec for a note-taking service with an error format, pagination and an idempotent create (the Swagger editor is free).
- **Code:** why complexity is the enemy: deep vs shallow modules. Watch John Ousterhout's [A Philosophy of Software Design talk](https://www.youtube.com/watch?v=bmSAYlu0NcY). Apply: take one AI-generated function and list three places it is hard to understand.
- **Output:** the OpenAPI file, a one-page note on three API decisions, your three "hard to understand" notes.

### Week 2: Databases and indexes

- **System:** relational model, indexes, query plans, transactions, isolation levels. Work through [Use The Index, Luke](https://use-the-index-luke.com) and the index and transaction chapters of the [PostgreSQL docs](https://www.postgresql.org/docs/). Do: model the note service in Postgres; run `EXPLAIN ANALYZE` on a table of 1M generated rows before and after adding an index.
- **Code:** readable code: naming, small functions, comments that explain why. Read chapter 9 (code review) of [Software Engineering at Google](https://abseil.io/resources/swe-book). Apply: write three characterization tests for one messy function, then refactor it using the free [Refactoring Guru](https://refactoring.guru) catalog (extract function, rename).
- **Output:** schema file, before/after query plan with timings, one refactor with tests staying green.

### Week 3: Caching and back-of-envelope estimation

- **System:** cache-aside, write-through, TTLs, invalidation, CDNs, latency numbers, QPS and storage maths. Use the estimation and cache sections of the System Design Primer. Do: estimate QPS, storage and cache size for a URL shortener at 100M links and 1B reads a month; add a Redis cache (local Docker) and measure the hit rate.
- **Code:** separate decisions from side effects. Apply: split one function that mixes calculation with I/O into a pure function and a thin shell.
- **Output:** an estimation sheet where every number is derived, a cache demo with measured hit rate.

### Week 4: Queues and async work

- **System:** queues vs logs, at-least-once delivery, dead-letter queues, backpressure, retries. Read AWS's [Timeouts, retries and backoff with jitter](https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter/). Do: build a worker with a Redis- or Postgres-based queue; design an email-notification system that survives a 10-minute provider outage.
- **Code:** error handling as design: clear error types, fail fast, no swallowed exceptions (Python's exception docs plus Ousterhout's "define errors out of existence" idea from the talk). Apply: add typed errors to your worker.
- **Output:** a design doc with a failure-mode table (failure, effect, mitigation) and a working retry plus dead-letter demo.

### Week 5: Evidence week, Gate 1

- **System:** design a URL shortener end to end using the template in the Portfolio evidence section: requirements, estimates, API, data model, components, bottlenecks, trade-offs. Timebox a first pass to 90 minutes, then polish. Compare with the System Design Primer's worked examples and list what you missed.
- **Code:** write a refactor case study: pick one AI-generated module, refactor it in 3-5 small commits, and document the smell, the change, and how tests protected you.
- **Output:** **Gate 1.** Design doc #1 with three ADRs, plus the refactor case study, in a public `design-notes` repo with a README index.

## Rung 2 (Weeks 6-10): Design for data and failure

**You can:** choose replication, consistency and async patterns for a feature, and show what happens when each component fails. Your code keeps business logic separate from I/O, so it is testable without a database.

**Gate 2 (end of Week 10):** a public `reliability-lab` repo: queue worker, outbox, retries and circuit breaker, with a failure-mode table and tests that inject failures.

### Week 6: Replication and partitioning

- **System:** leader/follower replication, replication lag, quorums, sharding, hot keys. Watch Martin Kleppmann's free [Distributed Systems lecture series](https://www.youtube.com/playlist?list=PLeKd45zvjcDFUEv_ohr_HdUFe97RItdiB) (lectures on replication and quorums) with the [lecture notes](https://www.cl.cam.ac.uk/teaching/2021/ConcDisSys/dist-sys-notes.pdf). Do: for a bank transfer, a social feed and a shopping cart, write which consistency each needs and why.
- **Code:** ports and adapters. Read Alistair Cockburn's [Hexagonal Architecture](https://alistair.cockburn.us/hexagonal-architecture/) and the first chapters of [Cosmic Python](https://www.cosmicpython.com) (domain model, repository). Apply: write a small domain model in plain Python with no database imports.
- **Output:** a one-page consistency-choices note, and a domain model with unit tests.

### Week 7: Consistency, time and consensus

- **System:** CAP and PACELC, linearizability, eventual consistency, clocks and ordering. Watch the Kleppmann lectures on time, linearizability and eventual consistency; browse a few analyses at [Jepsen](https://jepsen.io) to see how real databases fail. Optional depth: the [MIT 6.5840](https://pdos.csail.mit.edu/6.824/) lecture on Raft.
- **Code:** repository pattern and service layer (Cosmic Python chapters 2 and 4). Apply: put your Week 2 Postgres access behind a repository, with an in-memory fake for tests.
- **Output:** a half-page summary of consensus and consistency in your own words; a repository plus fake with tests.

### Week 8: Transactions, outbox and idempotency

- **System:** ACID, isolation anomalies, why two-phase commit is usually avoided, the [transactional outbox](https://microservices.io/patterns/data/transactional-outbox.html), idempotent consumers. Do: implement an outbox with Postgres and a worker.
- **Code:** unit of work (Cosmic Python chapter 6). Apply: wrap order creation in a unit of work so the order and its outbox message commit together.
- **Output:** a working outbox demo, plus a test that kills the worker mid-run and shows no message is lost or applied twice.

### Week 9: Reliability patterns

- **System:** timeouts, retries with jitter, circuit breakers, bulkheads, rate limiting, load shedding. Read AWS's [Using load shedding to avoid overload](https://aws.amazon.com/builders-library/using-load-shedding-to-avoid-overload/) and the overload and cascading-failure chapters of the free [Google SRE books](https://sre.google/books/). Do: add a timeout, retry and circuit breaker to a service that calls a flaky dependency, and simulate the failure.
- **Code:** testing with fakes and test doubles (chapters 12 and 13 of Software Engineering at Google). Apply: write failure-injection tests using a fake dependency that times out or errors.
- **Output:** a failure-mode table covering every external call, and a demo of the service degrading gracefully.

### Week 10: Evidence week, Gate 2

- **System:** assemble the `reliability-lab` repo: a README with a Mermaid architecture diagram, the failure-mode table, and a "what I would change at 10x" section. Write two new ADRs for choices you made this rung.
- **Code:** layering review. Check that no domain module imports infrastructure, and make that a test using the free [import-linter](https://import-linter.readthedocs.io).
- **Output:** **Gate 2.** A public repo whose failure tests go red when you break a safeguard and green when it works, plus two ADRs.

## Rung 3 (Weeks 11-16): Choose an architecture

**You can:** choose between a monolith, a modular monolith and services for a given context, draw C4 diagrams, define module boundaries, and document the decision. You can enforce those boundaries in code.

**Gate 3 (end of Week 16):** Design doc #2 (payments or ride dispatch) with C4 diagrams, a saga, a failure-mode table, a scaling plan and five or more ADRs, plus a modular-monolith skeleton repo whose architecture tests pass.

### Week 11: Architecture styles and the C4 model

- **System:** monolith, modular monolith, microservices, serverless; coupling and cohesion; why a modular monolith is the default. Read Martin Fowler's [MonolithFirst](https://martinfowler.com/bliki/MonolithFirst.html), the [C4 model](https://c4model.com) site, and the architecture styles in the free [Azure Architecture Center](https://learn.microsoft.com/azure/architecture/patterns/). Do: draw Design doc #1 as C4 context and container diagrams in [Excalidraw](https://excalidraw.com) or [Mermaid](https://mermaid.js.org).
- **Code:** dependency inversion and dependency injection in Python (Cosmic Python chapters 3 and 13). Apply: wire your service from one composition root instead of importing concrete classes everywhere.
- **Output:** two C4 diagrams and an ADR titled "Monolith vs services for this system".

### Week 12: Domain-driven design, the useful 20%

- **System:** bounded contexts, aggregates, domain events, ubiquitous language. Read the relevant pattern summaries in Eric Evans' free [DDD Reference](https://domainlanguage.com/ddd/reference/) (PDF). Do: a one-hour paper event-storming session for an e-commerce checkout, then split it into 4-5 modules.
- **Code:** aggregates and invariants (Cosmic Python chapter 7). Apply: model an `Order` aggregate that enforces two invariants, with tests.
- **Output:** a module-boundary map listing what each module owns and exposes, and the `Order` aggregate.

### Week 13: Events, CQRS and sagas

- **System:** events vs commands, event sourcing and when not to use it, [CQRS](https://martinfowler.com/bliki/CQRS.html), [sagas](https://microservices.io/patterns/data/saga.html), orchestration vs choreography. Do: design an order flow (reserve stock, charge payment, ship) as a saga with compensating steps.
- **Code:** domain events and a message bus (Cosmic Python chapters 8 and 9). Apply: add an in-process event bus to your modular monolith.
- **Output:** a sequence diagram of the happy path and two failure paths, and an ADR on orchestration vs choreography.

### Week 14: Scaling and data architecture

- **System:** read replicas, partitioning, OLTP vs OLAP, search indexes, blob storage, data pipelines. Use the scaling sections of the System Design Primer. Do: scale Design doc #1 by 100x on paper and find what breaks first and the cheapest fix.
- **Code:** refactoring at scale. Read Fowler's [Strangler Fig](https://martinfowler.com/bliki/StranglerFigApplication.html) article and chapter 22 (large-scale changes) of Software Engineering at Google. Apply: refactor one module behind a feature flag, keeping old and new paths side by side.
- **Output:** a three-stage scaling plan (now, 10x, 100x) with the trigger metric for moving to the next stage, and a refactor log.

### Week 15: API contracts and evolution

- **System:** versioning, backward compatibility, schema evolution, contract-first design, webhooks. Read the [Google API Design Guide](https://cloud.google.com/apis/design) and the section on Hyrum's Law in chapter 1 of Software Engineering at Google. Do: design a v1 to v2 change that doesn't break existing clients.
- **Code:** narrow interfaces and information hiding. Rewatch the Ousterhout talk, and listen to his episode of The Pragmatic Engineer podcast on why design matters more as AI writes the low-level code. Apply: audit one module's public surface and cut it by a third.
- **Output:** a versioning ADR and a before/after diff of the API audit.

### Week 16: Evidence week, Gate 3

- **System:** write Design doc #2 for a payments service or ride dispatch, using the template. Include C4 diagrams, a saga, the failure-mode table, a scaling plan and at least five ADRs.
- **Code:** build the modular-monolith skeleton for it: modules, public interfaces, and architecture tests (import-linter) that fail if a module reaches into another's internals.
- **Output:** **Gate 3.** Design doc #2 (5-7 pages) and the skeleton repo, both published.

## Rung 4 (Weeks 17-21): Run it in production

**You can:** instrument, deploy, secure and cost a service, and explain how you would find and fix a failure. Your code has a test strategy and can be refactored safely.

**Gate 4 (end of Week 21):** a production-readiness pack in one repo: a running service with a CI pipeline, an SLO document, a threat model, a cost model, a mock postmortem, and a test and refactor log. Local Docker Compose is enough; no paid hosting is needed.

### Week 17: Observability and SLOs

- **System:** logs, metrics and traces; the golden signals (latency, traffic, errors, saturation); SLIs, SLOs and error budgets. Read the monitoring and SLO chapters of the free [Google SRE books](https://sre.google/books/) and the [OpenTelemetry docs](https://opentelemetry.io/docs/). Do: instrument your Rung 3 skeleton with OpenTelemetry and view traces locally with Jaeger or Grafana; define two SLOs.
- **Code:** structured logging with request IDs, using Python's logging docs and the OpenTelemetry Python instrumentation. Apply: make one request traceable from entry to database.
- **Output:** a service emitting logs, metrics and traces, and an SLO document with targets and alert rules.

### Week 18: CI/CD, containers and deploy strategies

- **System:** Docker, multi-stage builds, CI pipelines, blue-green and canary deploys, feature flags, rollbacks, config via environment ([12-factor app](https://12factor.net)). Read chapters 23 and 24 (CI and CD) of Software Engineering at Google. Do: containerize the service and build a GitHub Actions pipeline (free for public repos) that lints, tests and builds.
- **Code:** test pyramid and flaky tests (chapters 11 and 14 of Software Engineering at Google). Apply: tag tests as unit or integration and split them into pipeline stages.
- **Output:** a working pipeline and a one-page deploy and rollback runbook.

### Week 19: Security and threat modeling

- **System:** authentication vs authorization, OAuth 2.0 and OIDC, secrets, least privilege, multi-tenancy, the [OWASP Top 10](https://owasp.org/www-project-top-ten/), STRIDE. Use the [OWASP Cheat Sheet Series](https://cheatsheetseries.owasp.org). Do: draw a data-flow diagram with trust boundaries, run a STRIDE pass, and list the top five threats.
- **Code:** secure code review of AI output: input validation, parameterized queries, no secrets in code. Apply: run the free scanners [Bandit](https://bandit.readthedocs.io) and [pip-audit](https://pypi.org/project/pip-audit/) on your repo and fix what they find.
- **Output:** a threat model, an ADR on your authn/authz approach, and a scanner report with fixes.

### Week 20: Cost, capacity and performance

- **System:** cost drivers (compute, storage, egress, managed services), capacity planning, load testing. Read the cost optimization pillar of the [AWS Well-Architected Framework](https://aws.amazon.com/architecture/well-architected/). Do: price Design doc #2 at 1x, 10x and 100x with a cloud pricing calculator (free to use); load test one endpoint with [k6](https://grafana.com/docs/k6/) or [Locust](https://locust.io).
- **Code:** measure before optimizing. Profile with Python's built-in cProfile. Apply: find the top hotspot on one slow path, fix it, and record the before/after numbers.
- **Output:** a cost model with stated assumptions, a load-test report, and a profile before/after.

### Week 21: Evidence week, Gate 4

- **System:** write a mock blameless postmortem for a failure you inject into your own service (the SRE book has the format), and assemble the pack with a README that links every artifact.
- **Code:** test-suite health check. Delete tests that only mirror the implementation, add three behavior tests, and write a refactor log summarizing every refactor since Week 5.
- **Output:** **Gate 4.** The production-readiness pack with the test and refactor log.

## Rung 5 (Weeks 22-27): Build AI-native systems

**You can:** design, evaluate, secure and operate a system where an LLM is one component, with measured quality and bounded cost. Your code wraps nondeterministic parts behind testable interfaces.

**Gate 5 (end of Week 27):** Design doc #3 plus a repo with an eval gate in CI, traces for every LLM call, and a red-team report. Use your existing RAG projects as the base.

### Week 22: LLM building blocks

- **System:** tokens and pricing, context windows, structured output, tool calling, streaming, prompt caching, model routing, fallbacks. Read the [Anthropic docs](https://docs.claude.com) and Chip Huyen's free [blog](https://huyenchip.com/blog/); the free [DeepLearning.AI short courses](https://www.deeplearning.ai/short-courses/) fill gaps. Do: build an endpoint with structured output, a timeout and a fallback to a second model, using Ollama or a free tier.
- **Code:** put the LLM client behind an interface with a fake for tests (the same ports-and-adapters pattern as Week 7). Apply: write tests that run with no network.
- **Output:** a working endpoint, a cost-per-request estimate (tokens in, tokens out, retries), and fake-LLM tests.

### Week 23: Retrieval and RAG architecture

- **System:** ingestion pipelines, chunking, embeddings, hybrid search, reranking, metadata filters, citations, index freshness. Read Eugene Yan's [patterns for LLM systems](https://eugeneyan.com) and the docs of an open-source vector option such as [pgvector](https://github.com/pgvector/pgvector) or [Chroma](https://docs.trychroma.com). Do: draw your RAG pipeline as an ingestion path and a query path, with the failure mode of each stage.
- **Code:** pipeline design: small composable stages, config separate from code, idempotent ingestion. Apply: refactor one ingestion script into stages with tests.
- **Output:** a RAG architecture diagram and three ADRs backed by measured retrieval results (chunk size, retriever, reranker), not opinion.

### Week 24: Evals as architecture

- **System:** golden sets, recall@k, MRR, faithfulness, citation accuracy, the limits of LLM-as-judge, regression gates. Read Hamel Husain's free writing on [evals](https://hamel.dev). Do: build a 50-question golden set from real documents and a script that reports the metrics.
- **Code:** testing nondeterministic code: validate structure not wording, fix seeds, use tolerances. Use [pytest](https://docs.pytest.org) and [Hypothesis](https://hypothesis.readthedocs.io). Apply: add tests for parsing and validating LLM output.
- **Output:** a versioned eval set, a metrics script, and a CI check that blocks a change which drops quality below your threshold.

### Week 25: Agents, tools and workflows

- **System:** workflows vs agents, tool design, state and memory, human-in-the-loop, step budgets, MCP. Read Anthropic's [Building effective agents](https://www.anthropic.com/engineering/building-effective-agents) and the [MCP docs](https://modelcontextprotocol.io). Do: build one fixed workflow and one agent for the same task and compare reliability, cost and latency.
- **Code:** tool interfaces: small, typed, well described, least privilege. Apply: define three tools with JSON schemas and input validation.
- **Output:** a comparison table and an ADR, "Workflow or agent for this task", with the measured result. Default to the simpler one that passes your evals.

### Week 26: Safety, guardrails and LLM security

- **System:** prompt injection (direct and indirect), data exfiltration through tools, least-privilege permissions, output validation, PII, rate limits. Read the [OWASP Top 10 for LLM Applications](https://owasp.org/www-project-top-10-for-large-language-model-applications/). Do: red-team your system with 20 adversarial inputs, including instructions hidden inside retrieved documents.
- **Code:** defend in code, not only in the prompt: permission checks, validators, confirmation for risky actions. Apply: implement and test three guardrails.
- **Output:** a red-team report listing each attack, the result and the fix.

### Week 27: Evidence week, Gate 5

- **System:** write Design doc #3 for your AI system: requirements, estimates, architecture, eval results with numbers, threat model, cost model, and a rollout plan for swapping to a newer model (shadow run, eval compare, canary, rollback).
- **Code:** add tracing for every LLM call (inputs, outputs, tokens, latency, cost) through OpenTelemetry or structured logs, and make the eval gate run in CI.
- **Output:** **Gate 5.** Design doc #3 and the repo with eval gate, traces and red-team report.

## Rung 6 (Weeks 28-30): Prove it

**You can:** show your skill to a stranger in ten minutes, and defend your decisions live. No new topics; this rung turns five gates into one portfolio.

**Gate 6 (end of Week 30):** a public portfolio index linking every gate, with two polished design docs, one flagship repo and a recorded walkthrough.

### Week 28: Polish the evidence

- **System:** choose your best two design docs (usually #2 and #3). Rewrite each for a reader with five minutes: lead with the problem, the decision and the numbers; keep diagrams; cut anything that doesn't carry the argument. Add an ADR index.
- **Code:** make the flagship repo easy to run: a README with a run command, an architecture diagram, and an AGENTS.md or CLAUDE.md that encodes your boundaries and rules. Remove dead code.
- **Output:** two polished design docs and a flagship repo someone else can run in five minutes.

### Week 29: Walkthrough and mock reviews

- **System:** record a 10-minute walkthrough of one design with the free [OBS Studio](https://obsproject.com): the problem, two alternatives you rejected and why, the failure modes, the eval numbers. Then run two mock design reviews, with a peer or an AI told to be a skeptical reviewer.
- **Code:** use the review questions you couldn't answer to find weak spots in the code, and fix or document each one.
- **Output:** the recording, plus a written answer to every question you stumbled on.

### Week 30: Publish and plan the next 90 days

- **System:** publish a portfolio page (a GitHub profile README or free GitHub Pages) that links each gate with one line on what it proves. Write one short public post on your biggest lesson.
- **Code:** run a final secret scan, remove private data and keys from every repo, and check licenses of anything you copied.
- **Output:** **Gate 6.** The portfolio index, plus a half-page plan for what to deepen next, chosen from the weakest gate.

## Working with AI coders (every week)

Track B exists so that you can direct AI code instead of just accepting it. Treat its output like a pull request from a fast, tireless junior engineer who sometimes invents things.

**Spec-first workflow:**

1. **Design first:** requirements, constraints, API contract, data model, module boundaries, non-goals.
2. **Encode the rules** in an AGENTS.md or CLAUDE.md per repo: module boundaries, allowed dependencies, testing rules, a "never do" list.
3. **Contract first:** write the OpenAPI or schema yourself; the AI implements against it.
4. **Tests as guardrails:** write or approve the tests before the implementation.
5. **Small slices:** one module or endpoint per request, each reviewed and committed separately.
6. **Review hard**, using the checklist below.

**Review checklist:**

- **Architecture drift:** did it respect module boundaries, or reach into another module's internals?
- **Hidden coupling:** new shared state, global config, cross-module imports not in the design.
- **Failure handling:** timeouts, retries and error paths, or only the happy path?
- **Security:** input validation, authorization on every route, no secrets in code, parameterized queries.
- **Dependencies:** any library you didn't choose? Is it maintained and necessary?
- **Tests:** do they test behavior, or mirror the implementation? Would they fail if the logic broke?
- **Over-engineering:** extra abstractions, unused flexibility, duplicated helpers.

**Habits that compound:** keep a review log (one line per real flaw, plus the rule that would have prevented it, then move good rules into AGENTS.md); ask the AI to critique your design before it implements anything; and ask for alternatives, then pick one and write the ADR yourself.

## Portfolio evidence: what to publish and when

Publish only at a gate. Each piece of evidence states a problem, the decision, the numbers and what you would change, so a reader sees judgment and not just output.

|   |   |   |   |
|---|---|---|---|
|Gate|Week|Evidence|What it proves|
|1|5|Design doc #1 (URL shortener), three ADRs, refactor case study|You can estimate, design an API and data model, and tidy code safely|
|2|10|`reliability-lab` repo with failure-injection tests|You design for failure and keep logic separate from I/O|
|3|16|Design doc #2, modular-monolith skeleton with architecture tests|You choose and enforce an architecture|
|4|21|Production-readiness pack: CI, SLOs, threat model, cost model, postmortem|You can run, secure and cost a service|
|5|27|Design doc #3, eval gate in CI, traces, red-team report|You can build and measure AI systems|
|6|30|Portfolio index, two polished docs, recorded walkthrough|You can communicate and defend your work|

**Every artifact must contain:** requirements and non-goals; scale and cost estimates; a diagram; the failure modes; real measured numbers; and at least one rejected alternative with the reason.

**Never publish:** secrets, private documents, anyone's personal data, or client or employer material.

### Design doc template

```markdown
# <System name> design doc

## 1. Context and goals
- Problem, users, success metrics (with numbers)
- Non-goals

## 2. Requirements
- Functional
- Non-functional (latency, availability, cost, privacy) with targets

## 3. Estimates
- Traffic, storage, token usage, monthly cost

## 4. Architecture
- C4 context and container diagrams
- Data model and API contract
- Key flows (sequence diagrams)

## 5. Failure modes
| Failure | Effect | Detection | Mitigation |

## 6. Quality and evals (AI systems)
- Golden set, metrics, thresholds, regression gate

## 7. Security and privacy
- Trust boundaries, top threats, mitigations

## 8. Rollout and operations
- Deploy plan, rollback, SLOs, dashboards, runbook

## 9. Scaling plan
- Now, 10x, 100x: what breaks first

## 10. Decisions (ADR index)
## 11. Open questions and risks
```

### ADR template

```markdown
# ADR-NNN: <decision title>
- Status: proposed | accepted | superseded by ADR-NNN
- Date:

## Context
What forces and constraints led to this decision?

## Options considered
1. Option A: pros, cons
2. Option B: pros, cons

## Decision
What we chose and the single strongest reason.

## Consequences
What gets easier, what gets harder, what we must monitor.
```

## Free resources and progress checklist

All of these are free to read or watch. Free access can change, so open each link before you rely on it.

|   |   |   |
|---|---|---|
|Resource|Covers|Weeks|
|[System Design Primer](https://github.com/donnemartin/system-design-primer)|Estimation, caching, scaling, worked designs|1, 3, 5, 14|
|[Kleppmann's Distributed Systems lectures](https://www.youtube.com/playlist?list=PLeKd45zvjcDFUEv_ohr_HdUFe97RItdiB) and [notes](https://www.cl.cam.ac.uk/teaching/2021/ConcDisSys/dist-sys-notes.pdf)|Replication, consistency, consensus|6-8|
|[MIT 6.5840](https://pdos.csail.mit.edu/6.824/)|Raft and fault tolerance (optional depth)|7|
|[Use The Index, Luke](https://use-the-index-luke.com) and [PostgreSQL docs](https://www.postgresql.org/docs/)|Indexes, query plans, transactions|2|
|[Jepsen](https://jepsen.io)|Real database failure analyses|7|
|[AWS Builders' Library](https://aws.amazon.com/builders-library/)|Retries, timeouts, load shedding|4, 9|
|[Google SRE books](https://sre.google/books/)|Overload, monitoring, SLOs, postmortems|9, 17, 21|
|[Software Engineering at Google](https://abseil.io/resources/swe-book)|Code review, testing, CI/CD, large-scale changes|2, 9, 14, 15, 18|
|[A Philosophy of Software Design talk](https://www.youtube.com/watch?v=bmSAYlu0NcY) (Ousterhout)|Complexity, deep modules, error design|1, 4, 15|
|[Cosmic Python](https://www.cosmicpython.com)|Repository, service layer, unit of work, events|6-8, 11-13|
|[Refactoring Guru](https://refactoring.guru) and [refactoring.com catalog](https://refactoring.com/catalog/)|Code smells, refactorings|2, 5|
|[Hexagonal Architecture](https://alistair.cockburn.us/hexagonal-architecture/) (Cockburn)|Ports and adapters|6|
|[Martin Fowler's site](https://martinfowler.com) and [microservices.io](https://microservices.io)|Architecture styles, CQRS, sagas, outbox|8, 11, 13, 14|
|[C4 model](https://c4model.com), [Excalidraw](https://excalidraw.com), [Mermaid](https://mermaid.js.org)|Diagrams|11, all gates|
|[DDD Reference](https://domainlanguage.com/ddd/reference/) (Evans, PDF)|Bounded contexts, aggregates|12|
|[Azure Architecture Center](https://learn.microsoft.com/azure/architecture/patterns/)|Cloud design patterns|11, 13|
|[Google API Design Guide](https://cloud.google.com/apis/design)|API versioning and evolution|15|
|[OpenTelemetry](https://opentelemetry.io/docs/) and [12-factor app](https://12factor.net)|Observability, deployment|17, 18|
|[OWASP Cheat Sheets](https://cheatsheetseries.owasp.org) and [Top 10](https://owasp.org/www-project-top-ten/)|Application security|19|
|[AWS Well-Architected](https://aws.amazon.com/architecture/well-architected/), [k6](https://grafana.com/docs/k6/), [Locust](https://locust.io)|Cost, load testing|20|
|[Anthropic docs](https://docs.claude.com), [Chip Huyen's blog](https://huyenchip.com/blog/), [DeepLearning.AI short courses](https://www.deeplearning.ai/short-courses/)|LLM system building blocks|22|
|[Eugene Yan](https://eugeneyan.com), [Hamel Husain](https://hamel.dev)|LLM patterns and evals|23, 24|
|[Building effective agents](https://www.anthropic.com/engineering/building-effective-agents) and [MCP docs](https://modelcontextprotocol.io)|Agents and tools|25|
|[OWASP Top 10 for LLM Applications](https://owasp.org/www-project-top-10-for-large-language-model-applications/)|LLM security|26|
|[ADR GitHub org](https://adr.github.io)|ADR formats and tooling|all|

**Tools (all free):** Python, Docker, Postgres, Redis, [Ollama](https://ollama.com), pytest, Hypothesis, import-linter, Bandit, pip-audit, GitHub Actions free tier, OBS Studio.

### Progress checklist

- Gate 1 (Week 5): Design doc #1, three ADRs, refactor case study
- Gate 2 (Week 10): `reliability-lab` repo with failure-injection tests
- Gate 3 (Week 16): Design doc #2 and modular skeleton with architecture tests
- Gate 4 (Week 21): production-readiness pack and test/refactor log
- Gate 5 (Week 27): Design doc #3, eval gate in CI, red-team report
- Gate 6 (Week 30): portfolio index, two polished docs, recorded walkthrough
- AGENTS.md or CLAUDE.md in every repo, with a growing review log

**If you fall behind:** shrink the exercises and drop optional reading, but never the gate. The written, measured output is what builds the skill and what employers can check.