---
title: Backend Engineering Roadmap v3
created-date: 2026-10-31
status: approved
approved-date: 2026-10-31
version: "3.0"
supersedes: "Backend Engineering Roadmap v2 (kept in reference/ until the app loader moves to v3)"
governed-by: "AI-Era Programming Skills Framework v1 (27 skills); Learning Method v2 with Amendment A1 (2026-10-31)"
roadmap-role: "Spine roadmap (Python, then Backend, then AI Engineering)"
primary-framework: FastAPI
primary-language: Python
ai-involvement: collaborative
ai-provider: Claude
tags:
  - "#claude"
---

> [!info] Provenance
> Made with Claude on 2026-10-31 at Asheesh's direction from Backend Engineering Roadmap v2 (approved 2026-10-18). **Asheesh approved on 2026-10-31 slotting the Networking and Database units into this path.** Only the path order (Table 1) and the named prerequisites marked "Changed in v3" differ from v2; every Backend unit's targets, Methods, concept and outcome are v2 text unchanged.

# Backend Engineering Roadmap v3

## What changed from v2

- **Networking and Database units are slotted into the path.** NET-0.1 to NET-0.6 open the course, before BE-0.1. DB-0.1 to DB-1.6 come before BE-6.1, where persistence starts. Table 1 now lists the whole path: 79 Backend units and 19 slotted units (98 in all).
- **The link pass promised in v2 is done.** 28 prerequisites that named a whole roadmap now name a unit: in Networking v2, Database v2, Software Design v2 and Git v2, or in Python v4 for the OS / Process topics that were folded into Python. Each says "Changed in v3".
- **Nothing else changed.** Backend units keep their v2 targets, Methods, concepts and outcomes. The whole path (Python v4, the slotted units, Backend v3 and AI Engineering v2) passes the entry rule and the one-rung rule of Learning Method Amendment A1, checked by script on 2026-10-31.

## What changed from v1 (in v2)

- **Each unit has one to four target skills**, each with a goal level, taken from the Framework's 27 skills (the old five competencies are gone). Skills not listed come up only as part of the work.
- **Each unit has a one-line concept** that Explain teaches and the CO-6 check tests, a **Methods** list (Explain first) and an **Outcome** line saying what is measured when the unit ends.
- **8 new units** fill gaps: BE-1.6, BE-2.4, BE-2.5, BE-3.5, BE-7.6, BE-5.5, BE-8.5, BE-12.6.
- **Testing and logging are taught earlier** (IDs unchanged): BE-11.1 right after BE-2.5, BE-11.2 after BE-4.2, BE-13.1 after BE-4.3, BE-11.4 after BE-5.4, BE-11.3 after BE-6.3. A learner now has a check for each kind of code right after writing it, instead of after 60 units of building. BE-5.5, BE-7.6 and BE-1.6 sit later than their number because they need earlier units.
- **Goal levels** follow v1 (nothing requires Own by default; BE-14.3 stays Understand), with Own set only where Asheesh approved it: **BE-17.2** (BU-3) and **BE-17.4** (VE-3, VE-4).
- **BE-17.5 now ends in small pull requests**, each with a description and a failing-then-passing check (BU-5).
- **Python entry point:** a learner should have finished Python through Stage 11 before BE-2.1 for typed contracts and models (PY-7.6), logging and pytest (PY-9.2, PY-9.3), environments and dependencies (PY-10.x) and async (PY-11.2, PY-11.3). Units name the one they need as "soft:".
- **Other roadmaps are named only where a unit needs them.** The "link:" and "soft:" notes carried over from v1 stay as written; named prerequisite units in Networking, Database, Software Design, OS and Git are added in a link pass after those roadmaps are upgraded.
- **Skill practice is balanced** across the roadmap (see the coverage table). The old gaps for DE-2, CO-2, SP-4, VE-5, BU-2, BU-5, CO-1 and CO-6 are closed.
- Existing unit IDs never change; the sequence below is the order. The old Stage numbers are kept as labels.

## Scope and boundaries (kept from v1, shortened)

**Purpose.** The backend capability to build, read, debug, test, secure, operate and evolve a backend service while understanding the responsibilities and failure boundaries involved. It aims at backend capability for software and AI engineering, not at becoming a platform specialist before AI Engineering begins.

**This roadmap owns:** the service mental model; API and resource design; routing, binding and validation; response contracts; error translation; dependency injection use; service and application layer design; persistence integration (sessions, ORM, repositories, transaction boundaries in service flows); external API clients; authentication integration and authorization; async and blocking behaviour in services; lifecycle and resource management; in-process background work and durable-job recognition; application caching; pagination and rate or resource limits; middleware and CORS configuration; backend testing; API security; logging, tracing, metrics and health checks; resilience patterns; backend project structure; server and runtime fundamentals.

**Other roadmaps own:** Networking / Web (HTTP semantics, DNS, TCP/TLS, origin, proxies); Python (syntax, exceptions, typing, async mechanics, testing mechanics, tooling); Software Design (responsibility allocation, patterns, SOLID); Database / SQL (modelling, SQL, transactions and isolation, indexes, schema evolution); AI Engineering (model semantics, RAG, tool calling, agents, AI evaluation); System Architecture (whole-system decomposition, distributed design); Infrastructure / Ops (containers in depth, CI/CD, orchestration, cloud). Backend owns how those are applied in a service.

**Outside default scope:** deep Nginx administration, Kubernetes, Terraform, distributed consensus, Kafka internals, service mesh, advanced microservices, database administration, DBMS internals, frontend engineering, a full OAuth/OIDC provider, cryptography internals, penetration testing, advanced SRE, cloud certification breadth, high-scale system design before evidence demands it.

**Anti-bloat rule.** The roadmap is broad; a learner's path is narrow. For example, "a notes API with login" needs the contract, models, persistence, auth and tests, not async, jobs or deployment. Follow the units the current objective needs.

**Lock rule (carried over).** Do not revise the terrain because a framework adds a feature or a tutorial changes fashion. Ask: is this a durable backend capability, or only today's mechanism for one?

## Table 1: path sequence, target skills and methods

Networking (NET) and Database (DB) units are slotted in; their details are in their own roadmaps.

