---
title: Networking / Web Foundations Roadmap v2
created-date: 2026-10-31
status: approved
approved-date: 2026-10-31
version: "2.0"
supersedes: "Networking / Web Foundations Supporting Track v1 (22 units, Competency Model codes)"
governed-by: "AI-Era Programming Skills Framework v1 (27 skills); Learning Method v2 with Amendment A1 (2026-10-31)"
roadmap-role: "Supporting roadmap, slotted into the Python and Backend path"
ai-involvement: collaborative
ai-provider: Claude
tags:
  - "#claude"
---

> [!info] Provenance
> AI-drafted with Claude on 2026-10-31 at Asheesh's direction. **The scope (which units are kept, merged or dropped) and their place in the path were approved by Asheesh on 2026-10-31.** Target skills, goal levels, Methods, concept lines and outcome lines are new AI-drafted wording, checked by script against the Framework and Learning Method v2, and not yet reviewed by Asheesh. Detailed teaching tasks per unit are still to be written. The v1 file stays in `reference/` until it is moved to history.

# Networking / Web Foundations Roadmap v2

**Purpose.** The minimum networking a backend or AI-application engineer needs to trace a request and locate a failure. HTTP methods, status codes, idempotency and CORS stay in the Backend roadmap.

## What changed from v1

- **Converted to the AI-Era Programming Skills Framework.** Each unit has one to three target skills from the 27, each with a goal level, a one-line concept for Explain and the CO-6 check, a Methods list (Explain first, then the main activity of each target skill) and an outcome line that can be graded without AI. The old five competencies are gone.
- **6 units replace 15 v1 units.** Small v1 units were merged into units the size of a Python unit; each unit lists the v1 units it replaces. Dropped: Already in Backend: NET-2.4, 2.5, 2.7 (methods, status codes, idempotency and caching: BE-1.2, BE-1.6), NET-3.1, 3.2 (same-origin and CORS: BE-10.3). Supporting: NET-1.5 (UDP, now awareness in NET-0.2), NET-2.8 (HTTP versions, now awareness in NET-0.4).
- **Entry rule (Learning Method Amendment A1).** No skill enters the learning path above Apply, and no skill rises more than one level from one unit to the next. Levels here are set for where these units sit in the path, after the Python units that precede them.
- **Slotted into the path.** Units are taught where the path first needs them, not as a separate course run after Python (see "Place in the path").
- **New unit IDs.** IDs restart at `NET-0.1`. The "Replaces (v1)" field maps each one to the old IDs.

## Place in the path

| Stage | Title | Taught | Units |
| --- | --- | --- | --- |
| 0 | How web requests travel | at the start of Backend, before BE-0.1 | 6 |

**Course project.** No separate project: NET-0.6 failure location is used again in Backend Stage 17 incident work.

## Table 1: sequence, target skills and methods

| # | Unit | Stage | Targets (goal level) | Methods |
| --- | --- | --- | --- | --- |
| 1 | NET-0.1 Tracing a request: URL, DNS, IP and ports | 0 | CO-2 (Adapt), CO-5 (Adapt) | Explain → Trace |
| 2 | NET-0.2 TCP connections, reuse and pooling | 0 | CO-6 (Adapt), DE-6 (Adapt) | Explain → Evaluate |
| 3 | NET-0.3 TLS and HTTPS | 0 | CO-6 (Adapt), VE-4 (Adapt) | Explain → Debug & Validate |
| 4 | NET-0.4 Reading raw HTTP messages and headers | 0 | CO-3 (Adapt), VE-4 (Adapt) | Explain → Trace → Debug & Validate |
| 5 | NET-0.5 Proxies, gateways, load balancers and CDNs | 0 | CO-5 (Adapt), DE-4 (Adapt) | Explain → Trace → Direct |
| 6 | NET-0.6 Locating timeouts and failures across layers | 0 | VE-3 (Adapt), VE-4 (Adapt) | Explain → Debug & Validate |

The CO-6 concept check runs in every unit as part of Explain and is a target only where listed.

## Table 2: stage, unit and topics

| Stage | Unit | Topics |
| --- | --- | --- |
| 0 | NET-0.1 Tracing a request: URL, DNS, IP and ports | scheme, host, port, path, query and origin; DNS resolution at application depth; IP addresses and ports as endpoints; client, server and intermediary roles; `curl -v` |
|  | NET-0.2 TCP connections, reuse and pooling | TCP's role for HTTP; handshake cost; keep-alive; connection pools in HTTP clients; UDP (awareness) |
|  | NET-0.3 TLS and HTTPS | encryption, integrity and server identity; certificates and certificate authorities; hostname checks; HTTP versus HTTPS; never disabling verification to make an error go away |
|  | NET-0.4 Reading raw HTTP messages and headers | request line; status line; common headers: Host, Content-Type, Content-Length, Authorization, Accept, Cache-Control; bodies; HTTP versions (awareness) |
|  | NET-0.5 Proxies, gateways, load balancers and CDNs | forward and reverse proxies; API gateways; load balancers; CDNs and caching (awareness); forwarded headers; request IDs |
|  | NET-0.6 Locating timeouts and failures across layers | connect, read and total timeouts; DNS, TCP, TLS, proxy and application failures; 502, 503 and 504; client-side versus server-side evidence |

## Unit details

### Stage 0: How web requests travel

#### NET-0.1 Tracing a request: URL, DNS, IP and ports