| # | Unit | Stage | Targets (goal level) | Methods |
| --- | --- | --- | --- | --- |
| 1 | NET-0.1 Tracing a request: URL, DNS, IP and ports *(Networking v2)* | NET 0 | CO-2 (Adapt), CO-5 (Adapt) | Explain → Trace |
| 2 | NET-0.2 TCP connections, reuse and pooling *(Networking v2)* | NET 0 | CO-6 (Adapt), DE-6 (Adapt) | Explain → Evaluate |
| 3 | NET-0.3 TLS and HTTPS *(Networking v2)* | NET 0 | CO-6 (Adapt), VE-4 (Adapt) | Explain → Debug & Validate |
| 4 | NET-0.4 Reading raw HTTP messages and headers *(Networking v2)* | NET 0 | CO-3 (Adapt), VE-4 (Adapt) | Explain → Trace → Debug & Validate |
| 5 | NET-0.5 Proxies, gateways, load balancers and CDNs *(Networking v2)* | NET 0 | CO-5 (Adapt), DE-4 (Adapt) | Explain → Trace → Direct |
| 6 | NET-0.6 Locating timeouts and failures across layers *(Networking v2)* | NET 0 | VE-3 (Adapt), VE-4 (Adapt) | Explain → Debug & Validate |
| 7 | BE-0.1 Trace a Request Through a Backend Service | 0 | CO-2 (Apply), CO-5 (Apply), SP-3 (Apply), DE-2 (Apply) | Explain → Trace → Decompose → Direct |
| 8 | BE-0.2 Distinguish Transport, Application, Domain, and Persistence Concerns | 0 | SP-3 (Adapt), CO-6 (Adapt), DE-1 (Adapt), DE-6 (Adapt) | Explain → Decompose → Evaluate |
| 9 | BE-1.1 Model Backend Operations as Clear API Resources/Actions | 1 | SP-1 (Adapt), SP-2 (Adapt), SP-3 (Adapt), DE-6 (Adapt) | Explain → Specify → Decompose → Evaluate |
| 10 | BE-1.2 Select HTTP Methods and Status Codes Consistently | 1 | CO-1 (Apply), CO-4 (Apply), DE-1 (Apply), DE-4 (Apply) | Explain → Predict → Evaluate → Direct |
| 11 | BE-1.3 Design Path, Query, Header, and Body Inputs Deliberately | 1 | SP-2 (Apply), BU-1 (Apply), BU-2 (Apply) | Explain → Specify → Modify |
| 12 | BE-1.4 Design Pagination for Collection Endpoints | 1 | SP-1 (Apply), BU-1 (Apply), DE-6 (Apply) | Explain → Specify → Modify → Evaluate |
| 13 | BE-1.5 Evolve API Contracts Without Accidental Breakage | 1 | SP-1 (Apply), SP-4 (Apply), DE-1 (Apply), DE-6 (Apply) | Explain → Specify → Evaluate |
| 14 | BE-2.1 Implement FastAPI Routes and Parameter Binding | 2 | CO-1 (Apply), BU-1 (Apply), BU-3 (Apply), VE-4 (Apply) | Explain → Predict → Modify → Build → Debug & Validate |
| 15 | BE-2.2 Define Request and Response Models as Explicit Contracts | 2 | SP-2 (Adapt), BU-2 (Adapt), BU-4 (Adapt), DE-1 (Adapt) | Explain → Specify → Modify → Evaluate |
| 16 | BE-2.3 Handle Validation Failures Deliberately | 2 | VE-1 (Adapt), VE-6 (Adapt), DE-1 (Adapt) | Explain → Debug & Validate → Evaluate |
| 17 | BE-2.4 Read and use the generated OpenAPI contract **(new)** | 2 | BU-3 (Apply), CO-3 (Apply), DE-4 (Apply) | Explain → Build → Direct |
| 18 | BE-2.5 Accept and serve files **(new)** | 2 | BU-3 (Apply), VE-6 (Apply), DE-5 (Apply) | Explain → Build → Debug & Validate → Direct |
| 19 | BE-11.1 Separate Unit, Service, API, and Integration Tests by Failure Boundary *(moved)* | 11 | SP-3 (Adapt), DE-1 (Adapt), DE-6 (Adapt) | Explain → Decompose → Evaluate |
| 20 | BE-3.1 Use Dependency Injection for Shared Request/Application Concerns | 3 | BU-1 (Apply), BU-3 (Apply), DE-4 (Apply), CO-6 (Apply) | Explain → Modify → Build → Direct |
| 21 | BE-3.2 Avoid Dependency Injection as a Generic Service Locator | 3 | CO-3 (Adapt), DE-2 (Adapt), DE-3 (Adapt), DE-6 (Adapt) | Explain → Direct → Evaluate |
| 22 | BE-3.3 Move Application Behavior Out of Route Handlers | 3 | SP-3 (Adapt), BU-1 (Adapt), BU-4 (Adapt), BU-5 (Adapt) | Explain → Decompose → Modify |
| 23 | BE-3.4 Design Backend Dependency Flow | 3 | SP-3 (Adapt), BU-1 (Adapt), BU-4 (Adapt), CO-5 (Adapt) | Explain → Decompose → Modify |
| 24 | BE-3.5 Configuration per environment **(new)** | 3 | BU-3 (Apply), BU-5 (Apply), DE-4 (Apply) | Explain → Build → Modify → Direct |
| 25 | BE-4.1 Separate Domain/Application Errors from HTTP Errors | 4 | SP-2 (Adapt), BU-1 (Adapt), BU-2 (Adapt), DE-1 (Adapt) | Explain → Specify → Modify → Evaluate |
| 26 | BE-4.2 Map Failures to Stable Client-Facing Error Contracts | 4 | VE-1 (Apply), VE-6 (Apply), DE-1 (Apply), DE-5 (Apply) | Explain → Debug & Validate → Evaluate → Direct |
| 27 | BE-11.2 Test API Contracts and Failure Responses *(moved)* | 11 | BU-3 (Adapt), VE-1 (Adapt), VE-6 (Adapt) | Explain → Build → Debug & Validate |
| 28 | BE-4.3 Distinguish Expected Failures from Programmer Defects | 4 | VE-2 (Adapt), VE-4 (Adapt), VE-5 (Adapt), DE-1 (Adapt) | Explain → Debug & Validate → Evaluate |
| 29 | BE-13.1 Emit Structured, Contextual Backend Logs *(moved)* | 13 | BU-1 (Apply), BU-2 (Apply), BU-3 (Apply), DE-1 (Apply) | Explain → Modify → Build → Evaluate |
| 30 | BE-5.1 Build a Typed External API Client Boundary | 5 | SP-3 (Adapt), BU-3 (Adapt), DE-3 (Adapt), DE-6 (Adapt) | Explain → Decompose → Build → Direct → Evaluate |
| 31 | BE-5.2 Configure Timeouts Explicitly | 5 | VE-5 (Apply), VE-6 (Apply), DE-4 (Apply), BU-5 (Apply) | Explain → Debug & Validate → Direct → Modify |
| 32 | BE-5.3 Apply Retries Only to Suitable Failures/Operations | 5 | SP-1 (Adapt), VE-2 (Adapt), VE-6 (Adapt), DE-1 (Adapt) | Explain → Specify → Debug & Validate → Evaluate |
| 33 | BE-5.4 Validate and Distrust Third-Party API Responses | 5 | BU-1 (Adapt), VE-1 (Adapt), VE-6 (Adapt), DE-5 (Adapt) | Explain → Modify → Debug & Validate → Direct |
| 34 | BE-11.4 Test External-Service Failures Without Expensive Real Calls *(moved)* | 11 | BU-1 (Adapt), BU-3 (Adapt), VE-1 (Adapt), VE-6 (Adapt) | Explain → Modify → Build → Debug & Validate |
| 35 | DB-0.1 Why databases, and the relational model *(Database v2)* | DB 0 | CO-6 (Apply), DE-6 (Apply) | Explain → Evaluate |
| 36 | DB-0.2 Keys and relationships *(Database v2)* | DB 0 | SP-2 (Adapt), CO-5 (Adapt) | Explain → Specify |
| 37 | DB-0.3 Constraints and integrity violations *(Database v2)* | DB 0 | VE-4 (Adapt), VE-6 (Adapt) | Explain → Debug & Validate |
| 38 | DB-0.4 SELECT, NULL and safe writes *(Database v2)* | DB 0 | CO-1 (Adapt), VE-6 (Adapt) | Explain → Predict → Debug & Validate |
| 39 | DB-0.5 Joins and join bugs *(Database v2)* | DB 0 | CO-1 (Adapt), VE-2 (Adapt), BU-2 (Adapt) | Explain → Predict → Modify → Debug & Validate |
| 40 | DB-0.6 Aggregation with GROUP BY and HAVING *(Database v2)* | DB 0 | BU-2 (Adapt), VE-1 (Adapt) | Explain → Modify → Debug & Validate |
| 41 | DB-0.7 Subqueries and CTEs *(Database v2)* | DB 0 | SP-3 (Adapt), BU-4 (Adapt) | Explain → Decompose → Modify |
| 42 | DB-1.1 Schema design and normalisation *(Database v2)* | DB 1 | SP-1 (Adapt), SP-2 (Adapt), DE-6 (Adapt) | Explain → Specify → Evaluate |
| 43 | DB-1.2 Transactions and ACID *(Database v2)* | DB 1 | CO-6 (Adapt), VE-5 (Adapt) | Explain → Debug & Validate |
| 44 | DB-1.3 Concurrency anomalies, isolation and locks *(Database v2)* | DB 1 | CO-1 (Adapt), VE-3 (Adapt), DE-6 (Adapt) | Explain → Predict → Debug & Validate → Evaluate |
| 45 | DB-1.4 Indexes from query patterns *(Database v2)* | DB 1 | DE-6 (Adapt), VE-6 (Adapt) | Explain → Evaluate → Debug & Validate |
| 46 | DB-1.5 Query plans and evidence-led tuning *(Database v2)* | DB 1 | VE-3 (Adapt), VE-5 (Adapt) | Explain → Debug & Validate |
| 47 | DB-1.6 Migrations and choosing storage *(Database v2)* | DB 1 | BU-5 (Adapt), VE-6 (Adapt), DE-6 (Adapt) | Explain → Modify → Debug & Validate → Evaluate |
| 48 | BE-6.1 Understand ORM Models as Persistence Mappings, Not Domain Truth | 6 | CO-3 (Apply), CO-6 (Apply), DE-1 (Apply), DE-2 (Apply) | Explain → Evaluate → Direct |
| 49 | BE-6.2 Manage Database Session/Connection Lifecycle per Application Operation | 6 | BU-1 (Adapt), BU-3 (Adapt), VE-3 (Adapt), VE-5 (Adapt) | Explain → Modify → Build → Debug & Validate |
| 50 | BE-6.3 Coordinate Application Transaction Boundaries | 6 | SP-2 (Adapt), BU-1 (Adapt), DE-6 (Adapt), VE-1 (Adapt) | Explain → Specify → Modify → Evaluate → Debug & Validate |
| 51 | BE-1.6 Make write endpoints safe to repeat **(new)** | 1 | SP-1 (Adapt), SP-2 (Adapt), VE-1 (Adapt), VE-6 (Adapt) | Explain → Specify → Debug & Validate |
| 52 | BE-11.3 Test Persistence Behavior with Controlled Database State *(moved)* | 11 | BU-3 (Adapt), VE-1 (Adapt), VE-2 (Adapt), DE-6 (Adapt) | Explain → Build → Debug & Validate → Evaluate |
| 53 | BE-6.4 Use Repositories/Data-Access Abstractions Only Where They Clarify Ownership | 6 | SP-3 (Apply), BU-4 (Apply), DE-3 (Apply), DE-6 (Apply) | Explain → Decompose → Modify → Direct → Evaluate |
| 54 | BE-6.5 Diagnose Persistence Failures Across Backend and Database Boundaries | 6 | SP-3 (Adapt), VE-3 (Adapt), VE-4 (Adapt), CO-2 (Adapt) | Explain → Decompose → Debug & Validate → Trace |
| 55 | BE-7.1 Distinguish Authentication from Authorization | 7 | CO-3 (Apply), CO-4 (Apply) | Explain |
| 56 | BE-7.2 Implement Token-Based Authentication at Application Depth | 7 | BU-1 (Apply), BU-3 (Apply), VE-1 (Apply), DE-5 (Apply) | Explain → Modify → Build → Debug & Validate → Direct |
| 57 | BE-7.3 Handle Passwords and Secrets Safely at Application Depth | 7 | BU-3 (Apply), DE-1 (Apply), DE-5 (Apply), DE-2 (Apply) | Explain → Build → Evaluate → Direct |
| 58 | BE-5.5 Receive a webhook safely **(new)** | 5 | BU-3 (Adapt), VE-6 (Adapt), DE-5 (Adapt), CO-3 (Adapt) | Explain → Build → Debug & Validate → Direct |
| 59 | BE-7.4 Enforce Function/Role-Level Authorization | 7 | BU-1 (Adapt), VE-1 (Adapt), VE-2 (Adapt), DE-5 (Adapt) | Explain → Modify → Debug & Validate → Direct |
| 60 | BE-7.5 Enforce Object-Level Authorization | 7 | SP-1 (Adapt), VE-2 (Adapt), VE-6 (Adapt), DE-5 (Adapt) | Explain → Specify → Debug & Validate → Direct |
| 61 | BE-8.1 Choose def versus async def from Workload Behavior | 8 | CO-3 (Adapt), CO-4 (Adapt), DE-1 (Adapt), DE-6 (Adapt) | Explain → Evaluate |
| 62 | BE-8.2 Avoid Blocking the Event Loop | 8 | VE-4 (Adapt), VE-3 (Adapt), VE-5 (Adapt), DE-6 (Adapt) | Explain → Debug & Validate → Evaluate |
| 63 | BE-8.3 Initialize and Clean Up Shared Application Resources with Lifespan | 8 | BU-1 (Adapt), BU-3 (Adapt), VE-3 (Adapt), DE-1 (Adapt) | Explain → Modify → Build → Debug & Validate → Evaluate |
| 64 | BE-8.4 Reason About Multi-Process Resource Duplication | 8 | CO-1 (Adapt), CO-5 (Apply), CO-2 (Apply), DE-1 (Apply) | Explain → Predict → Trace → Evaluate |
| 65 | BE-8.5 Stream a response **(new)** | 8 | BU-3 (Adapt), VE-6 (Adapt), DE-6 (Adapt), DE-4 (Adapt) | Explain → Build → Debug & Validate → Evaluate → Direct |
| 66 | BE-9.1 Use In-Process Background Tasks for Small Non-Critical Work | 9 | BU-1 (Apply), BU-3 (Apply), DE-1 (Apply), BU-5 (Apply) | Explain → Modify → Build → Evaluate |
| 67 | BE-9.2 Recognize When Durable Job Processing Is Required | 9 | SP-1 (Apply), SP-4 (Apply), DE-6 (Apply), DE-2 (Apply) | Explain → Specify → Evaluate → Direct |
| 68 | BE-9.3 Identify Safe Application Cache Opportunities | 9 | SP-1 (Adapt), SP-2 (Adapt), VE-3 (Adapt), DE-6 (Adapt) | Explain → Specify → Debug & Validate → Evaluate |
| 69 | BE-9.4 Avoid Using Cache as Unexamined Persistent Truth | 9 | CO-1 (Apply), CO-6 (Apply), VE-2 (Apply), VE-6 (Apply) | Explain → Predict → Debug & Validate |
| 70 | BE-10.1 Use Middleware for True Request-Wide Concerns | 10 | BU-3 (Apply), BU-1 (Apply), BU-4 (Apply), DE-3 (Apply) | Explain → Build → Modify → Direct |
| 71 | BE-10.2 Reason About Middleware Ordering | 10 | CO-1 (Adapt), CO-2 (Apply), VE-3 (Apply) | Explain → Predict → Trace → Debug & Validate |
| 72 | BE-10.3 Configure CORS from Explicit Origin Requirements | 10 | BU-1 (Apply), DE-4 (Apply), DE-5 (Apply) | Explain → Modify → Direct |
| 73 | BE-7.6 Cookie sessions and CSRF awareness **(new)** | 7 | CO-6 (Apply), SP-4 (Apply), DE-5 (Apply) | Explain → Specify → Direct |
| 74 | BE-12.1 Audit Object and Function Authorization Boundaries | 12 | VE-2 (Adapt), VE-6 (Adapt), DE-5 (Adapt) | Explain → Debug & Validate → Direct |
| 75 | BE-12.2 Prevent Excessive Data Exposure and Unsafe Mass Assignment | 12 | SP-2 (Adapt), BU-2 (Adapt), VE-6 (Adapt), DE-3 (Adapt) | Explain → Specify → Modify → Debug & Validate → Direct |
| 76 | BE-12.3 Control Resource Consumption at API Boundaries | 12 | CO-4 (Apply), SP-4 (Apply), DE-5 (Apply), DE-6 (Apply) | Explain → Specify → Direct → Evaluate |
| 77 | BE-12.4 Prevent Unsafe Server-Side Fetching | 12 | SP-1 (Apply), VE-5 (Apply), VE-6 (Apply), DE-5 (Apply) | Explain → Specify → Debug & Validate → Direct |
| 78 | BE-12.5 Remove Unsafe Debug/Test/Configuration Exposure | 12 | VE-2 (Adapt), VE-6 (Adapt), DE-1 (Adapt), DE-5 (Adapt) | Explain → Debug & Validate → Evaluate → Direct |
| 79 | BE-12.6 Check a package before you add it **(new)** | 12 | DE-4 (Adapt), DE-1 (Adapt), DE-5 (Adapt) | Explain → Direct → Evaluate |
| 80 | BE-13.2 Correlate a Request Across Backend Boundaries | 13 | SP-3 (Adapt), VE-3 (Adapt), VE-4 (Adapt), CO-2 (Adapt) | Explain → Decompose → Debug & Validate → Trace |
| 81 | BE-13.3 Explain Logs, Metrics, and Traces as Different Signals | 13 | CO-6 (Apply), DE-4 (Apply), DE-2 (Apply), CO-5 (Apply) | Explain → Direct |
| 82 | BE-13.4 Define Useful Backend Health and Readiness Checks | 13 | SP-2 (Apply), SP-4 (Apply), DE-1 (Apply) | Explain → Specify → Evaluate |
| 83 | BE-14.1 Use Timeout, Retry, and Backoff as a Coordinated Policy | 14 | VE-3 (Adapt), VE-6 (Adapt), DE-1 (Adapt), DE-6 (Adapt) | Explain → Debug & Validate → Evaluate |
| 84 | BE-14.2 Apply Fallbacks Only When Semantically Safe | 14 | SP-1 (Adapt), SP-4 (Adapt), DE-1 (Adapt), DE-6 (Adapt) | Explain → Specify → Evaluate |
| 85 | BE-14.3 Recognize Circuit-Breaker / Bulkhead Use Cases at Awareness Depth | 14 | CO-4 (Understand), CO-6 (Understand), DE-6 (Understand), DE-2 (Understand) | Explain → Evaluate → Direct |
| 86 | BE-15.1 Organize a Multi-File FastAPI Backend Around Responsibilities | 15 | SP-3 (Adapt), BU-1 (Adapt), BU-4 (Adapt), DE-6 (Adapt) | Explain → Decompose → Modify → Evaluate |
| 87 | BE-15.2 Avoid God Modules and Accidental Layering | 15 | DE-1 (Adapt), DE-6 (Adapt), BU-4 (Adapt), CO-5 (Adapt) | Explain → Evaluate → Modify |
| 88 | BE-15.3 Keep Framework and Infrastructure Details at Appropriate Boundaries | 15 | SP-3 (Adapt), BU-1 (Adapt), BU-4 (Adapt), DE-1 (Adapt) | Explain → Decompose → Modify → Evaluate |
| 89 | BE-16.1 Distinguish Development Server from Production Runtime | 16 | CO-4 (Apply), DE-1 (Apply), DE-4 (Apply), DE-2 (Apply) | Explain → Evaluate → Direct |
| 90 | BE-16.2 Reason About Worker Processes and Memory Duplication | 16 | CO-1 (Apply), CO-4 (Apply), CO-5 (Apply), DE-6 (Apply) | Explain → Predict → Evaluate |
| 91 | BE-16.3 Run One-Time Startup Operations Safely | 16 | SP-1 (Apply), DE-1 (Apply), BU-5 (Apply) | Explain → Specify → Evaluate → Modify |
| 92 | BE-16.4 Treat Application Processes as Disposable Runtime Units | 16 | CO-3 (Apply), CO-6 (Apply), DE-1 (Apply) | Explain → Evaluate |
| 93 | BE-17.1 Design a Backend Service from Requirements | 17 | SP-1 (Adapt), SP-2 (Adapt), SP-3 (Adapt), DE-3 (Adapt) | Explain → Specify → Decompose → Direct |
| 94 | BE-17.2 Implement the Service with Clear Boundaries | 17 | BU-2 (Adapt), BU-3 (Own), BU-5 (Adapt), DE-3 (Adapt) | Explain → Modify → Build → Direct |
| 95 | BE-17.3 Test Security, Failure, and Persistence Paths | 17 | BU-3 (Adapt), VE-1 (Adapt), VE-2 (Adapt), VE-6 (Adapt) | Explain → Build → Debug & Validate |
| 96 | BE-17.4 Diagnose a Runtime Incident from Evidence | 17 | CO-2 (Adapt), VE-3 (Own), VE-4 (Own), SP-3 (Adapt) | Explain → Trace → Debug & Validate → Decompose |
| 97 | BE-17.5 Modify the Existing Service Safely Under a Requirement Change | 17 | BU-1 (Adapt), BU-5 (Adapt), VE-1 (Adapt), VE-5 (Adapt) | Explain → Modify → Debug & Validate |
| 98 | BE-17.6 Integrate Backend Capability into an AI Application Without Claim Leakage | 17 | SP-3 (Adapt), BU-3 (Adapt), DE-3 (Adapt), DE-5 (Adapt) | Explain → Decompose → Build → Direct |

## Table 2: stage, unit and topics

| Stage | Unit | Topics |
| --- | --- | --- |
| 0 | BE-0.1 Trace a Request Through a Backend Service | request flow; server, routing, validation, service, persistence, external call, response; boundaries and what crosses them |
|  | BE-0.2 Distinguish Transport, Application, Domain, and Persistence Concerns | transport, application, domain and persistence concerns; fat route functions; where each belongs |
| 1 | BE-1.1 Model Backend Operations as Clear API Resources/Actions | resources and actions; RPC versus REST trade-offs; naming; requirement to endpoint list |
|  | BE-1.2 Select HTTP Methods and Status Codes Consistently | GET, POST, PUT, PATCH, DELETE; safe and idempotent; status code classes; RFC 9110 |
|  | BE-1.3 Design Path, Query, Header, and Body Inputs Deliberately | path, query, header and body inputs; identifiers; filters; control parameters; contract wording |
|  | BE-1.4 Design Pagination for Collection Endpoints | limits and offsets; cursors; consistency while data changes; bounded responses |
|  | BE-1.5 Evolve API Contracts Without Accidental Breakage | additive versus breaking changes; deprecation; versioning options; client compatibility |
| 2 | BE-2.1 Implement FastAPI Routes and Parameter Binding | route handlers; path, query, header and body binding; type hints; 422 responses |
|  | BE-2.2 Define Request and Response Models as Explicit Contracts | Pydantic models; required and optional fields; nesting; serialisation; response shape; not returning persistence models |
|  | BE-2.3 Handle Validation Failures Deliberately | schema versus business validation; client-facing errors; not hiding defects |
|  | BE-2.4 Read and use the generated OpenAPI contract | OpenAPI; /docs; schemas; examples; descriptions; response models; contract review |
|  | BE-2.5 Accept and serve files | multipart uploads; size and type limits; file names; storage location; streaming downloads |
| 11 | BE-11.1 Separate Unit, Service, API, and Integration Tests by Failure Boundary | unit, service, API and integration tests; boundaries; over-mocking |
| 3 | BE-3.1 Use Dependency Injection for Shared Request/Application Concerns | Depends; yield dependencies; request scope; shared concerns; sub-dependencies |
|  | BE-3.2 Avoid Dependency Injection as a Generic Service Locator | useful versus hidden dependencies; service locator risk; readability |
|  | BE-3.3 Move Application Behavior Out of Route Handlers | thin handlers; service functions; extract-and-verify; unchanged responses |
|  | BE-3.4 Design Backend Dependency Flow | dependency direction; circular imports; inversion; layering |
|  | BE-3.5 Configuration per environment | environment variables; typed settings; defaults; required values; test settings; no secrets in source |
| 4 | BE-4.1 Separate Domain/Application Errors from HTTP Errors | domain errors; translation at the boundary; exception handlers |
|  | BE-4.2 Map Failures to Stable Client-Facing Error Contracts | status codes; error bodies; stable error shape; no stack traces or secrets |
| 11 | BE-11.2 Test API Contracts and Failure Responses | TestClient; status codes; schemas; validation failures; auth; error contracts |
| 4 | BE-4.3 Distinguish Expected Failures from Programmer Defects | expected failures versus defects; broad except; preserving tracebacks |
| 13 | BE-13.1 Emit Structured, Contextual Backend Logs | structured logs; request IDs; log levels; avoiding secrets; noise |
| 5 | BE-5.1 Build a Typed External API Client Boundary | client class; typed payload mapping; provider details in one place; SDK versus own client |
|  | BE-5.2 Configure Timeouts Explicitly | connect, read, write and pool timeouts; failing fast; httpx docs |
|  | BE-5.3 Apply Retries Only to Suitable Failures/Operations | idempotency; retryable failures; retry budget; response codes |
|  | BE-5.4 Validate and Distrust Third-Party API Responses | validating upstream payloads; failing predictably; trust boundary |
| 11 | BE-11.4 Test External-Service Failures Without Expensive Real Calls | fakes; dependency overrides; timeout, malformed and upstream-error tests; retry behaviour |
| 6 | BE-6.1 Understand ORM Models as Persistence Mappings, Not Domain Truth | ORM models; API schemas; domain concepts; separate model types |
|  | BE-6.2 Manage Database Session/Connection Lifecycle per Application Operation | session per request; commit and rollback; release on error; pool exhaustion |
|  | BE-6.3 Coordinate Application Transaction Boundaries | transaction boundaries; rollback; unit of work; partial failure |
| 1 | BE-1.6 Make write endpoints safe to repeat | idempotency keys; storing results; duplicate detection; concurrent repeats; key lifetime |
| 11 | BE-11.3 Test Persistence Behavior with Controlled Database State | test database; rollback fixtures; fakes versus real; controlled state |
| 6 | BE-6.4 Use Repositories/Data-Access Abstractions Only Where They Clarify Ownership | repositories; data-access ownership; indirection cost |
|  | BE-6.5 Diagnose Persistence Failures Across Backend and Database Boundaries | validation errors; detached instances; constraint violations; transaction failures; database availability |
| 7 | BE-7.1 Distinguish Authentication from Authorization | identity versus permission; where each check sits |
|  | BE-7.2 Implement Token-Based Authentication at Application Depth | token-based authentication; validation; expiry; audience; established libraries |
|  | BE-7.3 Handle Passwords and Secrets Safely at Application Depth | password hashing; secret storage; signing keys; no secrets in source |
| 5 | BE-5.5 Receive a webhook safely | signature verification; quick acknowledgement; idempotent processing; replays; retries from the sender |
| 7 | BE-7.4 Enforce Function/Role-Level Authorization | role checks; permission requirements; 403; not relying on the frontend |
|  | BE-7.5 Enforce Object-Level Authorization | object-level authorization; ownership checks; IDOR |
| 8 | BE-8.1 Choose def versus async def from Workload Behavior | sync versus async endpoints; blocking behaviour; I/O waiting; cargo-cult async |
|  | BE-8.2 Avoid Blocking the Event Loop | event loop blocking; async clients; thread offload; measuring latency |
|  | BE-8.3 Initialize and Clean Up Shared Application Resources with Lifespan | lifespan; connection pools; shared clients; cleanup |
|  | BE-8.4 Reason About Multi-Process Resource Duplication | worker processes; in-memory state; duplication; shared versus per-process |
|  | BE-8.5 Stream a response | streaming responses; server-sent events; generators; backpressure; client disconnects; timeouts |
| 9 | BE-9.1 Use In-Process Background Tasks for Small Non-Critical Work | BackgroundTasks; acceptable loss; what happens on restart |
|  | BE-9.2 Recognize When Durable Job Processing Is Required | durability; retries; scheduling; job queues; when to leave in-process tasks |
|  | BE-9.3 Identify Safe Application Cache Opportunities | cache keys; lifetime; invalidation; stale-data risk; measuring the gain |
|  | BE-9.4 Avoid Using Cache as Unexamined Persistent Truth | cache versus source of truth; misses; stale data; restart behaviour |
| 10 | BE-10.1 Use Middleware for True Request-Wide Concerns | middleware; correlation IDs; timing; request-wide headers; what does not belong |
|  | BE-10.2 Reason About Middleware Ordering | middleware order; exception boundaries; response headers |
|  | BE-10.3 Configure CORS from Explicit Origin Requirements | allowed origins, methods, headers, credentials; wildcards; real client requirements |
| 7 | BE-7.6 Cookie sessions and CSRF awareness | cookies; session ids; SameSite, Secure, HttpOnly; CSRF; browser versus API clients |
| 12 | BE-12.1 Audit Object and Function Authorization Boundaries | authorization audit; object-level and function-level checks; exploit requests |
|  | BE-12.2 Prevent Excessive Data Exposure and Unsafe Mass Assignment | excessive data exposure; mass assignment; allowed fields per caller |
|  | BE-12.3 Control Resource Consumption at API Boundaries | unbounded pagination; payload size; expensive operations; rate limits |
|  | BE-12.4 Prevent Unsafe Server-Side Fetching | SSRF; allow-lists; internal addresses; metadata endpoints |
|  | BE-12.5 Remove Unsafe Debug/Test/Configuration Exposure | debug exposure; permissive defaults; leaked secrets; test routes; configuration review |
|  | BE-12.6 Check a package before you add it | package authenticity; typosquatting; maintenance signals; lock files; the least dependency needed; supply-chain risk |
| 13 | BE-13.2 Correlate a Request Across Backend Boundaries | request IDs; following a request across boundaries; log correlation |
|  | BE-13.3 Explain Logs, Metrics, and Traces as Different Signals | events, aggregates and traces; choosing the signal; diagnostic questions |
|  | BE-13.4 Define Useful Backend Health and Readiness Checks | liveness; readiness; dependency checks; probe load |
| 14 | BE-14.1 Use Timeout, Retry, and Backoff as a Coordinated Policy | timeouts, retries and backoff as one policy; jitter; retry amplification |
|  | BE-14.2 Apply Fallbacks Only When Semantically Safe | degraded responses; misleading fallbacks; surfacing failure |
|  | BE-14.3 Recognize Circuit-Breaker / Bulkhead Use Cases at Awareness Depth | circuit breaker; bulkhead; shared resource contention; awareness depth |
| 15 | BE-15.1 Organize a Multi-File FastAPI Backend Around Responsibilities | project layout; responsibilities; imports; config and clients |
|  | BE-15.2 Avoid God Modules and Accidental Layering | god modules; pass-through layers; real change boundaries |
|  | BE-15.3 Keep Framework and Infrastructure Details at Appropriate Boundaries | framework details at the edge; plain arguments; session and request leakage |
| 16 | BE-16.1 Distinguish Development Server from Production Runtime | development server; restarts; process count; memory; HTTPS boundary; failure recovery |
|  | BE-16.2 Reason About Worker Processes and Memory Duplication | worker processes; memory duplication; concurrency trade-offs |
|  | BE-16.3 Run One-Time Startup Operations Safely | migrations; one-time startup; pre-start steps |
|  | BE-16.4 Treat Application Processes as Disposable Runtime Units | stateless processes; local files; restarts; replacement |
| 17 | BE-17.1 Design a Backend Service from Requirements | resources; contracts; services; persistence and external dependencies; auth; failure behaviour |
|  | BE-17.2 Implement the Service with Clear Boundaries | multi-file FastAPI service; layers; dependencies; persistence and clients; small pull requests |
|  | BE-17.3 Test Security, Failure, and Persistence Paths | security, failure and persistence tests; planted bugs; coverage by boundary |
|  | BE-17.4 Diagnose a Runtime Incident from Evidence | logs; request IDs; status codes; dependency evidence; process context |
|  | BE-17.5 Modify the Existing Service Safely Under a Requirement Change | changing an existing service; contracts; tests; migrations; auth; small reviewed pull requests |
|  | BE-17.6 Integrate Backend Capability into an AI Application Without Claim Leakage | LLM call behind an API; timeouts; output validation; claim localisation |

## Unit details


### Stage 0: Backend service mental model

#### BE-0.1 Trace a Request Through a Backend Service

- **Objective:** Can trace a request from protocol/server boundary through routing, validation, application/service logic, persistence or external dependencies, and response generation.
- **The concept (Explain):** A request passes through fixed boundaries, and each one changes the data.
- **Target skills:** CO-2 to Apply; CO-5 to Apply; SP-3 to Apply; DE-2 to Apply
- **Methods:** Explain → Trace → Decompose → Direct
- **Outcome (measured at unit end):** CO-2: writes the state of the data at each step of one request through an AI-generated FastAPI app. CO-5: names each boundary and what crosses it. SP-3: splits the path into stages. DE-2: asks a tool to explain a boundary instead of tracing it for them.
- **Topics:** request flow; server, routing, validation, service, persistence, external call, response; boundaries and what crosses them
- **Prerequisites:** NET-0.1; soft: Python Engineering | **Importance:** Foundational | **Changed in v3:** named prerequisite from the converted supporting roadmaps

#### BE-0.2 Distinguish Transport, Application, Domain, and Persistence Concerns

- **Objective:** Can distinguish HTTP/framework concerns from application behavior, business/domain logic, and data access sufficiently to avoid putting every responsibility in the route function.
- **The concept (Explain):** Each line of code has one main concern: transport, application, domain or persistence.
- **Target skills:** SP-3 to Adapt; CO-6 to Adapt; DE-1 to Adapt; DE-6 to Adapt
- **Methods:** Explain → Decompose → Evaluate
- **Outcome (measured at unit end):** CO-6: explains the four concerns in own words with an example and a non-example. SP-3: labels each line of a route function by concern. DE-1: accepts or rejects the AI's proposed split. DE-6: compares two splits.
- **Topics:** transport, application, domain and persistence concerns; fat route functions; where each belongs
- **Prerequisites:** BE-0.1; SD-0.2 | **Importance:** Foundational | **Changed in v3:** named prerequisite from the converted supporting roadmaps


### Stage 1: API and resource design

#### BE-1.1 Model Backend Operations as Clear API Resources/Actions

- **Objective:** Can turn application requirements into coherent API endpoints/resources and avoid both RPC-like endpoint sprawl and forced REST purity where it harms clarity.
- **The concept (Explain):** An endpoint is a named thing or action that clients depend on; design it from requirements.
- **Target skills:** SP-1 to Adapt; SP-2 to Adapt; SP-3 to Adapt; DE-6 to Adapt
- **Methods:** Explain → Specify → Decompose → Evaluate
- **Outcome (measured at unit end):** SP-1: lists the open questions in a booking requirement. SP-2: writes the endpoint list. SP-3: splits requirements into resources. DE-6: compares an RPC-style and a resource-style design.
- **Topics:** resources and actions; RPC versus REST trade-offs; naming; requirement to endpoint list
- **Prerequisites:** BE-0.1; NET-0.4 | **Importance:** Core | **Changed in v3:** named prerequisite from the converted supporting roadmaps

#### BE-1.2 Select HTTP Methods and Status Codes Consistently

- **Objective:** Can map backend operations to appropriate HTTP methods/status outcomes while respecting safe/idempotent semantics where relevant.
- **The concept (Explain):** The method and status code tell clients what happened and whether a repeat is safe.
- **Target skills:** CO-1 to Apply; CO-4 to Apply; DE-1 to Apply; DE-4 to Apply
- **Methods:** Explain → Predict → Evaluate → Direct
- **Outcome (measured at unit end):** CO-1: predicts status codes for create, repeated create and missing item. CO-4: explains why a repeat of a PUT is safe and a repeat of a POST is not. DE-4: checks RFC 9110. DE-1: accepts or corrects each.
- **Topics:** GET, POST, PUT, PATCH, DELETE; safe and idempotent; status code classes; RFC 9110
- **Prerequisites:** BE-1.1; NET-0.4 | **Importance:** Core | **Changed in v3:** named prerequisite from the converted supporting roadmaps

#### BE-1.3 Design Path, Query, Header, and Body Inputs Deliberately