- **Objective:** Can trace a web request from URL to response at high level, naming each step and the evidence it leaves.
- **The concept (Explain):** A request is a chain: name to address, address to connection, connection to HTTP.
- **Target skills:** CO-2 to Adapt; CO-5 to Adapt
- **Methods:** Explain → Trace
- **Outcome (measured at unit end):** CO-2: traces a request step by step (DNS lookup, connect to IP and port, TLS, HTTP request and response) using `curl -v` output. CO-5: sketches client, DNS, proxy and server and what each depends on.
- **Topics:** scheme, host, port, path, query and origin; DNS resolution at application depth; IP addresses and ports as endpoints; client, server and intermediary roles; `curl -v`
- **Prerequisites:** PY-8.4 | **Importance:** Foundational | **Replaces (v1):** NET-0.1, NET-0.2, NET-1.1, NET-1.2, NET-1.3

#### NET-0.2 TCP connections, reuse and pooling

- **Objective:** Can explain what a TCP connection gives HTTP, why opening one costs time, and when to reuse connections.
- **The concept (Explain):** A connection is set up once and costs time; reusing it saves that time on every later request.
- **Target skills:** CO-6 to Adapt; DE-6 to Adapt
- **Methods:** Explain → Evaluate
- **Outcome (measured at unit end):** CO-6: explains connection setup in their own words with an example and a non-example, and corrects a wrong explanation. DE-6: decides between one shared client and a client per request in an `httpx` script, with the reason.
- **Topics:** TCP's role for HTTP; handshake cost; keep-alive; connection pools in HTTP clients; UDP (awareness)
- **Prerequisites:** NET-0.1 | **Importance:** Core | **Replaces (v1):** NET-1.4, NET-4.3

#### NET-0.3 TLS and HTTPS

- **Objective:** Can explain what TLS adds to a connection and diagnose common certificate errors.
- **The concept (Explain):** TLS proves who the server is and keeps the conversation private and unaltered; it does not make the server trustworthy.
- **Target skills:** CO-6 to Adapt; VE-4 to Adapt
- **Methods:** Explain → Debug & Validate
- **Outcome (measured at unit end):** CO-6: explains what HTTPS guarantees and what it does not. VE-4: reads three certificate errors (expired, wrong host, unknown issuer) and names the cause of each.
- **Topics:** encryption, integrity and server identity; certificates and certificate authorities; hostname checks; HTTP versus HTTPS; never disabling verification to make an error go away
- **Prerequisites:** NET-0.1 | **Importance:** Core | **Replaces (v1):** NET-2.1, NET-2.2

#### NET-0.4 Reading raw HTTP messages and headers

- **Objective:** Can read a raw HTTP request and response and use headers as evidence.
- **The concept (Explain):** An HTTP message is a start line, headers and an optional body; the headers say how to read the body.
- **Target skills:** CO-3 to Adapt; VE-4 to Adapt
- **Methods:** Explain → Trace → Debug & Validate
- **Outcome (measured at unit end):** CO-3: explains every line of a raw request and response. VE-4: finds why a JSON body was rejected (a wrong `Content-Type`) from the raw exchange.
- **Topics:** request line; status line; common headers: Host, Content-Type, Content-Length, Authorization, Accept, Cache-Control; bodies; HTTP versions (awareness)
- **Prerequisites:** NET-0.1 | **Importance:** Foundational | **Replaces (v1):** NET-2.3, NET-2.6

#### NET-0.5 Proxies, gateways, load balancers and CDNs

- **Objective:** Can say where intermediaries sit in front of a service and which evidence each one adds.
- **The concept (Explain):** Between the client and your code there are often other servers, and each can change or answer the request.
- **Target skills:** CO-5 to Adapt; DE-4 to Adapt
- **Methods:** Explain → Trace → Direct
- **Outcome (measured at unit end):** CO-5: sketches where a reverse proxy, load balancer and CDN sit for one service. DE-4: picks which log or header (X-Forwarded-For, Via, cache headers, request ID) answers a given question.
- **Topics:** forward and reverse proxies; API gateways; load balancers; CDNs and caching (awareness); forwarded headers; request IDs
- **Prerequisites:** NET-0.4 | **Importance:** Core | **Replaces (v1):** NET-4.1, NET-4.2

#### NET-0.6 Locating timeouts and failures across layers

- **Objective:** Can locate a failed or slow request to the layer that caused it from the evidence it leaves.
- **The concept (Explain):** Each layer fails in its own way, and the error or delay tells you which layer to look at.
- **Target skills:** VE-3 to Adapt; VE-4 to Adapt
- **Methods:** Explain → Debug & Validate
- **Outcome (measured at unit end):** VE-3 and VE-4: locates five failures (DNS failure, connect timeout, TLS error, 502 from a proxy, slow application) from their evidence, one hypothesis at a time.
- **Topics:** connect, read and total timeouts; DNS, TCP, TLS, proxy and application failures; 502, 503 and 504; client-side versus server-side evidence
- **Prerequisites:** NET-0.2, NET-0.3, NET-0.5 | **Importance:** Core | **Replaces (v1):** NET-4.4, NET-4.5

## Skill coverage (target skills, this roadmap)

6 units carry 12 targets: Adapt 12. Skills not listed are trained in the Python, Backend and AI Engineering roadmaps.

| Skill | Units | Highest level |
| --- | --- | --- |
| CO-2 | 1 | Adapt |
| CO-3 | 1 | Adapt |
| CO-5 | 2 | Adapt |
| CO-6 | 2 | Adapt |
| VE-3 | 1 | Adapt |
| VE-4 | 3 | Adapt |
| DE-4 | 1 | Adapt |
| DE-6 | 1 | Adapt |

## Decisions

1. **Scope, cuts and placement** approved by Asheesh on 2026-10-31 (review "New roadmaps: framework fit and scope").
2. **Wording still to review:** target skills, levels, concept and outcome lines.
3. **Stage builds:** every stage needs one build (owner rule). Not yet written for this roadmap.