- **Objective:** Can place identifiers, filters, control parameters, metadata, and structured payloads in appropriate request locations and explain the contract.
- **The concept (Explain):** Each input belongs in the place that matches its meaning: identity in the path, filters in the query, data in the body.
- **Target skills:** SP-2 to Apply; BU-1 to Apply; BU-2 to Apply
- **Methods:** Explain → Specify → Modify
- **Outcome (measured at unit end):** SP-2: writes the input contract for a search endpoint. BU-1: adapts an AI draft that put the filter in the body. BU-2: refines it to the contract.
- **Topics:** path, query, header and body inputs; identifiers; filters; control parameters; contract wording
- **Prerequisites:** BE-1.1 | **Importance:** Core

#### BE-1.4 Design Pagination for Collection Endpoints

- **Objective:** Can implement and reason about bounded collection responses and choose offset/cursor-style approaches at practical depth based on access and consistency needs.
- **The concept (Explain):** A list endpoint must have a bound on how much it returns, and the bound must work while data changes.
- **Target skills:** SP-1 to Apply; BU-1 to Apply; DE-6 to Apply
- **Methods:** Explain → Specify → Modify → Evaluate
- **Outcome (measured at unit end):** SP-1: asks what the feed and its readers need. BU-1: adds pagination to an existing list endpoint. DE-6: compares offset and cursor pagination.
- **Topics:** limits and offsets; cursors; consistency while data changes; bounded responses
- **Prerequisites:** BE-1.1; soft: DB-0.2 (taught later in this path) | **Importance:** Core | **Changed in v3:** named prerequisite from the converted supporting roadmaps

#### BE-1.5 Evolve API Contracts Without Accidental Breakage

- **Objective:** Can distinguish additive from breaking contract changes and choose proportionate compatibility/versioning strategies.
- **The concept (Explain):** A contract change is breaking when an existing client stops working.
- **Target skills:** SP-1 to Apply; SP-4 to Apply; DE-1 to Apply; DE-6 to Apply
- **Methods:** Explain → Specify → Evaluate
- **Outcome (measured at unit end):** SP-1: asks which clients exist. SP-4: spots the missing compatibility detail in a proposed change. DE-1: rejects each breaking change. DE-6: picks a proportionate versioning strategy.
- **Topics:** additive versus breaking changes; deprecation; versioning options; client compatibility
- **Prerequisites:** BE-1.1 | **Importance:** Supporting


### Stage 2: FastAPI request handling and validation

#### BE-2.1 Implement FastAPI Routes and Parameter Binding

- **Objective:** Can implement route handlers using path, query, header, and request-body parameters and predict how FastAPI binds and validates incoming data.
- **The concept (Explain):** FastAPI reads the function signature to decide where each value comes from.
- **Target skills:** CO-1 to Apply; BU-1 to Apply; BU-3 to Apply; VE-4 to Apply
- **Methods:** Explain → Predict → Modify → Build → Debug & Validate
- **Outcome (measured at unit end):** CO-1: predicts how FastAPI binds or rejects five sample requests. VE-4: reads the 422 body to name the failing field. BU-1: adapts the route for a new optional header. BU-3: uses FastAPI's documented binding.
- **Topics:** route handlers; path, query, header and body binding; type hints; 422 responses
- **Prerequisites:** BE-1.2; BE-1.3; soft: Python typing/models | **Importance:** Core

#### BE-2.2 Define Request and Response Models as Explicit Contracts

- **Objective:** Can use Pydantic-backed request/response models to express required/optional fields, nested data, serialization, and response shape without leaking persistence models directly.
- **The concept (Explain):** Request and response models are the contract; the database object is not.
- **Target skills:** SP-2 to Adapt; BU-2 to Adapt; BU-4 to Adapt; DE-1 to Adapt
- **Methods:** Explain → Specify → Modify → Evaluate
- **Outcome (measured at unit end):** SP-2: writes the field-by-field spec. BU-2: refines an AI draft that returns the ORM object into create, update and response models. BU-4: keeps them readable. DE-1: accepts or rejects the AI's shortcuts.
- **Topics:** Pydantic models; required and optional fields; nesting; serialisation; response shape; not returning persistence models
- **Prerequisites:** BE-2.1 | **Importance:** Core

#### BE-2.3 Handle Validation Failures Deliberately

- **Objective:** Can distinguish framework/schema validation from business-rule validation and return useful client-facing errors without hiding programming defects.
- **The concept (Explain):** Schema validation checks shape; business rules need their own checks, and bugs must not look like bad input.
- **Target skills:** VE-1 to Adapt; VE-6 to Adapt; DE-1 to Adapt
- **Methods:** Explain → Debug & Validate → Evaluate
- **Outcome (measured at unit end):** VE-1: writes requests that a plausible wrong validator would accept. VE-6: tries missing, wrong-type and rule-breaking input. DE-1: rejects a handler that turns every error into a 400.
- **Topics:** schema versus business validation; client-facing errors; not hiding defects
- **Prerequisites:** BE-2.2 | **Importance:** Core

#### BE-2.4 Read and use the generated OpenAPI contract (new unit)

- **Objective:** Can read the OpenAPI description FastAPI generates, use it to check a route against its intended contract, and add the descriptions and examples clients need.
- **The concept (Explain):** The OpenAPI document is the contract clients read, generated from your code.
- **Target skills:** BU-3 to Apply; CO-3 to Apply; DE-4 to Apply
- **Methods:** Explain → Build → Direct
- **Outcome (measured at unit end):** CO-3: reads the OpenAPI document of an unfamiliar service. BU-3: adds descriptions, examples and response models. DE-4: checks the FastAPI docs for how it is generated.
- **Topics:** OpenAPI; /docs; schemas; examples; descriptions; response models; contract review
- **Prerequisites:** BE-2.2 | **Importance:** Core

#### BE-2.5 Accept and serve files (new unit)

- **Objective:** Can accept uploaded files and serve downloads with size and type limits, and without trusting the file name or content.
- **The concept (Explain):** A file is untrusted input that is large and may not be what it claims.
- **Target skills:** BU-3 to Apply; VE-6 to Apply; DE-5 to Apply
- **Methods:** Explain → Build → Debug & Validate → Direct
- **Outcome (measured at unit end):** BU-3: implements an upload and a download using the framework's file support. VE-6: tries a huge file, a wrong type and a path-like name. DE-5: decides what limits and storage rules apply.
- **Topics:** multipart uploads; size and type limits; file names; storage location; streaming downloads
- **Prerequisites:** BE-2.2; BE-1.3 | **Importance:** Core


### Stage 11: Backend testing (taught here, earlier than v1)

#### BE-11.1 Separate Unit, Service, API, and Integration Tests by Failure Boundary

- **Objective:** Can choose an appropriate test layer based on what behavior and boundary needs evidence instead of testing everything through HTTP or mocking everything.
- **The concept (Explain):** Choose the test layer by the boundary the behaviour must be proven across.
- **Target skills:** SP-3 to Adapt; DE-1 to Adapt; DE-6 to Adapt
- **Methods:** Explain → Decompose → Evaluate
- **Outcome (measured at unit end):** SP-3: sorts a service's behaviours into unit, service, API and integration tests. DE-1: rejects an AI suite that mocks the database in every test. DE-6: compares layers by cost and what each can catch.
- **Topics:** unit, service, API and integration tests; boundaries; over-mocking
- **Prerequisites:** soft: Python testing foundations; BE-0.2 | **Importance:** Core | **Moved:** Taught right after BE-2.5 (v1: Stage 11)


### Stage 3: Dependency management and application boundaries

#### BE-3.1 Use Dependency Injection for Shared Request/Application Concerns

- **Objective:** Can use FastAPI dependencies for shared concerns such as database sessions, authentication context, configuration, or reusable checks and explain their lifecycle and scope.
- **The concept (Explain):** A dependency is shared setup that FastAPI runs for each request, with a lifetime you can state.
- **Target skills:** BU-1 to Apply; BU-3 to Apply; DE-4 to Apply; CO-6 to Apply
- **Methods:** Explain → Modify → Build → Direct
- **Outcome (measured at unit end):** CO-6: explains dependency injection in own words with an example and a non-example. BU-1: adds a yield-based database-session dependency. BU-3: uses the FastAPI dependency system. DE-4: settles its lifecycle from the docs.
- **Topics:** Depends; yield dependencies; request scope; shared concerns; sub-dependencies
- **Prerequisites:** BE-2.1; SD-0.2 | **Importance:** Core | **Changed in v3:** named prerequisite from the converted supporting roadmaps

#### BE-3.2 Avoid Dependency Injection as a Generic Service Locator

- **Objective:** Can distinguish useful dependency injection from hiding arbitrary application logic behind dependency resolution.
- **The concept (Explain):** A dependency should supply a shared resource; hiding business logic in a chain of them makes code hard to follow.
- **Target skills:** CO-3 to Adapt; DE-2 to Adapt; DE-3 to Adapt; DE-6 to Adapt
- **Methods:** Explain → Direct → Evaluate
- **Outcome (measured at unit end):** CO-3: reads a nested dependency chain in an AI codebase. DE-2: asks a tool to explain it before deciding. DE-3: tells the tool to remove the dependency that hides business logic, with the constraint to keep behaviour identical. DE-6: compares it with a plain service call.
- **Topics:** useful versus hidden dependencies; service locator risk; readability
- **Prerequisites:** BE-3.1; link: SD-0.2 | **Importance:** Supporting | **Changed in v3:** named prerequisite from the converted supporting roadmaps

#### BE-3.3 Move Application Behavior Out of Route Handlers

- **Objective:** Can separate transport/framework code from reusable application/service behavior when the endpoint would otherwise own unrelated responsibilities.
- **The concept (Explain):** A route handler should translate between HTTP and a service call, and do little else.
- **Target skills:** SP-3 to Adapt; BU-1 to Adapt; BU-4 to Adapt; BU-5 to Adapt
- **Methods:** Explain → Decompose → Modify
- **Outcome (measured at unit end):** SP-3: splits a 120-line route handler. BU-1: extracts a service function. BU-4: keeps the service free of framework types. BU-5: makes it one reversible move at a time, old requests unchanged.
- **Topics:** thin handlers; service functions; extract-and-verify; unchanged responses
- **Prerequisites:** BE-0.2; BE-2.1; soft: PY-12.3 | **Importance:** Core | **Changed in v3:** named prerequisite from the converted supporting roadmaps

#### BE-3.4 Design Backend Dependency Flow

- **Objective:** Can keep dependency direction understandable across routes, services, repositories/clients, and infrastructure adapters and avoid circular imports or inward dependencies on framework details.
- **The concept (Explain):** Dependencies should point one way: routes depend on services, services on adapters, never the reverse.
- **Target skills:** SP-3 to Adapt; BU-1 to Adapt; BU-4 to Adapt; CO-5 to Adapt
- **Methods:** Explain → Decompose → Modify
- **Outcome (measured at unit end):** CO-5: maps the import graph before changing anything. SP-3: splits the cycle. BU-1: inverts the dependency. BU-4: keeps the new direction clear.
- **Topics:** dependency direction; circular imports; inversion; layering
- **Prerequisites:** BE-3.3; soft: Python modules/packages; SD-0.2 | **Importance:** Core | **Changed in v3:** named prerequisite from the converted supporting roadmaps

#### BE-3.5 Configuration per environment (new unit)

- **Objective:** Can load settings from the environment with defaults and validation, keep them separate from code, and change them per environment without editing source.
- **The concept (Explain):** The same code runs in development, test and production; only the settings differ.
- **Target skills:** BU-3 to Apply; BU-5 to Apply; DE-4 to Apply
- **Methods:** Explain → Build → Modify → Direct
- **Outcome (measured at unit end):** BU-3: loads settings with a typed settings class from its docs. BU-5: moves one hard-coded value at a time. DE-4: checks the settings library's documentation for source order.
- **Topics:** environment variables; typed settings; defaults; required values; test settings; no secrets in source
- **Prerequisites:** BE-3.1; soft: PY-8.3 | **Importance:** Core


### Stage 4: Errors, failure translation and API reliability basics

#### BE-4.1 Separate Domain/Application Errors from HTTP Errors

- **Objective:** Can represent lower-level/domain failure independently from HTTP and translate it at the API boundary without coupling internal components directly to framework exceptions.
- **The concept (Explain):** Inner code reports failures in its own terms; only the API boundary turns them into HTTP.
- **Target skills:** SP-2 to Adapt; BU-1 to Adapt; BU-2 to Adapt; DE-1 to Adapt
- **Methods:** Explain → Specify → Modify → Evaluate
- **Outcome (measured at unit end):** SP-2: specifies the domain errors a service may raise. BU-1: adapts AI code that raises HTTPException deep inside. BU-2: refines it to the spec. DE-1: accepts or rejects the AI's version.
- **Topics:** domain errors; translation at the boundary; exception handlers
- **Prerequisites:** BE-3.3; soft: Python exception foundations | **Importance:** Core

#### BE-4.2 Map Failures to Stable Client-Facing Error Contracts

- **Objective:** Can expose appropriate status codes and error bodies without leaking internal stack traces, secrets, or implementation details.
- **The concept (Explain):** Errors have one stable shape and leak nothing.
- **Target skills:** VE-1 to Apply; VE-6 to Apply; DE-1 to Apply; DE-5 to Apply
- **Methods:** Explain → Debug & Validate → Evaluate → Direct
- **Outcome (measured at unit end):** VE-1: writes checks that every error keeps one fixed shape. VE-6: forces a crash. DE-5: ensures no stack trace, SQL or secret reaches the client. DE-1: accepts or rejects an AI error handler.
- **Topics:** status codes; error bodies; stable error shape; no stack traces or secrets
- **Prerequisites:** BE-4.1; BE-1.2 | **Importance:** Core


### Stage 11: Backend testing (taught here, earlier than v1)

#### BE-11.2 Test API Contracts and Failure Responses

- **Objective:** Can test status codes, response schemas, validation failures, auth behavior, and error contracts using the framework test client or equivalent.
- **The concept (Explain):** Contract tests check what clients see: status, shape, errors.
- **Target skills:** BU-3 to Adapt; VE-1 to Adapt; VE-6 to Adapt
- **Methods:** Explain → Build → Debug & Validate
- **Outcome (measured at unit end):** BU-3: writes TestClient tests. VE-1: checks status codes, schemas, 422s and 401/403s so they fail on a planted wrong version. VE-6: tries bad input.
- **Topics:** TestClient; status codes; schemas; validation failures; auth; error contracts
- **Prerequisites:** BE-2.2; BE-4.2; link: FastAPI testing | **Importance:** Core | **Moved:** Taught right after BE-4.2 (v1: Stage 11)


### Stage 4: Errors, failure translation and API reliability basics

#### BE-4.3 Distinguish Expected Failures from Programmer Defects

- **Objective:** Can avoid converting every unexpected exception into a misleading business/API error and preserve enough internal evidence for diagnosis.
- **The concept (Explain):** A caught bug is worse than an uncaught one if it looks like a normal answer.
- **Target skills:** VE-2 to Adapt; VE-4 to Adapt; VE-5 to Adapt; DE-1 to Adapt
- **Methods:** Explain → Debug & Validate → Evaluate
- **Outcome (measured at unit end):** VE-2: finds the broad except in AI code. VE-4: reads the traceback behind a 'not found'. VE-5: proves the fix. DE-1: rejects the catch-all.
- **Topics:** expected failures versus defects; broad except; preserving tracebacks
- **Prerequisites:** BE-4.1 | **Importance:** Core


### Stage 13: Observability and runtime diagnosis (taught here, earlier than v1)

#### BE-13.1 Emit Structured, Contextual Backend Logs

- **Objective:** Can log meaningful application/runtime events with request/correlation context and avoid logging secrets or duplicating raw noise.
- **The concept (Explain):** A log line is useful when it carries enough context to find one request later.
- **Target skills:** BU-1 to Apply; BU-2 to Apply; BU-3 to Apply; DE-1 to Apply
- **Methods:** Explain → Modify → Build → Evaluate
- **Outcome (measured at unit end):** BU-1: adapts print-style logging to structured logs with request IDs. BU-2: refines the log format. BU-3: uses the logging library. DE-1: rejects the line that logs the Authorization header.
- **Topics:** structured logs; request IDs; log levels; avoiding secrets; noise
- **Prerequisites:** soft: Python logging; BE-0.1 | **Importance:** Core | **Moved:** Taught right after BE-4.3 (v1: Stage 13)


### Stage 5: External API clients

#### BE-5.1 Build a Typed External API Client Boundary

- **Objective:** Can encapsulate outbound HTTP calls behind a focused client interface and map request/response payloads without scattering provider-specific details through application code.
- **The concept (Explain):** All code that talks to one outside service lives in one client.
- **Target skills:** SP-3 to Adapt; BU-3 to Adapt; DE-3 to Adapt; DE-6 to Adapt
- **Methods:** Explain → Decompose → Build → Direct → Evaluate
- **Outcome (measured at unit end):** SP-3: gathers scattered calls into one boundary. BU-3: builds a typed client from the provider's docs. DE-3: directs the tool to keep the client small and typed, with a stated constraint. DE-6: compares it with the provider's SDK.
- **Topics:** client class; typed payload mapping; provider details in one place; SDK versus own client
- **Prerequisites:** BE-3.3; NET-0.2 | **Importance:** Core | **Changed in v3:** named prerequisite from the converted supporting roadmaps

#### BE-5.2 Configure Timeouts Explicitly

- **Objective:** Can distinguish connection/read/write/pool or equivalent timeout concerns at practical depth and avoid unbounded external waits.
- **The concept (Explain):** Without a timeout, a slow partner takes your service down with it.
- **Target skills:** VE-5 to Apply; VE-6 to Apply; DE-4 to Apply; BU-5 to Apply
- **Methods:** Explain → Debug & Validate → Direct → Modify
- **Outcome (measured at unit end):** VE-6: finds that an AI client has no timeout. DE-4: reads what each httpx timeout covers. BU-5: sets them one change at a time. VE-5: shows a slow fake upstream now fails fast.
- **Topics:** connect, read, write and pool timeouts; failing fast; httpx docs
- **Prerequisites:** BE-5.1; NET-0.6 | **Importance:** Core | **Changed in v3:** named prerequisite from the converted supporting roadmaps

#### BE-5.3 Apply Retries Only to Suitable Failures/Operations

- **Objective:** Can decide whether an outbound operation is safe to retry based on idempotency, failure mode, retry budget, and server response instead of retrying every exception.
- **The concept (Explain):** Only retry what is safe to repeat.
- **Target skills:** SP-1 to Adapt; VE-2 to Adapt; VE-6 to Adapt; DE-1 to Adapt
- **Methods:** Explain → Specify → Debug & Validate → Evaluate
- **Outcome (measured at unit end):** SP-1: asks which calls are idempotent. VE-2: finds the request that shows the harm of an AI retry decorator. VE-6: tests a POST and a 400. DE-1: narrows it to safe failures.
- **Topics:** idempotency; retryable failures; retry budget; response codes
- **Prerequisites:** BE-5.2; link: HTTP idempotency | **Importance:** Core

#### BE-5.4 Validate and Distrust Third-Party API Responses

- **Objective:** Can treat external API data as untrusted input, validate required structure, and fail predictably when upstream payloads are malformed or incomplete.
- **The concept (Explain):** Data from another service is untrusted input.
- **Target skills:** BU-1 to Adapt; VE-1 to Adapt; VE-6 to Adapt; DE-5 to Adapt
- **Methods:** Explain → Modify → Debug & Validate → Direct
- **Outcome (measured at unit end):** DE-5: states where the trust boundary sits and what crosses it unchecked. VE-1: writes checks for malformed, partial and oversized payloads. VE-6: feeds them to an AI client. BU-1: adds response validation.
- **Topics:** validating upstream payloads; failing predictably; trust boundary
- **Prerequisites:** BE-5.1; BE-2.2 | **Importance:** Core


### Stage 11: Backend testing (taught here, earlier than v1)

#### BE-11.4 Test External-Service Failures Without Expensive Real Calls

- **Objective:** Can replace or fake external client boundaries and test timeout, malformed-response, upstream-error, and retry behavior without relying on live providers.
- **The concept (Explain):** Replace the outside service with a fake so failure tests are cheap and repeatable.
- **Target skills:** BU-1 to Adapt; BU-3 to Adapt; VE-1 to Adapt; VE-6 to Adapt
- **Methods:** Explain → Modify → Build → Debug & Validate
- **Outcome (measured at unit end):** BU-3: swaps the live provider for a fake through dependency override. BU-1: adapts the client for testing. VE-1: writes checks for timeout, malformed body and upstream 500. VE-6: checks the retry count.
- **Topics:** fakes; dependency overrides; timeout, malformed and upstream-error tests; retry behaviour
- **Prerequisites:** BE-5.1; BE-5.2; BE-5.4 | **Importance:** Core | **Moved:** Taught right after BE-5.4 (v1: Stage 11)


### Stage 6: Persistence integration

#### BE-6.1 Understand ORM Models as Persistence Mappings, Not Domain Truth

- **Objective:** Can distinguish ORM-mapped objects from API schemas and domain/application concepts and avoid forcing all layers to share one model type.
- **The concept (Explain):** A database mapping class is not the API schema and not the domain object.
- **Target skills:** CO-3 to Apply; CO-6 to Apply; DE-1 to Apply; DE-2 to Apply
- **Methods:** Explain → Evaluate → Direct
- **Outcome (measured at unit end):** CO-6: explains the difference with an example and a non-example. CO-3: reads a class that plays all three roles. DE-2: asks a tool to explain what the ORM is generating. DE-1: rejects the advice to keep one class for everything.
- **Topics:** ORM models; API schemas; domain concepts; separate model types
- **Prerequisites:** DB-0.2; BE-0.2 | **Importance:** Core | **Changed in v3:** named prerequisite from the converted supporting roadmaps

#### BE-6.2 Manage Database Session/Connection Lifecycle per Application Operation

- **Objective:** Can obtain, use, commit/rollback, and release database sessions/connections safely within backend request or job boundaries.
- **The concept (Explain):** A session or connection must be released on every path, including the error path.
- **Target skills:** BU-1 to Adapt; BU-3 to Adapt; VE-3 to Adapt; VE-5 to Adapt
- **Methods:** Explain → Modify → Build → Debug & Validate
- **Outcome (measured at unit end):** VE-3: finds by one hypothesis at a time why an AI endpoint exhausts the pool. BU-1: fixes it with a yield dependency. BU-3: uses the SQLAlchemy session. VE-5: proves the pool is no longer exhausted.
- **Topics:** session per request; commit and rollback; release on error; pool exhaustion
- **Prerequisites:** BE-3.1; DB-1.2 | **Importance:** Core | **Changed in v3:** named prerequisite from the converted supporting roadmaps

#### BE-6.3 Coordinate Application Transaction Boundaries

- **Objective:** Can decide which service operations belong in one transaction and ensure failures roll back the intended unit of work.
- **The concept (Explain):** A transaction is the unit of work that must succeed or fail together.
- **Target skills:** SP-2 to Adapt; BU-1 to Adapt; DE-6 to Adapt; VE-1 to Adapt
- **Methods:** Explain → Specify → Modify → Evaluate → Debug & Validate
- **Outcome (measured at unit end):** SP-2: decides which steps of an order-plus-stock service belong together. BU-1: adapts AI code that commits after each step. DE-6: compares boundary choices. VE-1: writes a check that a failure midway leaves no partial order.
- **Topics:** transaction boundaries; rollback; unit of work; partial failure
- **Prerequisites:** BE-6.2; DB-1.3 | **Importance:** Core | **Changed in v3:** named prerequisite from the converted supporting roadmaps


### Stage 1: API and resource design

#### BE-1.6 Make write endpoints safe to repeat (new unit)

- **Objective:** Can make create and payment-style endpoints safe to retry by accepting an idempotency key and returning the stored result for a repeat.
- **The concept (Explain):** A write is safe to repeat only if the server remembers that it already did it.
- **Target skills:** SP-1 to Adapt; SP-2 to Adapt; VE-1 to Adapt; VE-6 to Adapt
- **Methods:** Explain → Specify → Debug & Validate
- **Outcome (measured at unit end):** SP-1: asks which writes clients may retry. SP-2: specifies the key rule. VE-1: writes a check that a repeated request creates one record. VE-6: tries concurrent repeats and a missing key.
- **Topics:** idempotency keys; storing results; duplicate detection; concurrent repeats; key lifetime
- **Prerequisites:** BE-1.2; BE-6.3 | **Importance:** Core | **Integration link:** Networking / Web Foundations (idempotency) | **Moved:** Taught right after BE-6.3 (needs transactions)


### Stage 11: Backend testing (taught here, earlier than v1)

#### BE-11.3 Test Persistence Behavior with Controlled Database State

- **Objective:** Can verify database-backed flows with isolated/controlled state and distinguish unit-level fake/mocked persistence from real integration behavior.
- **The concept (Explain):** Real database behaviour needs a real database with controlled data.
- **Target skills:** BU-3 to Adapt; VE-1 to Adapt; VE-2 to Adapt; DE-6 to Adapt
- **Methods:** Explain → Build → Debug & Validate → Evaluate
- **Outcome (measured at unit end):** BU-3: builds a fixture that rolls back each test. VE-1: writes persistence checks. VE-2: finds a bug an AI mocked-session test missed. DE-6: compares fake and real persistence.
- **Topics:** test database; rollback fixtures; fakes versus real; controlled state
- **Prerequisites:** BE-6.2; BE-6.3 | **Importance:** Core | **Moved:** Taught right after BE-6.3 (v1: Stage 11)


### Stage 6: Persistence integration

#### BE-6.4 Use Repositories/Data-Access Abstractions Only Where They Clarify Ownership

- **Objective:** Can centralize persistence-specific access where useful without introducing a repository layer merely because a pattern exists.
- **The concept (Explain):** A repository is worth its cost only when it clarifies who owns data access.
- **Target skills:** SP-3 to Apply; BU-4 to Apply; DE-3 to Apply; DE-6 to Apply
- **Methods:** Explain → Decompose → Modify → Direct → Evaluate
- **Outcome (measured at unit end):** SP-3: splits a three-table service. BU-4: removes an unneeded wrapper so the data access stays small. DE-3: directs the tool to remove or keep a repository layer, with the constraints stated. DE-6: compares it with direct session use.
- **Topics:** repositories; data-access ownership; indirection cost
- **Prerequisites:** BE-6.1; BE-3.4; link: SD-1.1 | **Importance:** Supporting | **Changed in v3:** named prerequisite from the converted supporting roadmaps

#### BE-6.5 Diagnose Persistence Failures Across Backend and Database Boundaries

- **Objective:** Can distinguish application validation, ORM/session errors, constraint violations, transaction failures, and database availability failures and route investigation correctly.
- **The concept (Explain):** Persistence failures come from different places, and the traceback tells which.
- **Target skills:** SP-3 to Adapt; VE-3 to Adapt; VE-4 to Adapt; CO-2 to Adapt
- **Methods:** Explain → Decompose → Debug & Validate → Trace
- **Outcome (measured at unit end):** VE-4: reads four tracebacks (validation, detached instance, unique violation, connection refused). SP-3: sorts them by failing boundary. VE-3: confirms each with one test. CO-2: traces the session state in the detached-instance case.
- **Topics:** validation errors; detached instances; constraint violations; transaction failures; database availability
- **Prerequisites:** BE-6.2; DB-0.3 | **Importance:** Core | **Changed in v3:** named prerequisite from the converted supporting roadmaps


### Stage 7: Authentication and authorization

#### BE-7.1 Distinguish Authentication from Authorization

- **Objective:** Can explain identity verification separately from permission decisions and identify where each belongs in backend request flow.
- **The concept (Explain):** Authentication asks who you are; authorization asks what you may do.
- **Target skills:** CO-3 to Apply; CO-4 to Apply
- **Methods:** Explain
- **Outcome (measured at unit end):** CO-3: reads a protected route in AI code. CO-4: labels each check as identity or permission and says where it belongs in the request flow.
- **Topics:** identity versus permission; where each check sits
- **Prerequisites:** BE-0.1 | **Importance:** Core

#### BE-7.2 Implement Token-Based Authentication at Application Depth

- **Objective:** Can integrate a standard token-based authentication flow, validate credentials/tokens, and attach an authenticated principal to request handling without designing a custom cryptographic protocol.
- **The concept (Explain):** A token is a claim until the server verifies it.
- **Target skills:** BU-1 to Apply; BU-3 to Apply; VE-1 to Apply; DE-5 to Apply
- **Methods:** Explain → Modify → Build → Debug & Validate → Direct
- **Outcome (measured at unit end):** BU-3: integrates a JWT library from its docs. BU-1: fits it into an existing app. VE-1: writes checks that expired, tampered, wrong-audience and missing tokens fail. DE-5: treats every token as untrusted until verified.
- **Topics:** token-based authentication; validation; expiry; audience; established libraries
- **Prerequisites:** BE-7.1; BE-3.1 | **Importance:** Core

#### BE-7.3 Handle Passwords and Secrets Safely at Application Depth

- **Objective:** Can use established password hashing/secret-handling libraries, avoid plaintext credentials, and keep signing/API secrets out of source code.
- **The concept (Explain):** Secrets and passwords have established, safe handling; do not invent your own.
- **Target skills:** BU-3 to Apply; DE-1 to Apply; DE-5 to Apply; DE-2 to Apply
- **Methods:** Explain → Build → Evaluate → Direct
- **Outcome (measured at unit end):** BU-3: uses a password hashing library and environment config. DE-1: rejects an AI draft with plain SHA-256 and a hard-coded key. DE-5: keeps secrets out of source. DE-2: asks a tool to explain why a hashing choice is weak.
- **Topics:** password hashing; secret storage; signing keys; no secrets in source
- **Prerequisites:** BE-7.2; link: configuration/secrets | **Importance:** Core


### Stage 5: External API clients

#### BE-5.5 Receive a webhook safely (new unit)

- **Objective:** Can receive a webhook by verifying its signature, acknowledging quickly, processing once, and handling replays.
- **The concept (Explain):** A webhook is a request from the outside; trust it only after you verify who sent it.
- **Target skills:** BU-3 to Adapt; VE-6 to Adapt; DE-5 to Adapt; CO-3 to Adapt
- **Methods:** Explain → Build → Debug & Validate → Direct
- **Outcome (measured at unit end):** BU-3: implements a receiver with signature verification from the provider's docs. VE-6: replays an old request and sends a bad signature. DE-5: decides what to trust and what to do before acknowledging. CO-3: reads the provider's event format.
- **Topics:** signature verification; quick acknowledgement; idempotent processing; replays; retries from the sender
- **Prerequisites:** BE-7.3; BE-1.6 | **Importance:** Core | **Moved:** Taught right after BE-7.3 (needs secrets handling and idempotent writes)


### Stage 7: Authentication and authorization

#### BE-7.4 Enforce Function/Role-Level Authorization

- **Objective:** Can enforce role/permission requirements before protected backend actions and avoid relying only on frontend visibility.
- **The concept (Explain):** The server must check permissions; hiding a button is not a check.
- **Target skills:** BU-1 to Adapt; VE-1 to Adapt; VE-2 to Adapt; DE-5 to Adapt
- **Methods:** Explain → Modify → Debug & Validate → Direct
- **Outcome (measured at unit end):** BU-1: adds a server-side role check to an admin router. VE-1: writes direct requests for a normal user. VE-2: finds routes with no check. DE-5: decides who may do what.
- **Topics:** role checks; permission requirements; 403; not relying on the frontend
- **Prerequisites:** BE-7.1; BE-7.2 | **Importance:** Core

#### BE-7.5 Enforce Object-Level Authorization

- **Objective:** Can verify that the authenticated principal is allowed to access or modify the specific requested object rather than assuming an authenticated user may access any identifier.
- **The concept (Explain):** Being logged in does not mean you may read any record.
- **Target skills:** SP-1 to Adapt; VE-2 to Adapt; VE-6 to Adapt; DE-5 to Adapt
- **Methods:** Explain → Specify → Debug & Validate → Direct
- **Outcome (measured at unit end):** SP-1: asks who owns each record. VE-2: finds the endpoint where any user can read /invoices/{id}. VE-6: names the request that exposes it. DE-5: states the ownership rule.
- **Topics:** object-level authorization; ownership checks; IDOR
- **Prerequisites:** BE-7.4; BE-6.2 | **Importance:** Core


### Stage 8: Async, concurrency and resource lifecycles

#### BE-8.1 Choose def versus async def from Workload Behavior

- **Objective:** Can decide whether endpoint/dependency/service work should be synchronous or asynchronous based on blocking behavior and I/O rather than cargo-cult use of `async`.
- **The concept (Explain):** async def helps only when the work waits; otherwise it can hurt.
- **Target skills:** CO-3 to Adapt; CO-4 to Adapt; DE-1 to Adapt; DE-6 to Adapt
- **Methods:** Explain → Evaluate
- **Outcome (measured at unit end):** CO-3: reads an AI codebase that marks every endpoint async. CO-4: explains why an awaited call lets other requests run and a blocking one does not. DE-1: rejects the blanket async. DE-6: chooses per endpoint with a reason.
- **Topics:** sync versus async endpoints; blocking behaviour; I/O waiting; cargo-cult async
- **Prerequisites:** link: Python async/concurrency; link: PY-11.1, PY-11.5 (OS / Process folded into Python) | **Importance:** Core | **Changed in v3:** named prerequisite from the converted supporting roadmaps

#### BE-8.2 Avoid Blocking the Event Loop

- **Objective:** Can identify blocking operations inside async backend paths and choose a safe alternative such as async client/library use, thread offload, process separation, or synchronous endpoint execution.
- **The concept (Explain):** A blocking call in an async route stalls every request.
- **Target skills:** VE-4 to Adapt; VE-3 to Adapt; VE-5 to Adapt; DE-6 to Adapt
- **Methods:** Explain → Debug & Validate → Evaluate
- **Outcome (measured at unit end):** VE-4: finds the requests.get inside an async route. VE-3: tests one hypothesis. VE-5: measures latency before and after. DE-6: picks async client, thread offload or def.
- **Topics:** event loop blocking; async clients; thread offload; measuring latency
- **Prerequisites:** BE-8.1 | **Importance:** Core

#### BE-8.3 Initialize and Clean Up Shared Application Resources with Lifespan

- **Objective:** Can create and close shared resources such as connection pools or model/client objects at application startup/shutdown rather than recreating them per request or leaking them.
- **The concept (Explain):** Shared resources are created once at startup and closed at shutdown.
- **Target skills:** BU-1 to Adapt; BU-3 to Adapt; VE-3 to Adapt; DE-1 to Adapt
- **Methods:** Explain → Modify → Build → Debug & Validate → Evaluate
- **Outcome (measured at unit end):** BU-1: adapts an app that opens a client per request to one shared client in lifespan. BU-3: uses lifespan. VE-3: compares open connections before and after. DE-1: accepts or rejects the AI's version.
- **Topics:** lifespan; connection pools; shared clients; cleanup
- **Prerequisites:** BE-6.2 or BE-5.1; link: PY-7.4, PY-11.4 | **Importance:** Core | **Changed in v3:** named prerequisite from the converted supporting roadmaps

#### BE-8.4 Reason About Multi-Process Resource Duplication

- **Objective:** Can recognize that each worker process may initialize its own in-memory resources and avoid assuming shared process memory across workers.
- **The concept (Explain):** Each worker process has its own memory.
- **Target skills:** CO-1 to Adapt; CO-5 to Apply; CO-2 to Apply; DE-1 to Apply
- **Methods:** Explain → Predict → Trace → Evaluate
- **Outcome (measured at unit end):** CO-1: predicts what an in-memory counter reports with four workers. CO-2: traces the state in each worker. CO-5: maps what is shared and what is not. DE-1: rejects the claim that the counter is global.
- **Topics:** worker processes; in-memory state; duplication; shared versus per-process
- **Prerequisites:** BE-8.3; link: PY-8.7, PY-11.5 | **Importance:** Supporting | **Changed in v3:** named prerequisite from the converted supporting roadmaps

#### BE-8.5 Stream a response (new unit)

- **Objective:** Can return a streamed response (including server-sent events) to a client, and handle slow and disconnecting clients.
- **The concept (Explain):** A stream keeps a connection open, so you must handle clients that stop reading or leave.
- **Target skills:** BU-3 to Adapt; VE-6 to Adapt; DE-6 to Adapt; DE-4 to Adapt
- **Methods:** Explain → Build → Debug & Validate → Evaluate → Direct
- **Outcome (measured at unit end):** BU-3: implements a streaming endpoint from the framework docs. VE-6: tries a slow client and a disconnect. DE-6: compares streaming with waiting for the full result. DE-4: checks how the framework handles disconnects.
- **Topics:** streaming responses; server-sent events; generators; backpressure; client disconnects; timeouts
- **Prerequisites:** BE-8.1; BE-8.3 | **Importance:** Core | **Integration link:** AI Engineering AI-1.5 (stream a response)


### Stage 9: Background work, jobs and caching

#### BE-9.1 Use In-Process Background Tasks for Small Non-Critical Work

- **Objective:** Can use response-attached/in-process background work for bounded tasks whose loss on process failure is acceptable.
- **The concept (Explain):** In-process background work is lost if the process dies, so use it only when that is acceptable.
- **Target skills:** BU-1 to Apply; BU-3 to Apply; DE-1 to Apply; BU-5 to Apply
- **Methods:** Explain → Modify → Build → Evaluate
- **Outcome (measured at unit end):** BU-3: moves a welcome email into BackgroundTasks. BU-1: adapts the endpoint. BU-5: changes one endpoint at a time. DE-1: rejects the use of the same mechanism for invoices that must not be lost.
- **Topics:** BackgroundTasks; acceptable loss; what happens on restart
- **Prerequisites:** BE-0.1; BE-8.3 | **Importance:** Supporting

#### BE-9.2 Recognize When Durable Job Processing Is Required

- **Objective:** Can identify workloads that require persistence, retries, isolation, scheduling, or multi-process workers and route them toward a durable queue/job system rather than in-process background tasks.
- **The concept (Explain):** Some work needs durability, retries or scheduling that in-process tasks cannot give.
- **Target skills:** SP-1 to Apply; SP-4 to Apply; DE-6 to Apply; DE-2 to Apply
- **Methods:** Explain → Specify → Evaluate → Direct
- **Outcome (measured at unit end):** SP-1: lists the durability and retry questions for a report export. SP-4: spots the missing requirement. DE-6: compares in-process tasks with a job queue. DE-2: asks a tool to explain queue guarantees.
- **Topics:** durability; retries; scheduling; job queues; when to leave in-process tasks
- **Prerequisites:** BE-9.1; link: System Architecture | **Importance:** Core

#### BE-9.3 Identify Safe Application Cache Opportunities

- **Objective:** Can identify repeated expensive reads/computations that may benefit from caching and specify cache key, lifetime, invalidation, and stale-data risks.
- **The concept (Explain):** A cache needs a key, a lifetime and an invalidation rule before it needs code.
- **Target skills:** SP-1 to Adapt; SP-2 to Adapt; VE-3 to Adapt; DE-6 to Adapt
- **Methods:** Explain → Specify → Debug & Validate → Evaluate
- **Outcome (measured at unit end):** SP-1: asks how fresh the data must be. SP-2: specifies key, lifetime and invalidation. VE-3: measures latency before and after. DE-6: judges where an AI's cache would serve stale prices.
- **Topics:** cache keys; lifetime; invalidation; stale-data risk; measuring the gain
- **Prerequisites:** BE-0.2; soft: DB-1.5 | **Importance:** Core | **Changed in v3:** named prerequisite from the converted supporting roadmaps

#### BE-9.4 Avoid Using Cache as Unexamined Persistent Truth

- **Objective:** Can distinguish cache from authoritative state and reason about cache misses, invalidation, stale data, and restart/process boundaries.
- **The concept (Explain):** A cache is a copy, never the truth.
- **Target skills:** CO-1 to Apply; CO-6 to Apply; VE-2 to Apply; VE-6 to Apply
- **Methods:** Explain → Predict → Debug & Validate
- **Outcome (measured at unit end):** CO-1: predicts what an AI-cached endpoint returns after an update and after a restart. CO-6: explains cache versus authoritative state with an example and a non-example. VE-2: finds the path that treats the cache as truth. VE-6: tries misses and restarts.
- **Topics:** cache versus source of truth; misses; stale data; restart behaviour
- **Prerequisites:** BE-9.3 | **Importance:** Core


### Stage 10: Middleware, cross-cutting request concerns and CORS

#### BE-10.1 Use Middleware for True Request-Wide Concerns

- **Objective:** Can implement or configure middleware for concerns such as correlation IDs, timing, headers, or request-level logging and avoid moving endpoint/business behavior into middleware.
- **The concept (Explain):** Middleware is for rules that apply to every request.
- **Target skills:** BU-3 to Apply; BU-1 to Apply; BU-4 to Apply; DE-3 to Apply
- **Methods:** Explain → Build → Modify → Direct
- **Outcome (measured at unit end):** BU-3: adds correlation-ID and timing middleware. BU-1: fits it into an existing app. BU-4: keeps it to the one rule that applies to every request. DE-3: directs the tool to move permission logic that an AI put in middleware into a dependency.
- **Topics:** middleware; correlation IDs; timing; request-wide headers; what does not belong
- **Prerequisites:** BE-0.1 | **Importance:** Core

#### BE-10.2 Reason About Middleware Ordering

- **Objective:** Can diagnose behavior affected by middleware ordering and exception handling boundaries.
- **The concept (Explain):** Middleware runs in order, and errors change the path.
- **Target skills:** CO-1 to Adapt; CO-2 to Apply; VE-3 to Apply
- **Methods:** Explain → Predict → Trace → Debug & Validate
- **Outcome (measured at unit end):** CO-1: predicts the order of three middlewares. CO-2: traces one request through them. VE-3: finds why a header vanishes on error responses, one change at a time.
- **Topics:** middleware order; exception boundaries; response headers
- **Prerequisites:** BE-10.1 | **Importance:** Supporting

#### BE-10.3 Configure CORS from Explicit Origin Requirements

- **Objective:** Can configure allowed origins/methods/headers/credentials based on an actual frontend/client requirement and avoid permissive wildcard configuration where credentials or sensitive APIs are involved.
- **The concept (Explain):** CORS should list the origins the frontend really uses.
- **Target skills:** BU-1 to Apply; DE-4 to Apply; DE-5 to Apply
- **Methods:** Explain → Modify → Direct
- **Outcome (measured at unit end):** BU-1: replaces allow_origins=['*'] with the two real origins. DE-4: confirms the behaviour in the Starlette docs. DE-5: refuses a permissive setting with credentials.
- **Topics:** allowed origins, methods, headers, credentials; wildcards; real client requirements
- **Prerequisites:** BE-7.1 where authenticated browser clients exist | **Importance:** Core | **Changed in v3:** named prerequisite from the converted supporting roadmaps


### Stage 7: Authentication and authorization

#### BE-7.6 Cookie sessions and CSRF awareness (new unit)

- **Objective:** Can explain how cookie-based sessions differ from token headers, and when a browser client needs same-site cookies and CSRF protection.
- **The concept (Explain):** A browser sends cookies automatically, so a cookie session needs protection against requests the user did not intend.
- **Target skills:** CO-6 to Apply; SP-4 to Apply; DE-5 to Apply
- **Methods:** Explain → Specify → Direct
- **Outcome (measured at unit end):** CO-6: explains cookie sessions and CSRF in own words with an example and a non-example. SP-4: spots the missing protection in a described design. DE-5: decides where the trust boundary lies for a browser client.
- **Topics:** cookies; session ids; SameSite, Secure, HttpOnly; CSRF; browser versus API clients
- **Prerequisites:** BE-7.2; BE-10.3 | **Importance:** Supporting | **Moved:** Taught right after BE-10.3 (it needs the CORS unit)


### Stage 12: API security

#### BE-12.1 Audit Object and Function Authorization Boundaries

- **Objective:** Can inspect protected routes and identify missing object-level or function-level authorization checks.
- **The concept (Explain):** A missing permission check is found by reading each route and asking who can call it.
- **Target skills:** VE-2 to Adapt; VE-6 to Adapt; DE-5 to Adapt
- **Methods:** Explain → Debug & Validate → Direct
- **Outcome (measured at unit end):** VE-2: audits every route of an AI-generated API. VE-6: sends the exploiting request for each gap. DE-5: names the rule that should apply.
- **Topics:** authorization audit; object-level and function-level checks; exploit requests
- **Prerequisites:** BE-7.4; BE-7.5 | **Importance:** Core

#### BE-12.2 Prevent Excessive Data Exposure and Unsafe Mass Assignment

- **Objective:** Can constrain request/response models and update flows so clients cannot read or write properties merely because those properties exist in internal models.
- **The concept (Explain):** Clients must not read or write fields just because they exist in the model.
- **Target skills:** SP-2 to Adapt; BU-2 to Adapt; VE-6 to Adapt; DE-3 to Adapt
- **Methods:** Explain → Specify → Modify → Debug & Validate → Direct
- **Outcome (measured at unit end):** SP-2: states which fields each caller may read and write. BU-2: refines an update endpoint so clients cannot set is_admin. VE-6: sends the hostile request. DE-3: directs the tool to close the gap with explicit field lists, then reviews the diff.
- **Topics:** excessive data exposure; mass assignment; allowed fields per caller
- **Prerequisites:** BE-2.2; BE-7.5 | **Importance:** Core

#### BE-12.3 Control Resource Consumption at API Boundaries

- **Objective:** Can identify unbounded pagination, payload size, expensive operations, or uncontrolled repeated actions and apply proportionate limits.
- **The concept (Explain):** An API without limits can be used up by one client.
- **Target skills:** CO-4 to Apply; SP-4 to Apply; DE-5 to Apply; DE-6 to Apply
- **Methods:** Explain → Specify → Direct → Evaluate
- **Outcome (measured at unit end):** CO-4: explains how one client can use up a shared resource. SP-4: names the limits an AI's API spec left out. DE-5: sets them. DE-6: picks a proportionate limit for each.
- **Topics:** unbounded pagination; payload size; expensive operations; rate limits
- **Prerequisites:** BE-1.4; BE-9.2 | **Importance:** Core

#### BE-12.4 Prevent Unsafe Server-Side Fetching

- **Objective:** Can recognize when a backend accepts user-controlled URLs or network destinations and apply allow-listing/validation or architectural restrictions to reduce SSRF risk.
- **The concept (Explain):** A service that fetches a user-supplied URL can be turned against its own network.
- **Target skills:** SP-1 to Apply; VE-5 to Apply; VE-6 to Apply; DE-5 to Apply
- **Methods:** Explain → Specify → Debug & Validate → Direct
- **Outcome (measured at unit end):** SP-1: asks what the endpoint needs to fetch. VE-6: tries internal and cloud-metadata URLs. DE-5: specifies an allow-list. VE-5: checks the fix against the same URLs.
- **Topics:** SSRF; allow-lists; internal addresses; metadata endpoints
- **Prerequisites:** BE-5.1; NET-0.3 | **Importance:** Core | **Changed in v3:** named prerequisite from the converted supporting roadmaps

#### BE-12.5 Remove Unsafe Debug/Test/Configuration Exposure

- **Objective:** Can identify exposed debug endpoints, permissive defaults, leaked secrets, development-only routes, or insecure configuration before production deployment.
- **The concept (Explain):** What is safe in development can be dangerous in production.
- **Target skills:** VE-2 to Adapt; VE-6 to Adapt; DE-1 to Adapt; DE-5 to Adapt
- **Methods:** Explain → Debug & Validate → Evaluate → Direct
- **Outcome (measured at unit end):** VE-2: finds the exposed debug flag, test route and committed .env. VE-6: tests production-like requests. DE-1: decides keep or remove with a reason. DE-5: sets safe defaults.
- **Topics:** debug exposure; permissive defaults; leaked secrets; test routes; configuration review
- **Prerequisites:** BE-10.3; BE-7.3 | **Importance:** Core

#### BE-12.6 Check a package before you add it (new unit)

- **Objective:** Can check that a dependency is genuine, maintained and proportionate before installing it, and notice signs of typosquatting or a compromised release.
- **The concept (Explain):** Every package you add is code you run with your service's permissions.
- **Target skills:** DE-4 to Adapt; DE-1 to Adapt; DE-5 to Adapt
- **Methods:** Explain → Direct → Evaluate
- **Outcome (measured at unit end):** DE-4: checks the registry page, repository and release history against the project's official source. DE-1: accepts or rejects an AI-suggested package. DE-5: limits what the dependency can reach.
- **Topics:** package authenticity; typosquatting; maintenance signals; lock files; the least dependency needed; supply-chain risk
- **Prerequisites:** soft: PY-10.2 | **Importance:** Core


### Stage 13: Observability and runtime diagnosis

#### BE-13.2 Correlate a Request Across Backend Boundaries

- **Objective:** Can follow one request through route, service, database/external calls, and failure handling using IDs/context rather than isolated log messages.
- **The concept (Explain):** One request leaves a trail; follow the trail, not isolated lines.
- **Target skills:** SP-3 to Adapt; VE-3 to Adapt; VE-4 to Adapt; CO-2 to Adapt
- **Methods:** Explain → Decompose → Debug & Validate → Trace
- **Outcome (measured at unit end):** CO-2: follows the request's state through route, service and upstream-call logs. SP-3: splits the path into steps. VE-3: tests one hypothesis at a time. VE-4: reads the errors found.
- **Topics:** request IDs; following a request across boundaries; log correlation
- **Prerequisites:** BE-13.1; BE-5.1 or BE-6.2 | **Importance:** Core

#### BE-13.3 Explain Logs, Metrics, and Traces as Different Signals

- **Objective:** Can distinguish event detail, aggregate measurements, and distributed/request-path traces and choose the signal that answers the diagnostic question.
- **The concept (Explain):** Logs, metrics and traces answer different questions.
- **Target skills:** CO-6 to Apply; DE-4 to Apply; DE-2 to Apply; CO-5 to Apply
- **Methods:** Explain → Direct
- **Outcome (measured at unit end):** CO-6: explains the three signals with an example and a non-example. DE-4: picks the signal that answers each of three diagnostic questions. DE-2: asks a tool to explain a trace view. CO-5: maps how a request shows up in each signal.
- **Topics:** events, aggregates and traces; choosing the signal; diagnostic questions
- **Prerequisites:** BE-13.1 | **Importance:** Core

#### BE-13.4 Define Useful Backend Health and Readiness Checks

- **Objective:** Can distinguish process liveness from readiness to serve requests and avoid health checks that accidentally hide important dependency failure or overload dependencies.
- **The concept (Explain):** Alive and ready are different questions.
- **Target skills:** SP-2 to Apply; SP-4 to Apply; DE-1 to Apply
- **Methods:** Explain → Specify → Evaluate
- **Outcome (measured at unit end):** SP-2: specifies liveness and readiness. SP-4: spots the missing dependency case. DE-1: rejects an AI readiness check that calls the upstream on every probe.
- **Topics:** liveness; readiness; dependency checks; probe load
- **Prerequisites:** BE-8.3; BE-13.3 | **Importance:** Core


### Stage 14: Resilience and graceful degradation

#### BE-14.1 Use Timeout, Retry, and Backoff as a Coordinated Policy

- **Objective:** Can combine bounded timeouts, selective retries, and backoff/jitter where appropriate and explain how poor retry policy can amplify failure.
- **The concept (Explain):** Retries without bounds make an outage worse.
- **Target skills:** VE-3 to Adapt; VE-6 to Adapt; DE-1 to Adapt; DE-6 to Adapt
- **Methods:** Explain → Debug & Validate → Evaluate
- **Outcome (measured at unit end):** VE-3: measures how many calls one request causes. VE-6: runs a flaky fake upstream. DE-1: rejects an AI retry policy. DE-6: replaces it with bounded retries and jittered backoff.
- **Topics:** timeouts, retries and backoff as one policy; jitter; retry amplification
- **Prerequisites:** BE-5.2; BE-5.3 | **Importance:** Core

#### BE-14.2 Apply Fallbacks Only When Semantically Safe

- **Objective:** Can distinguish a valid degraded response from a fallback that returns stale, misleading, or incorrect data and surface failure instead where necessary.
- **The concept (Explain):** A fallback is only safe if its answer is still true.
- **Target skills:** SP-1 to Adapt; SP-4 to Adapt; DE-1 to Adapt; DE-6 to Adapt
- **Methods:** Explain → Specify → Evaluate
- **Outcome (measured at unit end):** SP-1: asks what a stale answer would cost. SP-4: spots the missing case. DE-1: judges an AI fallback that returns a cached balance. DE-6: states per endpoint whether to degrade or fail.
- **Topics:** degraded responses; misleading fallbacks; surfacing failure
- **Prerequisites:** BE-4.1; BE-14.1 | **Importance:** Core

#### BE-14.3 Recognize Circuit-Breaker / Bulkhead Use Cases at Awareness Depth

- **Objective:** Can recognize when repeated dependency failure or shared resource contention may justify circuit-breaking or isolation patterns without implementing production-grade resilience infrastructure by default.
- **The concept (Explain):** Isolating a failing dependency can keep the rest of the service alive.
- **Target skills:** CO-4 to Understand; CO-6 to Understand; DE-6 to Understand; DE-2 to Understand
- **Methods:** Explain → Evaluate → Direct
- **Outcome (measured at unit end):** CO-6: explains circuit breaker and bulkhead with an example and a non-example. CO-4: says why one would or would not have helped in a described outage. DE-6: compares the options. DE-2: asks a tool to explain a pattern before deciding.
- **Topics:** circuit breaker; bulkhead; shared resource contention; awareness depth
- **Prerequisites:** BE-14.1 | **Importance:** Supporting


### Stage 15: Project structure and backend architecture

#### BE-15.1 Organize a Multi-File FastAPI Backend Around Responsibilities

- **Objective:** Can structure routes, application/services, schemas/contracts, persistence/data-access code, configuration, clients, and supporting code so imports/dependencies remain understandable.
- **The concept (Explain):** Files should follow responsibilities so imports stay understandable.
- **Target skills:** SP-3 to Adapt; BU-1 to Adapt; BU-4 to Adapt; DE-6 to Adapt
- **Methods:** Explain → Decompose → Modify → Evaluate
- **Outcome (measured at unit end):** SP-3: splits a single-file app into routes, services, schemas, data access, config and clients. BU-1: restructures it without changing behaviour. BU-4: keeps the layout clear. DE-6: compares two layouts.
- **Topics:** project layout; responsibilities; imports; config and clients
- **Prerequisites:** BE-3.3; BE-3.4; soft: Python modules/packages | **Importance:** Core

#### BE-15.2 Avoid God Modules and Accidental Layering

- **Objective:** Can identify when one module owns too many backend responsibilities or when extra layers add indirection without a real change boundary.
- **The concept (Explain):** Extra layers cost clarity unless they mark a real change boundary.
- **Target skills:** DE-1 to Adapt; DE-6 to Adapt; BU-4 to Adapt; CO-5 to Adapt
- **Methods:** Explain → Evaluate → Modify
- **Outcome (measured at unit end):** CO-5: maps what each module depends on. DE-1: accepts, changes or rejects the AI's refactor for the god module and the pass-through layer. DE-6: compares options. BU-4: carries out the agreed refactor.
- **Topics:** god modules; pass-through layers; real change boundaries
- **Prerequisites:** BE-15.1; link: SD-1.4 | **Importance:** Core | **Changed in v3:** named prerequisite from the converted supporting roadmaps

#### BE-15.3 Keep Framework and Infrastructure Details at Appropriate Boundaries

- **Objective:** Can prevent framework-specific request objects, ORM sessions, and provider clients from leaking unnecessarily into core application behavior.
- **The concept (Explain):** Core code should not depend on framework objects.
- **Target skills:** SP-3 to Adapt; BU-1 to Adapt; BU-4 to Adapt; DE-1 to Adapt
- **Methods:** Explain → Decompose → Modify → Evaluate
- **Outcome (measured at unit end):** SP-3: lists where Request and Session leak. BU-1: replaces them with plain arguments. BU-4: keeps callers working. DE-1: accepts or rejects the AI's change.
- **Topics:** framework details at the edge; plain arguments; session and request leakage
- **Prerequisites:** BE-15.1; BE-3.4; BE-6.1 | **Importance:** Core


### Stage 16: Deployment and runtime fundamentals

#### BE-16.1 Distinguish Development Server from Production Runtime

- **Objective:** Can explain why a development server/runtime is not itself a production strategy and identify startup, restart, process count, memory, HTTPS boundary, and failure recovery as production concerns.
- **The concept (Explain):** A development server is not a production strategy.
- **Target skills:** CO-4 to Apply; DE-1 to Apply; DE-4 to Apply; DE-2 to Apply
- **Methods:** Explain → Evaluate → Direct
- **Outcome (measured at unit end):** CO-4: explains what production needs. DE-1: rejects an AI deploy plan that runs the reloading dev server. DE-4: cites the FastAPI deployment docs. DE-2: asks a tool to explain the deployment options before choosing.
- **Topics:** development server; restarts; process count; memory; HTTPS boundary; failure recovery
- **Prerequisites:** BE-8.3; link: PY-5.4, PY-8.7 | **Importance:** Core | **Changed in v3:** named prerequisite from the converted supporting roadmaps

#### BE-16.2 Reason About Worker Processes and Memory Duplication

- **Objective:** Can reason about multiple backend worker processes, independent memory/resource initialization, and process count versus memory/concurrency trade-offs.
- **The concept (Explain):** More workers mean more memory.
- **Target skills:** CO-1 to Apply; CO-4 to Apply; CO-5 to Apply; DE-6 to Apply
- **Methods:** Explain → Predict → Evaluate
- **Outcome (measured at unit end):** CO-1: predicts memory with a 1 GB model and four workers. CO-4: explains why memory is paid per process. CO-5: maps what each worker holds. DE-6: chooses a worker count with a reason.
- **Topics:** worker processes; memory duplication; concurrency trade-offs
- **Prerequisites:** BE-8.4; link: PY-8.7, PY-11.5 | **Importance:** Core | **Changed in v3:** named prerequisite from the converted supporting roadmaps

#### BE-16.3 Run One-Time Startup Operations Safely

- **Objective:** Can recognize operations such as database migrations that should not be executed independently by every replicated application worker.
- **The concept (Explain):** Some startup work must run once, not once per worker.
- **Target skills:** SP-1 to Apply; DE-1 to Apply; BU-5 to Apply
- **Methods:** Explain → Specify → Evaluate → Modify
- **Outcome (measured at unit end):** SP-1: asks which startup steps must run once. DE-1: rejects migrations in every worker's lifespan. BU-5: moves them to one pre-start step in a small change.
- **Topics:** migrations; one-time startup; pre-start steps
- **Prerequisites:** BE-16.2; DB-1.6 | **Importance:** Core | **Changed in v3:** named prerequisite from the converted supporting roadmaps

#### BE-16.4 Treat Application Processes as Disposable Runtime Units

- **Objective:** Can avoid relying on local process memory or filesystem as durable shared application state and design for restart/replacement at foundation depth.
- **The concept (Explain):** A process should be safe to kill and replace.
- **Target skills:** CO-3 to Apply; CO-6 to Apply; DE-1 to Apply
- **Methods:** Explain → Evaluate
- **Outcome (measured at unit end):** CO-6: explains disposable processes with an example and a non-example. CO-3: lists every place an AI service keeps state in memory or local files. DE-1: accepts or rejects each for a restartable deployment.
- **Topics:** stateless processes; local files; restarts; replacement
- **Prerequisites:** BE-16.1; link: PY-10.4 | **Importance:** Core | **Changed in v3:** named prerequisite from the converted supporting roadmaps


### Stage 17: Integrated backend engineering

#### BE-17.1 Design a Backend Service from Requirements

- **Objective:** Can translate a bounded product/application requirement into API resources, contracts, service responsibilities, persistence/external dependencies, auth rules, and failure behavior.
- **The concept (Explain):** A service design starts from a loose brief and ends as contracts, responsibilities and failure rules.
- **Target skills:** SP-1 to Adapt; SP-2 to Adapt; SP-3 to Adapt; DE-3 to Adapt
- **Methods:** Explain → Specify → Decompose → Direct
- **Outcome (measured at unit end):** SP-1: lists open questions. SP-2: writes resources, contracts, auth rules and failure behaviour. SP-3: splits responsibilities. DE-3: plans what to delegate.
- **Topics:** resources; contracts; services; persistence and external dependencies; auth; failure behaviour
- **Prerequisites:** BE-1.1; BE-2.2; BE-3.3; selected persistence/external/auth units | **Importance:** Core

#### BE-17.2 Implement the Service with Clear Boundaries

- **Objective:** Can implement a multi-file FastAPI service using appropriate validation, application/service layers, dependencies, persistence/external clients, and runtime resources without collapsing everything into route handlers.
- **The concept (Explain):** A multi-file service stays readable if each piece has one job.
- **Target skills:** BU-2 to Adapt; BU-3 to Own; BU-5 to Adapt; DE-3 to Adapt
- **Methods:** Explain → Modify → Build → Direct
- **Outcome (measured at unit end):** DE-3: directs an AI to build the BE-17.1 service piece by piece. BU-2: refines each draft to its spec. BU-3: integrates persistence, clients and runtime resources. BU-5: delivers each piece as a small reviewable pull request.
- **Topics:** multi-file FastAPI service; layers; dependencies; persistence and clients; small pull requests
- **Prerequisites:** BE-17.1; BE-15.1 | **Importance:** Core

#### BE-17.3 Test Security, Failure, and Persistence Paths

- **Objective:** Can verify success and failure behavior across validation, auth, database/external dependencies, and error contracts.
- **The concept (Explain):** A good suite fails when the service is wrong, including in ways you did not plan.
- **Target skills:** BU-3 to Adapt; VE-1 to Adapt; VE-2 to Adapt; VE-6 to Adapt
- **Methods:** Explain → Build → Debug & Validate
- **Outcome (measured at unit end):** BU-3: uses test client, fixtures and fakes. VE-1: writes security, failure and persistence checks. VE-2: finds a planted bug. VE-6: tries versions the learner has not seen.
- **Topics:** security, failure and persistence tests; planted bugs; coverage by boundary
- **Prerequisites:** BE-11.2; BE-11.3; BE-11.4; selected Stage 12 units | **Importance:** Core

#### BE-17.4 Diagnose a Runtime Incident from Evidence

- **Objective:** Can trace an operational failure using logs, request correlation, status/error behavior, dependency evidence, and runtime/process context and identify the most likely failing boundary.
- **The concept (Explain):** An incident is solved by evidence, not guesses.
- **Target skills:** CO-2 to Adapt; VE-3 to Own; VE-4 to Own; SP-3 to Adapt
- **Methods:** Explain → Trace → Debug & Validate → Decompose
- **Outcome (measured at unit end):** CO-2: follows the request's state through logs and status codes. VE-3: tests one hypothesis at a time. VE-4: reads errors and dependency evidence. SP-3: names the failing boundary.
- **Topics:** logs; request IDs; status codes; dependency evidence; process context
- **Prerequisites:** BE-13.2; BE-13.3; BE-14.1 | **Importance:** Core

#### BE-17.5 Modify the Existing Service Safely Under a Requirement Change

- **Objective:** Can add or change behavior in an existing backend while preserving contracts, tests, boundaries, migrations, and security expectations.
- **The concept (Explain):** A change to someone else's service must keep contracts, tests and security intact.
- **Target skills:** BU-1 to Adapt; BU-5 to Adapt; VE-1 to Adapt; VE-5 to Adapt
- **Methods:** Explain → Modify → Debug & Validate
- **Outcome (measured at unit end):** BU-1: adds a requirement change. BU-5: delivers it as small pull requests with a description and a failing-then-passing check. VE-1: writes the check. VE-5: proves the fix.
- **Topics:** changing an existing service; contracts; tests; migrations; auth; small reviewed pull requests
- **Prerequisites:** BE-17.2; BE-17.3; GIT-1.2; link: SD-1.4 | **Importance:** Core | **Changed in v3:** named prerequisite from the converted supporting roadmaps

#### BE-17.6 Integrate Backend Capability into an AI Application Without Claim Leakage

- **Objective:** Can provide a robust backend boundary around an AI feature while keeping evidence localized: backend evidence for API/runtime/persistence/security/service behavior, AI Engineering evidence only for AI-specific capabilities.
- **The concept (Explain):** A backend boundary around an AI feature must keep the evidence for each roadmap apart.
- **Target skills:** SP-3 to Adapt; BU-3 to Adapt; DE-3 to Adapt; DE-5 to Adapt
- **Methods:** Explain → Decompose → Build → Direct
- **Outcome (measured at unit end):** BU-3: puts an LLM provider call behind an authenticated endpoint with timeouts and output validation. SP-3: splits backend and AI responsibilities. DE-3: decides who owns what. DE-5: bounds authority.
- **Topics:** LLM call behind an API; timeouts; output validation; claim localisation
- **Prerequisites:** BE-17.2; at least one AI Engineering unit when available | **Importance:** Core

## Skill coverage (target skills, whole roadmap)

Rule used: a skill gets sufficient practice when it is a target in at least 6 units, in at least three of the four bands (Stages 0-4, 5-9, 10-13, 14-17, by the old Stage label), and reaches Adapt or higher.

| Skill | Units | Stages 0-4 | Stages 5-9 | Stages 10-13 | Stages 14-17 | Highest level |
| --- | --- | --- | --- | --- | --- | --- |
| CO-1 | 6 | 2 | 2 | 1 | 1 | Adapt |
| CO-2 | 6 | 1 | 2 | 2 | 1 | Adapt |
| CO-3 | 7 | 2 | 4 | 0 | 1 | Adapt |
| CO-4 | 7 | 1 | 2 | 1 | 3 | Adapt |
| CO-5 | 6 | 2 | 1 | 1 | 2 | Adapt |
| CO-6 | 8 | 2 | 3 | 1 | 2 | Adapt |
| SP-1 | 12 | 4 | 4 | 1 | 3 | Adapt |
| SP-2 | 10 | 5 | 2 | 2 | 1 | Adapt |
| SP-3 | 15 | 5 | 3 | 2 | 5 | Adapt |
| SP-4 | 6 | 1 | 2 | 2 | 1 | Adapt |
| BU-1 | 21 | 7 | 7 | 4 | 3 | Adapt |
| BU-2 | 6 | 3 | 0 | 2 | 1 | Adapt |
| BU-3 | 21 | 5 | 8 | 5 | 3 | Own |
| BU-4 | 8 | 3 | 1 | 1 | 3 | Adapt |
| BU-5 | 7 | 2 | 2 | 0 | 3 | Adapt |
| VE-1 | 12 | 3 | 4 | 3 | 2 | Adapt |
| VE-2 | 9 | 1 | 4 | 3 | 1 | Adapt |
| VE-3 | 9 | 0 | 5 | 2 | 2 | Own |
| VE-4 | 6 | 2 | 2 | 1 | 1 | Own |
| VE-5 | 6 | 1 | 3 | 1 | 1 | Adapt |
| VE-6 | 19 | 4 | 7 | 6 | 2 | Adapt |
| DE-1 | 27 | 8 | 7 | 5 | 7 | Adapt |
| DE-2 | 8 | 2 | 3 | 1 | 2 | Adapt |
| DE-3 | 8 | 1 | 2 | 2 | 3 | Adapt |
| DE-4 | 10 | 4 | 2 | 3 | 1 | Adapt |
| DE-5 | 16 | 2 | 7 | 6 | 1 | Adapt |
| DE-6 | 22 | 5 | 8 | 3 | 6 | Adapt |

All 27 skills meet the rule. 79 units: 1 with two targets, 16 with three, 62 with four. Habits H-1 to H-3 are recorded every session and are not listed.

## Decisions (approved by Asheesh 2026-10-18)

1. **Testing and logging are taught earlier**, right after the code they check (see "What changed"). IDs are unchanged.
2. **New units:** BE-1.6 idempotent writes, BE-2.4 OpenAPI contract, BE-2.5 file upload and download, BE-3.5 configuration per environment, BE-5.5 receiving a webhook safely, BE-7.6 cookie sessions and CSRF awareness (Supporting), BE-8.5 streaming a response, BE-12.6 checking a package before adding it.
3. **Spine rule:** Backend, like Python and AI Engineering, must train all 27 skills enough.
4. **Own** only at BE-17.2 (BU-3) and BE-17.4 (VE-3, VE-4); everything else tops out at Adapt. BE-14.3 stays at Understand.
5. **Python entry point:** Python through Stage 11 (see "What changed").
6. **Four-target units** (62 of 79) are kept as drafted; over-covered skills (DE-1, DE-6, BU-1, VE-6, SP-3) can be trimmed later if learners find units heavy.
7. **Other roadmaps are not named prerequisites yet**; the link pass adds them after those roadmaps are upgraded.

## Project links

Projects follow the Projects & Capstones Integration Layer (P0 to P4). A project integrates the units; evidence stays with the roadmap that owns it. Each unit's Outcome task is the P0 exercise.

**Portfolio and pull requests (Asheesh, 2026-10-18).** Every project below is built to be shown in a portfolio and is delivered through pull requests, not direct commits to the main branch. From P1: small pull requests, each with a description of what changed and why, and the test result that backs it. From P2: at least one review round and automatic checks on every pull request. From P3: the pull request history is part of the evidence, and AI-assisted pull requests are marked as such. PR skills are owned by the Git roadmap; BE-17.5 is the first Backend unit that ends in reviewed pull requests.

Suggested starting points; a project brief names its own primary and secondary targets before it starts.

| Project | Maturity | Primary units | Secondary units | Other roadmaps |
| --- | --- | --- | --- | --- |
| P1-BE-1 Small API with a contract and tests | P1 | BE-1.1, BE-1.3, BE-2.1, BE-2.2, BE-11.2 | BE-2.3, BE-2.4, BE-4.2 | Python |
| P1-BE-2 Service that calls an outside API safely | P1 | BE-5.1, BE-5.2, BE-5.4, BE-11.4 | BE-5.3, BE-4.2 | Networking / Web |
| P1-BE-3 Notes service with saved data and ownership | P1 | BE-6.2, BE-6.3, BE-7.4, BE-7.5, BE-11.3 | BE-7.2, BE-7.3, BE-1.6 | Database / SQL |
| P2-BE-1 Authenticated multi-user API with security checks | P2 | BE-7.2, BE-7.5, BE-10.3, BE-12.1, BE-12.2 | BE-12.3, BE-13.1, BE-13.4 | Database / SQL, Networking / Web |
| P2-BE-2 Service with background work, caching and workers | P2 | BE-8.2, BE-8.3, BE-9.1, BE-9.3, BE-16.2 | BE-9.2, BE-9.4, BE-8.5 | OS / Process |
| P3-BE-1 Portfolio: hardened, observable service | P3 | BE-17.2, BE-17.3, BE-17.4 | BE-12.4, BE-12.5, BE-14.1, BE-13.3 | Git, Software Design |
| P4-BE-1 Capstone: backend for an AI feature | P4 | BE-17.1, BE-17.2, BE-17.5, BE-17.6 | BE-15.1, BE-16.1 | AI Engineering (AI-17.x), Database / SQL, System Architecture |

**Open item (PR skills):** the Git roadmap has one pull-request unit today (GIT-3.4). Description writing, small pull requests, answering review, reviewing others, automatic checks and AI-written pull requests become Git units earlier in the Git upgrade, with these projects as the practice.

Not yet done: detailed teaching tasks per unit. The app does not read this roadmap yet; app work is paused for roadmaps beyond Python.

## Decisions (2026-10-31)

1. Approved by Asheesh: slot Networking v2 and Database v2 into this path; Database window functions cut.
2. The app loader still reads v2. Moving it to v3 is a code change for the build thread.
