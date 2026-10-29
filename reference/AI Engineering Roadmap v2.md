---
title: AI Engineering Roadmap v2
created-date: 2026-10-18
status: approved
approved-date: 2026-10-18
version: "2.0"
supersedes: "AI Engineering Roadmap v1.1 and the AI Engineering skill map (AI Engineering under AI-Era Skills v1), both now in history/"
governed-by: "AI-Era Programming Skills Framework v1 (27 skills); Learning Method v2 (approved 2026-10-17)"
roadmap-role: "Spine roadmap (Python, then Backend, then AI Engineering)"
ai-involvement: collaborative
ai-provider: Claude
tags:
  - "#claude"
---

> [!info] Provenance
> AI-drafted with Claude on 2026-10-18 at Asheesh's direction and **approved by Asheesh the same day**. AI Engineering Roadmap v1.1 is unchanged and archived in history/. Unit objectives and topics come from v1.1 unless marked (new) or moved; target skills, Methods, concepts and outcomes are new and unreviewed. Outcome lines are drafted wording, not yet tested with learners. Detailed teaching tasks per unit are still to be written.

# AI Engineering Roadmap v2

## What changed from v1.1

- **Each unit has one to four target skills**, each with a goal level, taken from the Framework's 27 skills (the old five competencies are gone). Skills not listed come up only as part of the work.
- **Each unit has a one-line concept** that Explain teaches and the CO-6 check tests, a **Methods** list (Explain first) and an **Outcome** line saying what is measured when the unit ends.
- **7 new units** fill gaps: AI-1.5, AI-2.7, AI-2.8, AI-7.5, AI-10.5, AI-12.6, AI-12.7.
- **Two units moved earlier** (IDs unchanged): **Evaluation foundations (AI-5.1 to AI-5.5)** is taught right after AI-2.2, because AI-2.3 and AI-2.5 need an eval set; **AI-12.4 (classify data before sending)** is taught right after AI-1.1, because learners send data to a provider from the first call.
- **Goal levels** follow v1.1 (no unit requires Own by default), with Own set only where Asheesh approved it: **AI-17.2** (BU-3) and **AI-17.5** (VE-3, VE-4). AI-15.4 and AI-16.1 were "Understand / Apply" and are now **Understand**; Apply evidence is recorded if it appears.
- **Backend is a soft prerequisite only where named.** Units that need a backend skill list the specific Backend unit (BE-x.y) as "soft:" in their prerequisites. Finishing the whole Backend roadmap first is not required; the learner is routed to the one missing Backend unit. Both orders work for the spine (Python, then Backend, then AI Engineering), because the AI units only need the listed Backend units.
- **Python entry point:** a learner should have finished Python through Stage 8 (PY-8.2 structured data, PY-8.3 configuration, PY-8.4 HTTP services) before AI-1.1.
- **Skill practice is balanced** across the roadmap (see the coverage table). The old gaps for DE-2, CO-2, CO-5, CO-6 and BU-5 are closed.
- Existing unit IDs never change; the sequence below is the order. The old Stage numbers are kept as labels.

## Scope and boundaries (kept from v1.1, shortened)

**Purpose.** The engineering capability to build, evaluate, debug, secure and evolve applications powered by foundation models. The central question: can the learner turn probabilistic model capability into a feature or system whose behaviour is explicit, testable, bounded, observable, safe enough for its use case, and understandable in cost and operation? This is an AI application engineering roadmap, not machine-learning research. Provider-neutral; current official provider documentation is read during execution.

**Upstream:** Python, Backend, Database / SQL, Software Design, Practical DSA, Networking / Web, OS / Process, Git. AI Engineering does not wait for all of them; the nearest missing prerequisite is pulled in as needed.

**This roadmap owns:** model and provider API use as AI behaviour; model selection; prompts and context; structured outputs; tool calling and the execution loop; embeddings and semantic retrieval at application depth; RAG ingestion, chunking, retrieval, grounding and attribution; AI evaluation (datasets, deterministic, human and model-based, regression); agent and workflow construction and its evaluation; AI-specific safety, security and privacy boundaries; AI tracing; latency, cost and token reasoning; model and provider lifecycle; integrated AI-system engineering.

**Other roadmaps own:** Backend (HTTP service behaviour, auth, persistence integration, jobs, general testing and resilience); Database / SQL (relational schema, SQL, transactions, indexes); Software Design (responsibility allocation, interfaces, patterns); System Architecture (whole-system decomposition, distributed design, system-level reliability); Organizational AI / Governance (policy, accountability, risk acceptance). A single application may give evidence in several roadmaps, but each claim stays with the roadmap that owns it (see AI-17.7).

**Outside default scope:** training foundation models, deep neural-network mathematics, transformer derivations, GPU or CUDA work, distributed training, RLHF, exhaustive fine-tuning, ML-theory interview prep, vision, speech and reinforcement-learning research, building vector databases, building agent frameworks.

**Deferred or need-driven:** transformer maths depth, full MLOps for training, fine-tuning implementation depth, RLHF/DPO, synthetic-data work, advanced multimodal and realtime voice, computer-use agents, multi-agent depth (after single-agent evidence), vector-database internals, embedding-model training, GPU serving, self-hosted model serving, AI red-teaming depth, regulatory compliance implementation, tool standards such as MCP and local or open models (kept out for now by Asheesh's decision on 2026-10-18).

**Authoritative-source habit.** Provider behaviour changes quickly. Read, in order: current official provider documentation; standards owners (OWASP GenAI, NIST); provider architecture and evaluation guidance; research literature; strong practitioner sources; a chat assistant's explanation last. Keep provider-specific detail separate from the stable requirement. Do not memorise model names or API shapes.

**Anti-bloat rule.** The roadmap is broad; a learner's path is narrow. For example, "build grounded document Q&A" needs prompts, evaluation, embeddings, ingestion, RAG and RAG evaluation, not agents, fine-tuning or multimodal. Follow the units the current objective needs.

**Lock rule (carried over).** Do not revise the terrain because a provider releases a model, a framework adds an abstraction, a technique becomes fashionable or a vendor renames an API. Ask: is this a durable engineering capability, or only today's mechanism for one?

## Table 1: sequence, target skills and methods

| # | Unit | Stage | Targets (goal level) | Methods |
| --- | --- | --- | --- | --- |
| 1 | AI-0.1 Model capability versus application capability | 0 | CO-4 (Apply), CO-5 (Apply), CO-6 (Apply), SP-3 (Apply) | Explain → Decompose |
| 2 | AI-0.2 Probabilistic and non-deterministic behaviour | 0 | CO-1 (Adapt), VE-1 (Adapt), VE-6 (Adapt), DE-1 (Adapt) | Explain → Predict → Debug & Validate → Evaluate |
| 3 | AI-0.3 Training, inference, context, tokens and embeddings | 0 | CO-1 (Apply), CO-4 (Apply), DE-2 (Apply) | Explain → Predict → Direct |
| 4 | AI-0.4 Appropriate and inappropriate model responsibilities | 0 | SP-1 (Adapt), SP-3 (Adapt), DE-3 (Adapt), DE-6 (Adapt) | Explain → Specify → Decompose → Direct → Evaluate |
| 5 | AI-1.1 Make and inspect a model API request | 1 | CO-3 (Apply), BU-3 (Apply), DE-4 (Apply) | Explain → Build → Direct |
| 6 | AI-12.4 Classify data before sending it to a model or tool *(moved)* | 12 | SP-1 (Apply), DE-5 (Apply), DE-3 (Apply) | Explain → Specify → Direct |
| 7 | AI-1.5 Stream a response **(new)** | 1 | BU-1 (Apply), BU-3 (Apply), VE-6 (Apply), BU-4 (Apply) | Explain → Modify → Build → Debug & Validate |
| 8 | AI-1.2 Provider integration behind a focused boundary | 1 | SP-3 (Adapt), BU-1 (Adapt), BU-4 (Adapt), DE-6 (Adapt) | Explain → Decompose → Modify → Evaluate |
| 9 | AI-1.3 Select a model from requirements | 1 | SP-1 (Adapt), DE-4 (Adapt), DE-6 (Adapt) | Explain → Specify → Direct → Evaluate |
| 10 | AI-1.4 Provider and model features as versioned capabilities | 1 | CO-3 (Adapt), DE-1 (Adapt), DE-2 (Adapt), DE-4 (Adapt) | Explain → Evaluate → Direct |
| 11 | AI-2.1 Define the AI task before writing the prompt | 2 | SP-1 (Adapt), SP-2 (Adapt), SP-4 (Adapt), VE-1 (Adapt) | Explain → Specify → Debug & Validate |
| 12 | AI-2.2 Separate instructions, context, input, examples and output requirements | 2 | CO-3 (Adapt), BU-1 (Adapt), BU-2 (Adapt), DE-5 (Adapt) | Explain → Modify → Direct |
| 13 | AI-5.1 Task-specific quality criteria *(moved)* | 5 | SP-1 (Adapt), SP-2 (Adapt), VE-1 (Adapt), CO-6 (Adapt) | Explain → Specify → Debug & Validate |
| 14 | AI-5.2 Representative evaluation dataset | 5 | SP-3 (Adapt), VE-1 (Adapt), VE-6 (Adapt) | Explain → Decompose → Debug & Validate |
| 15 | AI-5.3 Choose deterministic, human and model-based evaluation | 5 | VE-1 (Adapt), DE-3 (Adapt), DE-6 (Adapt) | Explain → Debug & Validate → Direct → Evaluate |
| 16 | AI-5.4 Calibrate model-based judges against human judgment | 5 | VE-2 (Apply), DE-1 (Apply), DE-4 (Apply) | Explain → Debug & Validate → Evaluate → Direct |
| 17 | AI-5.5 Compare prompt, model, retrieval or tool changes with evaluations | 5 | VE-3 (Adapt), VE-5 (Adapt), DE-1 (Adapt) | Explain → Debug & Validate → Evaluate |
| 18 | AI-2.4 Context as a finite engineering resource | 2 | SP-4 (Adapt), DE-1 (Adapt), DE-6 (Adapt), CO-6 (Adapt) | Explain → Specify → Evaluate |
| 19 | AI-2.3 Zero-shot, one-shot and few-shot prompting | 2 | BU-2 (Apply), VE-3 (Apply), DE-1 (Apply), DE-6 (Apply) | Explain → Modify → Debug & Validate → Evaluate |
| 20 | AI-2.5 Diagnose prompt and context failures with smallest-change experiments | 2 | SP-4 (Adapt), VE-3 (Adapt), VE-5 (Adapt), BU-5 (Adapt) | Explain → Specify → Debug & Validate → Modify |
| 21 | AI-2.7 Conversation history and memory **(new)** | 2 | CO-2 (Adapt), BU-1 (Adapt), DE-6 (Adapt), CO-5 (Adapt) | Explain → Trace → Modify → Evaluate |
| 22 | AI-2.8 Prompts as versioned, reviewed artifacts **(new)** | 2 | BU-5 (Adapt), VE-5 (Adapt), DE-1 (Adapt), BU-4 (Adapt) | Explain → Modify → Debug & Validate → Evaluate |
| 23 | AI-2.6 Prompting and reasoning patterns | 2 | CO-4 (Apply), SP-3 (Apply), VE-3 (Apply), DE-6 (Apply) | Explain → Decompose → Debug & Validate → Evaluate |
| 24 | AI-3.1 Schema-constrained outputs | 3 | BU-3 (Adapt), VE-1 (Adapt), DE-1 (Adapt), CO-1 (Adapt) | Explain → Build → Debug & Validate → Evaluate → Predict |
| 25 | AI-3.2 Validate model output beyond schema shape | 3 | BU-1 (Adapt), VE-1 (Adapt), VE-6 (Adapt), BU-2 (Adapt) | Explain → Modify → Debug & Validate |
| 26 | AI-3.3 Failure handling for refusal, truncation, invalid or incomplete output | 3 | VE-2 (Adapt), VE-4 (Adapt), DE-1 (Adapt), CO-2 (Adapt) | Explain → Debug & Validate → Evaluate → Trace |
| 27 | AI-4.1 Tool contracts | 4 | SP-2 (Adapt), SP-4 (Adapt), BU-4 (Adapt), DE-1 (Adapt) | Explain → Specify → Modify → Evaluate |
| 28 | AI-4.2 The model, tool, result, model loop | 4 | BU-1 (Apply), BU-3 (Apply), VE-4 (Apply), VE-6 (Apply) | Explain → Modify → Build → Debug & Validate |
| 29 | AI-4.3 Tool execution under application authority | 4 | SP-1 (Adapt), VE-6 (Adapt), DE-5 (Adapt) | Explain → Specify → Debug & Validate → Direct |
| 30 | AI-4.4 Evaluate tool selection and argument quality | 4 | VE-1 (Adapt), VE-3 (Adapt), DE-1 (Adapt), CO-1 (Adapt) | Explain → Debug & Validate → Evaluate → Predict |
| 31 | AI-6.1 Embeddings at application-engineering depth | 6 | CO-1 (Apply), CO-4 (Apply), CO-6 (Apply), DE-2 (Apply) | Explain → Predict → Direct |
| 32 | AI-6.2 Semantic similarity and retrieval | 6 | BU-3 (Apply), VE-6 (Apply), DE-4 (Apply), CO-5 (Apply) | Explain → Build → Debug & Validate → Direct |
| 33 | AI-6.3 Similarity, top-k, thresholds and metadata filters | 6 | VE-3 (Adapt), DE-6 (Adapt) | Explain → Debug & Validate → Evaluate |
| 34 | AI-7.1 Ingestion with source traceability | 7 | SP-3 (Adapt), BU-1 (Adapt), BU-3 (Adapt), DE-1 (Adapt) | Explain → Decompose → Modify → Build → Evaluate |
| 35 | AI-7.5 Parse documents before chunking **(new)** | 7 | BU-3 (Adapt), VE-1 (Adapt), VE-6 (Adapt) | Explain → Build → Debug & Validate |
| 36 | AI-7.2 Chunking strategy | 7 | SP-1 (Adapt), VE-3 (Adapt), DE-6 (Adapt) | Explain → Specify → Debug & Validate → Evaluate |
| 37 | AI-7.3 Metadata and enrichment | 7 | BU-4 (Apply), DE-1 (Apply), DE-5 (Apply), BU-2 (Apply) | Explain → Modify → Evaluate → Direct |
| 38 | AI-7.4 Re-ingestion, updates and deletion | 7 | BU-1 (Adapt), VE-1 (Adapt), VE-2 (Adapt), VE-5 (Adapt) | Explain → Modify → Debug & Validate |
| 39 | AI-8.1 Query, retrieve, context, generate pipeline | 8 | SP-3 (Adapt), BU-1 (Adapt), BU-3 (Adapt), CO-5 (Adapt) | Explain → Decompose → Modify → Build |
| 40 | AI-8.2 Semantic, keyword, hybrid and multi-query retrieval | 8 | VE-3 (Adapt), DE-4 (Adapt), DE-6 (Adapt), DE-2 (Adapt) | Explain → Debug & Validate → Direct → Evaluate |
| 41 | AI-8.3 Reranking | 8 | BU-3 (Apply), DE-1 (Apply), DE-6 (Apply) | Explain → Build → Evaluate |
| 42 | AI-8.4 Context that keeps source boundaries | 8 | SP-2 (Adapt), BU-2 (Adapt), DE-5 (Adapt), CO-6 (Adapt) | Explain → Specify → Modify → Direct |
| 43 | AI-8.5 Missing, conflicting or insufficient evidence | 8 | SP-1 (Adapt), VE-1 (Adapt), VE-6 (Adapt), DE-1 (Adapt) | Explain → Specify → Debug & Validate → Evaluate |
| 44 | AI-8.6 Verifiable source attribution | 8 | BU-1 (Apply), VE-1 (Apply), VE-2 (Apply) | Explain → Modify → Debug & Validate |
| 45 | AI-9.1 Evaluate retrieval separately from generation | 9 | SP-3 (Adapt), VE-2 (Adapt), VE-3 (Adapt), DE-2 (Adapt) | Explain → Decompose → Debug & Validate → Direct |
| 46 | AI-9.2 Groundedness, relevance and completeness | 9 | VE-1 (Adapt), DE-1 (Adapt), DE-4 (Adapt) | Explain → Debug & Validate → Evaluate → Direct |
| 47 | AI-9.3 Improve RAG with evidence-driven experiments | 9 | BU-5 (Adapt), VE-3 (Adapt), VE-5 (Adapt), DE-1 (Adapt) | Explain → Modify → Debug & Validate → Evaluate |
| 48 | AI-10.1 Workflow, orchestration or agent loop | 10 | SP-1 (Adapt), SP-3 (Adapt), DE-3 (Adapt), DE-6 (Adapt) | Explain → Specify → Decompose → Direct → Evaluate |
| 49 | AI-10.2 Agent instructions, tools and stop conditions | 10 | SP-2 (Adapt), BU-2 (Adapt), DE-3 (Adapt), DE-5 (Adapt) | Explain → Specify → Modify → Direct |
| 50 | AI-10.3 Single-agent tool-use loop | 10 | BU-1 (Apply), BU-3 (Apply), VE-1 (Apply), VE-6 (Apply) | Explain → Modify → Build → Debug & Validate |
| 51 | AI-10.4 Prefer the simpler workflow | 10 | VE-3 (Adapt), DE-1 (Adapt), DE-6 (Adapt), CO-4 (Adapt) | Explain → Debug & Validate → Evaluate |
| 52 | AI-10.5 Choose and read an AI framework **(new)** | 10 | CO-3 (Adapt), DE-2 (Adapt), DE-4 (Adapt), DE-6 (Adapt) | Explain → Direct → Evaluate |
| 53 | AI-11.1 Evaluate tool-use quality | 11 | VE-1 (Adapt), VE-2 (Adapt), DE-1 (Adapt) | Explain → Debug & Validate → Evaluate |
| 54 | AI-11.2 Evaluate end-to-end task completion | 11 | SP-2 (Adapt), VE-1 (Adapt), VE-6 (Adapt), CO-6 (Adapt) | Explain → Specify → Debug & Validate |
| 55 | AI-11.3 Inspect agent traces | 11 | CO-2 (Adapt), SP-3 (Adapt), VE-2 (Adapt), VE-3 (Adapt) | Explain → Trace → Decompose → Debug & Validate |
| 56 | AI-12.1 Direct and indirect prompt injection | 12 | CO-3 (Adapt), CO-6 (Adapt), VE-6 (Adapt), DE-5 (Adapt) | Explain → Debug & Validate → Direct |
| 57 | AI-12.2 Validate and constrain output before side effects | 12 | VE-1 (Adapt), VE-6 (Adapt), DE-5 (Adapt), CO-1 (Adapt) | Explain → Debug & Validate → Direct → Predict |
| 58 | AI-12.3 Minimise agent functionality, permissions and autonomy | 12 | SP-1 (Adapt), DE-3 (Adapt), DE-5 (Adapt) | Explain → Specify → Direct |
| 59 | AI-12.6 Moderation and unsafe content **(new)** | 12 | VE-1 (Adapt), DE-5 (Adapt), DE-6 (Adapt) | Explain → Debug & Validate → Direct → Evaluate |
| 60 | AI-12.7 Abuse and unbounded consumption **(new)** | 12 | SP-4 (Adapt), VE-6 (Adapt), DE-5 (Adapt) | Explain → Specify → Debug & Validate → Direct |
| 61 | AI-12.5 Prevent leakage through prompts, logs, traces and outputs | 12 | VE-2 (Adapt), VE-6 (Adapt), DE-5 (Adapt), CO-5 (Adapt) | Explain → Debug & Validate → Direct |
| 62 | AI-13.1 Failure taxonomy | 13 | SP-3 (Adapt), VE-3 (Adapt), VE-4 (Adapt), CO-2 (Adapt) | Explain → Decompose → Debug & Validate → Trace |
| 63 | AI-13.2 Provider failures and incomplete responses | 13 | VE-4 (Adapt), VE-6 (Adapt), DE-1 (Adapt) | Explain → Debug & Validate → Evaluate |
| 64 | AI-13.3 Trace one AI request | 13 | BU-1 (Adapt), BU-3 (Adapt), VE-4 (Adapt), CO-2 (Adapt) | Explain → Modify → Build → Debug & Validate → Trace |
| 65 | AI-13.4 Connect production traces back to evaluation | 13 | VE-1 (Adapt), VE-5 (Adapt), DE-1 (Adapt) | Explain → Debug & Validate → Evaluate |
| 66 | AI-14.1 Latency by component | 14 | VE-3 (Adapt), DE-1 (Adapt), CO-2 (Adapt) | Explain → Debug & Validate → Evaluate → Trace |
| 67 | AI-14.2 Token and context cost | 14 | CO-1 (Apply), DE-6 (Apply) | Explain → Predict → Evaluate |
| 68 | AI-14.3 Optimise from measured requirements | 14 | VE-3 (Adapt), DE-6 (Adapt), BU-5 (Adapt) | Explain → Debug & Validate → Evaluate → Modify |
| 69 | AI-15.1 Model upgrades as behaviour changes | 15 | VE-2 (Adapt), VE-3 (Adapt), DE-1 (Adapt), DE-2 (Adapt) | Explain → Debug & Validate → Evaluate → Direct |
| 70 | AI-15.2 Provider substitution | 15 | SP-3 (Adapt), BU-1 (Adapt), BU-4 (Adapt), DE-6 (Adapt) | Explain → Decompose → Modify → Evaluate |
| 71 | AI-15.3 Prompting, retrieval, tools or fine-tuning | 15 | SP-1 (Adapt), SP-4 (Adapt), DE-6 (Adapt), CO-4 (Adapt) | Explain → Specify → Evaluate |
| 72 | AI-15.4 Fine-tuning at decision depth | 15 | CO-4 (Understand), CO-6 (Understand), DE-1 (Understand) | Explain → Evaluate |
| 73 | AI-16.1 Modalities as different contracts | 16 | CO-3 (Understand), DE-1 (Understand), DE-5 (Understand) | Explain → Evaluate → Direct |
| 74 | AI-16.2 Validate emerging capabilities | 16 | DE-1 (Apply), DE-4 (Apply), DE-6 (Apply) | Explain → Evaluate → Direct |
| 75 | AI-17.1 Design from a measurable requirement | 17 | SP-1 (Adapt), SP-2 (Adapt), SP-3 (Adapt), DE-6 (Adapt) | Explain → Specify → Decompose → Evaluate |
| 76 | AI-17.2 Implement with explicit boundaries | 17 | BU-2 (Adapt), BU-3 (Own), BU-5 (Adapt), DE-3 (Adapt) | Explain → Modify → Build → Direct |
| 77 | AI-17.3 Build and run a regression suite | 17 | BU-1 (Adapt), VE-1 (Adapt), VE-5 (Adapt), BU-4 (Adapt) | Explain → Modify → Debug & Validate |
| 78 | AI-17.4 Security review of inputs, outputs, retrieval and tools | 17 | VE-2 (Adapt), VE-6 (Adapt), DE-5 (Adapt), CO-5 (Adapt) | Explain → Debug & Validate → Direct |
| 79 | AI-17.5 Diagnose a failure from trace evidence | 17 | SP-3 (Adapt), VE-3 (Own), VE-4 (Own), DE-1 (Adapt) | Explain → Decompose → Debug & Validate → Evaluate |
| 80 | AI-17.6 Improve without hidden regression | 17 | BU-5 (Adapt), VE-3 (Adapt), VE-5 (Adapt), DE-6 (Adapt) | Explain → Modify → Debug & Validate → Evaluate |
| 81 | AI-17.7 Evidence without claim leakage | 17 | CO-4 (Apply), DE-1 (Apply) | Explain → Evaluate |

## Table 2: stage, unit and topics

| Stage | Unit | Topics |
| --- | --- | --- |
| 0 | AI-0.1 Model capability versus application capability | model versus application; instructions, context, tools, validation, state and policy as application jobs; deterministic control; where outputs go next |
|  | AI-0.2 Probabilistic and non-deterministic behaviour | probabilistic output; run-to-run variation; temperature awareness; plausible versus correct; where to use code, constraints or checks instead of trust |
|  | AI-0.3 Training, inference, context, tokens and embeddings | training versus inference; fixed parameters versus request context; tokenisation; context window; generative versus embedding representations; usage metadata |
|  | AI-0.4 Appropriate and inappropriate model responsibilities | model versus code versus retrieval versus query versus human review; reliability, cost and auditability; where free-form generation is a risk |
| 1 | AI-1.1 Make and inspect a model API request | request and response objects; instructions and input; usage, stop reason and error metadata; API keys kept out of code; transport versus model behaviour |
| 12 | AI-12.4 Classify data before sending it to a model or tool | sensitive, private, proprietary and regulated data; minimum necessary data; send, redact or never send; policy questions for a person; provider data terms awareness |
| 1 | AI-1.5 Stream a response | streaming events and chunks; assembling partial text; usage at the end of a stream; interruption and partial results; user-facing latency |
|  | AI-1.2 Provider integration behind a focused boundary | provider client interface; response translation; what stays provider-specific; wrapper libraries versus your own boundary |
|  | AI-1.3 Select a model from requirements | capability, quality, latency, cost and context limits; small sample comparison; documentation as source; not assuming the largest model |
|  | AI-1.4 Provider and model features as versioned capabilities | stable requirement versus provider mechanism; versioned capabilities; deprecations; official documentation first; isolating provider-specific code |
| 2 | AI-2.1 Define the AI task before writing the prompt | task, input, context and constraints; expected output; behaviour when unsure; worked examples as test cases; criteria before wording |
|  | AI-2.2 Separate instructions, context, input, examples and output requirements | prompt parts; delimiters; instruction hierarchy; untrusted text; examples; output requirements |
| 5 | AI-5.1 Task-specific quality criteria | observable criteria; correctness, groundedness, completeness, relevance, format, safety; criteria a reviewer could apply |
|  | AI-5.2 Representative evaluation dataset | normal, hard, edge and hostile cases; coverage; held-out cases; not tuning to the test set |
|  | AI-5.3 Choose deterministic, human and model-based evaluation | exact checks; human review; rubric judges; pairwise comparison; cost and reliability; the minimum sufficient combination |
|  | AI-5.4 Calibrate model-based judges against human judgment | judge prompts and rubrics; human-labelled examples; agreement; known judge biases; when to trust a judge |
|  | AI-5.5 Compare prompt, model, retrieval or tool changes with evaluations | comparable runs; per-case results; averages versus failures; noise; accept or reject with evidence |
| 2 | AI-2.4 Context as a finite engineering resource | context window; token budget; relevance; keeping constraints; ordering; cost of extra context |
|  | AI-2.3 Zero-shot, one-shot and few-shot prompting | zero-, one- and few-shot; choosing examples; accidental patterns; measuring the benefit |
|  | AI-2.5 Diagnose prompt and context failures with smallest-change experiments | hypothesis per change; one variable at a time; reruns; recording results; reversible changes |
|  | AI-2.7 Conversation history and memory | message history; rebuilding context each turn; summarising and trimming; session versus long-term memory; privacy of stored memory |
|  | AI-2.8 Prompts as versioned, reviewed artifacts | prompts in files; versions and diffs; a prompt change reviewed in a pull request; rolling back; linking a version to its eval results |
|  | AI-2.6 Prompting and reasoning patterns | iterative prompting; chaining; critique-and-revise; self-consistency; chain-of-thought as a pattern; tree-of-thought awareness; evidence over technique names |
| 3 | AI-3.1 Schema-constrained outputs | schemas; structured output features; structural versus semantic validity; schema design |
|  | AI-3.2 Validate model output beyond schema shape | range, total and existence checks; business rules; rejecting plausible wrong values |
|  | AI-3.3 Failure handling for refusal, truncation, invalid or incomplete output | refusals; truncation and stop reasons; invalid output; retry versus fail; explicit states |
| 4 | AI-4.1 Tool contracts | tool name, description, parameters and results; overlapping tools; typed arguments; result meaning |
|  | AI-4.2 The model, tool, result, model loop | tool-call detection; argument validation; executing trusted code; returning results; loop termination |
|  | AI-4.3 Tool execution under application authority | permissions; allowlists; side-effect limits; confirmation steps; enforcing outside the model |
|  | AI-4.4 Evaluate tool selection and argument quality | expected tool choices; ambiguous requests; argument checks; overlap; failure causes |
| 6 | AI-6.1 Embeddings at application-engineering depth | vectors; similarity; embedding versus generation; what embeddings do and do not capture |
|  | AI-6.2 Semantic similarity and retrieval | embedding documents and queries; vector stores; similarity search; inspecting results |
|  | AI-6.3 Similarity, top-k, thresholds and metadata filters | top-k; thresholds; filters; precision and recall; labelled queries |
| 7 | AI-7.1 Ingestion with source traceability | stable source IDs; metadata; provenance; pipeline stages; loader libraries |
|  | AI-7.5 Parse documents before chunking | text extraction; layout, tables and columns; OCR awareness; cleaning; checking parsed text |
|  | AI-7.2 Chunking strategy | fixed, heading-based, semantic chunking; size and overlap; testing against queries |
|  | AI-7.3 Metadata and enrichment | metadata for filters, ranking, traceability and access control; avoiding bloat |
|  | AI-7.4 Re-ingestion, updates and deletion | updates; deletions; duplicates; stale chunks; idempotent ingestion |
| 8 | AI-8.1 Query, retrieve, context, generate pipeline | retrieve, assemble, prompt, generate; inspectable stages; data flow |
|  | AI-8.2 Semantic, keyword, hybrid and multi-query retrieval | semantic and keyword search; hybrid retrieval; multi-query; measuring by query type |
|  | AI-8.3 Reranking | candidate retrieval versus ranking; rerankers; cost and latency |
|  | AI-8.4 Context that keeps source boundaries | source IDs; delimiters; instruction versus data; attribution support |
|  | AI-8.5 Missing, conflicting or insufficient evidence | abstaining; conflicting sources; qualified answers; no-evidence cases |
|  | AI-8.6 Verifiable source attribution | citing chunk IDs; checking citations against the trace; fabricated references |
| 9 | AI-9.1 Evaluate retrieval separately from generation | stage-by-stage diagnosis; retrieval metrics; generation checks |
|  | AI-9.2 Groundedness, relevance and completeness | groundedness; relevance; completeness; judge use and limits |
|  | AI-9.3 Improve RAG with evidence-driven experiments | single-variable experiments; per-case regression; keeping or dropping changes |
| 10 | AI-10.1 Workflow, orchestration or agent loop | fixed pipeline; orchestration; agent loop; predictability; control; cost |
|  | AI-10.2 Agent instructions, tools and stop conditions | agent task and tools; state; iteration caps; stop conditions; ReAct pattern; keeping authority in the application |
|  | AI-10.3 Single-agent tool-use loop | tool selection; state updates; termination; step limits |
|  | AI-10.4 Prefer the simpler workflow | agent versus workflow on the same cases; cost; speed; validation |
|  | AI-10.5 Choose and read an AI framework | frameworks for RAG and agents; reading their code; hidden prompts and defaults; lock-in; when plain code is simpler |
| 11 | AI-11.1 Evaluate tool-use quality | tool-choice scoring; argument validity; unnecessary calls; use of results |
|  | AI-11.2 Evaluate end-to-end task completion | task success criteria; final-state checks; multi-step evaluation |
|  | AI-11.3 Inspect agent traces | trace reading; state per step; divergence points; hypotheses |
| 12 | AI-12.1 Direct and indirect prompt injection | direct injection; indirect injection through retrieved documents; boundaries; defence in depth |
|  | AI-12.2 Validate and constrain output before side effects | output as untrusted input; allowlists; schema and rule checks; side effects |
|  | AI-12.3 Minimise agent functionality, permissions and autonomy | least privilege; scopes; credentials; autonomy limits; excessive agency |
|  | AI-12.6 Moderation and unsafe content | input and output moderation; provider moderation tools; false positives and negatives; handling flagged content |
|  | AI-12.7 Abuse and unbounded consumption | rate limits; token and cost caps; input size limits; loop limits; abuse patterns |
|  | AI-12.5 Prevent leakage through prompts, logs, traces and outputs | leakage paths; redaction; logging boundaries; access to traces |
| 13 | AI-13.1 Failure taxonomy | model, prompt, retrieval, tool, provider and application failures; evidence for each |
|  | AI-13.2 Provider failures and incomplete responses | rate limits; transport errors; context limits; incomplete output; handling per failure |
|  | AI-13.3 Trace one AI request | spans; trace metadata; latency and usage; avoiding sensitive content |
|  | AI-13.4 Connect production traces back to evaluation | failures to cases; regression suites; choosing representative cases |
| 14 | AI-14.1 Latency by component | per-stage timing; where time goes; measurement before change |
|  | AI-14.2 Token and context cost | input and output tokens; context size; retrieval depth; agent steps |
|  | AI-14.3 Optimise from measured requirements | model size; caching; batching; retrieval depth; workflow shape |
| 15 | AI-15.1 Model upgrades as behaviour changes | regression evaluation on a candidate model; format, tool, latency and cost changes |
|  | AI-15.2 Provider substitution | provider boundary; capability differences; wrapper trade-offs |
|  | AI-15.3 Prompting, retrieval, tools or fine-tuning | diagnosing capability gaps; fine-tuning as a last step |
|  | AI-15.4 Fine-tuning at decision depth | supervised tuning; dataset and evaluation needs; when it does not help |
| 16 | AI-16.1 Modalities as different contracts | image, audio and other inputs; file size and format; privacy; evaluation; injected text |
|  | AI-16.2 Validate emerging capabilities | preview versus stable; official docs; fallbacks |
| 17 | AI-17.1 Design from a measurable requirement | responsibilities; retrieval and tools; quality criteria; safety limits; operating targets |
|  | AI-17.2 Implement with explicit boundaries | multi-component AI feature; boundaries; replaceable parts; small pull requests |
|  | AI-17.3 Build and run a regression suite | representative cases; past failures; regression runs |
|  | AI-17.4 Security review of inputs, outputs, retrieval and tools | injection; leakage; permissions; unsafe output; excessive agency; resource limits |
|  | AI-17.5 Diagnose a failure from trace evidence | trace reading; failing boundary; targeted correction; cause versus symptom |
|  | AI-17.6 Improve without hidden regression | one change at a time; evaluation plus operating evidence; no hidden regression |
|  | AI-17.7 Evidence without claim leakage | evidence ownership; claim limits; separating roadmaps |

## Unit details


### Stage 0: AI-system mental model

#### AI-0.1 Model capability versus application capability

- **Objective:** Can explain that a model generates outputs while the surrounding application supplies instructions, context, tools, validation, state, policies and deterministic control.
- **The concept (Explain):** The model only generates; the application around it decides what it sees, what it may do, and what happens to the result.
- **Target skills:** CO-4 to Apply; CO-5 to Apply; CO-6 to Apply; SP-3 to Apply
- **Methods:** Explain → Decompose
- **Outcome (measured at unit end):** CO-4: says what the model contributes and what the code contributes in a chat app. CO-5: sketches the data flow between them. SP-3: splits a one-box design into model and non-model parts.
- **Topics:** model versus application; instructions, context, tools, validation, state and policy as application jobs; deterministic control; where outputs go next
- **Prerequisites:** PY-8.2, PY-8.3, PY-8.4 (Python through Stage 8) | **Importance:** Foundational | **Integration link:** Backend Engineering; Software Design / OOD / LLD

#### AI-0.2 Probabilistic and non-deterministic behaviour

- **Objective:** Can explain why plausible output is not proof of correctness and where evaluation, constraints, validation or deterministic code should replace trust in free-form generation.
- **The concept (Explain):** A fluent answer is a likely answer, not a checked one.
- **Target skills:** CO-1 to Adapt; VE-1 to Adapt; VE-6 to Adapt; DE-1 to Adapt
- **Methods:** Explain → Predict → Debug & Validate → Evaluate
- **Outcome (measured at unit end):** CO-1: predicts which parts of a summary will vary across five runs. VE-1: writes a check that catches a wrong but fluent answer. VE-6: tries inputs beyond 'it worked once'. DE-1: rejects a teammate's 'it worked once' claim with evidence.
- **Topics:** probabilistic output; run-to-run variation; temperature awareness; plausible versus correct; where to use code, constraints or checks instead of trust
- **Prerequisites:** AI-0.1 | **Importance:** Foundational

#### AI-0.3 Training, inference, context, tokens and embeddings

- **Objective:** Can distinguish training from inference, model parameters from request context, tokens from text, and generative output from embedding representations, without mathematics.
- **The concept (Explain):** A model does not remember your last request; everything it uses arrives in the request as tokens.
- **Target skills:** CO-1 to Apply; CO-4 to Apply; DE-2 to Apply
- **Methods:** Explain → Predict → Direct
- **Outcome (measured at unit end):** CO-1: predicts a request's token count and whether the model 'remembers' an earlier call. CO-4: explains each mismatch against the usage metadata. DE-2: asks a tool to explain a confusing term rather than to give the answer.
- **Topics:** training versus inference; fixed parameters versus request context; tokenisation; context window; generative versus embedding representations; usage metadata
- **Prerequisites:** AI-0.1 | **Importance:** Core

#### AI-0.4 Appropriate and inappropriate model responsibilities

- **Objective:** Can decide whether a task should use model generation, deterministic code, retrieval, a database query, validation logic or human review.
- **The concept (Explain):** Not every step belongs to the model; use the cheapest reliable tool for each step.
- **Target skills:** SP-1 to Adapt; SP-3 to Adapt; DE-3 to Adapt; DE-6 to Adapt
- **Methods:** Explain → Specify → Decompose → Direct → Evaluate
- **Outcome (measured at unit end):** SP-1: names what is unclear in a design that sends everything through an LLM. SP-3: splits it into model, code, query and human review. DE-3: gives a reason for each piece. DE-6: compares two splits by reliability and cost.
- **Topics:** model versus code versus retrieval versus query versus human review; reliability, cost and auditability; where free-form generation is a risk
- **Prerequisites:** AI-0.2 | **Importance:** Core


### Stage 1: Provider APIs and model selection

#### AI-1.1 Make and inspect a model API request

- **Objective:** Can construct a model request, provide instructions and input, inspect the response, find usage and error metadata, and separate provider transport behaviour from model output behaviour.
- **The concept (Explain):** A model call is an ordinary API call whose body and response have fields you can read.
- **Target skills:** CO-3 to Apply; BU-3 to Apply; DE-4 to Apply
- **Methods:** Explain → Build → Direct
- **Outcome (measured at unit end):** BU-3: calls a provider API from its current docs. CO-3: explains every field of the response in tool-drafted code. DE-4: finds the answer to a parameter question in the official docs.
- **Topics:** request and response objects; instructions and input; usage, stop reason and error metadata; API keys kept out of code; transport versus model behaviour
- **Prerequisites:** AI-0.1; PY-8.2, PY-8.3, PY-8.4; soft: BE-5.1 (typed external API client), BE-5.2 (timeouts) | **Importance:** Core | **Integration link:** Backend Engineering (external API basics)


### Stage 12: AI safety, security and data boundaries

#### AI-12.4 Classify data before sending it to a model or tool

- **Objective:** Can identify sensitive, private, proprietary, regulated or unnecessary data and decide whether it may enter model or provider context. (Taught here, right after the first API call.)
- **The concept (Explain):** Whatever goes into a request leaves your system; decide what may go before you send it.
- **Target skills:** SP-1 to Apply; DE-5 to Apply; DE-3 to Apply
- **Methods:** Explain → Specify → Direct
- **Outcome (measured at unit end):** SP-1: asks what each field is and who may see it. DE-5: marks each field send, redact or never send. DE-3: says which policy question needs a person.
- **Topics:** sensitive, private, proprietary and regulated data; minimum necessary data; send, redact or never send; policy questions for a person; provider data terms awareness
- **Prerequisites:** AI-1.1 | **Importance:** Core | **Integration link:** AI Governance (bridge) | **Moved:** Taught right after AI-1.1 (v1: Stage 12)


### Stage 1: Provider APIs and model selection

#### AI-1.5 Stream a response (new unit)

- **Objective:** Can receive a streamed model response, assemble it, and handle interrupted or partial streams.
- **The concept (Explain):** A stream delivers the answer in pieces, so the code must handle an answer that is half there.
- **Target skills:** BU-1 to Apply; BU-3 to Apply; VE-6 to Apply; BU-4 to Apply
- **Methods:** Explain → Modify → Build → Debug & Validate
- **Outcome (measured at unit end):** BU-3: reads a streamed response from the docs. BU-1: adapts a non-streaming call to stream without changing its results. VE-6: tries a dropped connection and an early stop. BU-4: keeps stream handling separate from the rest of the code.
- **Topics:** streaming events and chunks; assembling partial text; usage at the end of a stream; interruption and partial results; user-facing latency
- **Prerequisites:** AI-1.1 | **Importance:** Supporting | **Integration link:** Backend Engineering

#### AI-1.2 Provider integration behind a focused boundary

- **Objective:** Can isolate provider SDK and request details so application behaviour does not depend on one provider's response objects.
- **The concept (Explain):** Put the provider behind a small interface the rest of the code can use.
- **Target skills:** SP-3 to Adapt; BU-1 to Adapt; BU-4 to Adapt; DE-6 to Adapt
- **Methods:** Explain → Decompose → Modify → Evaluate
- **Outcome (measured at unit end):** SP-3: splits a script that passes raw SDK objects around. BU-1: moves them behind a small client without changing behaviour. BU-4: keeps the interface small. DE-6: compares it with adopting a wrapper library.
- **Topics:** provider client interface; response translation; what stays provider-specific; wrapper libraries versus your own boundary
- **Prerequisites:** AI-1.1 | **Importance:** Core | **Integration link:** Software Design / OOD / LLD (interfaces)

#### AI-1.3 Select a model from requirements

- **Objective:** Can compare candidate models on capability, quality, latency, cost and context needs from task-relevant evidence.
- **The concept (Explain):** The right model is the cheapest one that meets the measured requirements, not the newest or largest.
- **Target skills:** SP-1 to Adapt; DE-4 to Adapt; DE-6 to Adapt
- **Methods:** Explain → Specify → Direct → Evaluate
- **Outcome (measured at unit end):** SP-1: states the requirements first. DE-4: reads current model documentation for limits and prices. DE-6: compares three models on a 20-case sample and picks one with a reason.
- **Topics:** capability, quality, latency, cost and context limits; small sample comparison; documentation as source; not assuming the largest model
- **Prerequisites:** AI-0.2; AI-1.1 | **Importance:** Core

#### AI-1.4 Provider and model features as versioned capabilities

- **Objective:** Can tell stable application requirements from provider-specific mechanisms and check current documentation before depending on model-specific behaviour.
- **The concept (Explain):** A model feature is a versioned dependency; check what it promises today.
- **Target skills:** CO-3 to Adapt; DE-1 to Adapt; DE-2 to Adapt; DE-4 to Adapt
- **Methods:** Explain → Evaluate → Direct
- **Outcome (measured at unit end):** CO-3: finds the model-specific call in AI-written code. DE-2: asks a tool to explain a changelog entry rather than to rewrite the code. DE-4: checks the official docs. DE-1: accepts, changes or isolates the dependency with a reason.
- **Topics:** stable requirement versus provider mechanism; versioned capabilities; deprecations; official documentation first; isolating provider-specific code
- **Prerequisites:** AI-1.3 | **Importance:** Core


### Stage 2: Prompt and context engineering

#### AI-2.1 Define the AI task before writing the prompt

- **Objective:** Can specify the model's task, input, context, constraints, expected output, uncertainty behaviour and evaluation criteria before tuning prompt wording.
- **The concept (Explain):** Write down what a correct answer looks like before you write the prompt.
- **Target skills:** SP-1 to Adapt; SP-2 to Adapt; SP-4 to Adapt; VE-1 to Adapt
- **Methods:** Explain → Specify → Debug & Validate
- **Outcome (measured at unit end):** SP-1: asks the clarifying questions a vague request needs. SP-2: writes a task spec with 3-5 worked examples. SP-4: names the missing detail in a vague prompt that gave wrong answers. VE-1: turns the examples into the first checks.
- **Topics:** task, input, context and constraints; expected output; behaviour when unsure; worked examples as test cases; criteria before wording
- **Prerequisites:** AI-0.4 | **Importance:** Foundational

#### AI-2.2 Separate instructions, context, input, examples and output requirements

- **Objective:** Can structure prompts so instruction hierarchy and data boundaries are clear, and keep untrusted content apart from authoritative instructions.
- **The concept (Explain):** Instructions and untrusted text must not share the same slot.
- **Target skills:** CO-3 to Adapt; BU-1 to Adapt; BU-2 to Adapt; DE-5 to Adapt
- **Methods:** Explain → Modify → Direct
- **Outcome (measured at unit end):** CO-3: reads an unfamiliar prompt and labels its parts. BU-1 and BU-2: restructure it with delimiters and keep behaviour on existing cases. DE-5: moves untrusted text out of the instruction slot.
- **Topics:** prompt parts; delimiters; instruction hierarchy; untrusted text; examples; output requirements
- **Prerequisites:** AI-2.1 | **Importance:** Core


### Stage 5: Evaluation foundations (taught here, after AI-2.2)

#### AI-5.1 Task-specific quality criteria

- **Objective:** Can turn product and task expectations into observable criteria: correctness, groundedness, completeness, relevance, format, tool choice, safety or task completion.
- **The concept (Explain):** A criterion is only useful if someone else could apply it and get the same answer.
- **Target skills:** SP-1 to Adapt; SP-2 to Adapt; VE-1 to Adapt; CO-6 to Adapt
- **Methods:** Explain → Specify → Debug & Validate
- **Outcome (measured at unit end):** SP-1: asks what 'good' means for the task. SP-2: turns 'summaries should be good' into criteria a check or reviewer could apply. VE-1: writes one automatic check for each criterion that can be checked. CO-6: explains in own words what a quality criterion is, with an example and a non-example.
- **Topics:** observable criteria; correctness, groundedness, completeness, relevance, format, safety; criteria a reviewer could apply
- **Prerequisites:** AI-2.1 | **Importance:** Foundational | **Moved:** Taught right after AI-2.2 (v1: after Stage 4)

#### AI-5.2 Representative evaluation dataset

- **Objective:** Can build test cases for normal, difficult, edge and failure scenarios, not only the examples that motivated the implementation.
- **The concept (Explain):** An eval set that only holds the cases you built the prompt for will always look good.
- **Target skills:** SP-3 to Adapt; VE-1 to Adapt; VE-6 to Adapt
- **Methods:** Explain → Decompose → Debug & Validate
- **Outcome (measured at unit end):** SP-3: splits scenarios into groups. VE-1: builds a 30-case set. VE-6: shows it fails a plausible wrong prompt that the motivating examples alone would pass.
- **Topics:** normal, hard, edge and hostile cases; coverage; held-out cases; not tuning to the test set
- **Prerequisites:** AI-5.1 | **Importance:** Core

#### AI-5.3 Choose deterministic, human and model-based evaluation

- **Objective:** Can choose between exact checks, human judgment, rubric-based model judges and pairwise comparison, using the minimum sufficient combination.
- **The concept (Explain):** Use the cheapest method that can judge the criterion reliably.
- **Target skills:** VE-1 to Adapt; DE-3 to Adapt; DE-6 to Adapt
- **Methods:** Explain → Debug & Validate → Direct → Evaluate
- **Outcome (measured at unit end):** VE-1: writes exact checks where they work. DE-3: decides which criteria go to a model judge and which stay with a person. DE-6: compares methods by cost and reliability.
- **Topics:** exact checks; human review; rubric judges; pairwise comparison; cost and reliability; the minimum sufficient combination
- **Prerequisites:** AI-5.1 | **Importance:** Core

#### AI-5.4 Calibrate model-based judges against human judgment

- **Objective:** Can see that a model judge is fallible and check important judge behaviour against human-labelled examples before trusting automated scores.
- **The concept (Explain):** A judge is a model too; check it against people before you trust its score.
- **Target skills:** VE-2 to Apply; DE-1 to Apply; DE-4 to Apply
- **Methods:** Explain → Debug & Validate → Evaluate → Direct
- **Outcome (measured at unit end):** VE-2: finds where an AI-written judge disagrees with 20 human labels. DE-1: trusts, changes or drops it. DE-4: checks the provider's guidance on judging.
- **Topics:** judge prompts and rubrics; human-labelled examples; agreement; known judge biases; when to trust a judge
- **Prerequisites:** AI-5.3 | **Importance:** Core

#### AI-5.5 Compare prompt, model, retrieval or tool changes with evaluations

- **Objective:** Can run comparable evaluations before and after a change, read per-case failures instead of only averages, and decide whether the change is a real improvement.
- **The concept (Explain):** A change is better only if the same cases improve and none get worse.
- **Target skills:** VE-3 to Adapt; VE-5 to Adapt; DE-1 to Adapt
- **Methods:** Explain → Debug & Validate → Evaluate
- **Outcome (measured at unit end):** VE-3: states what the change should fix. VE-5: runs before and after on the same set. DE-1: accepts or rejects the change with the cases that decided it.
- **Topics:** comparable runs; per-case results; averages versus failures; noise; accept or reject with evidence
- **Prerequisites:** AI-5.2; AI-5.3 | **Importance:** Core


### Stage 2: Prompt and context engineering

#### AI-2.4 Context as a finite engineering resource

- **Objective:** Can decide what belongs in context, remove irrelevant material, keep required constraints, and reason about token and window limits.
- **The concept (Explain):** Context is a budget; every extra line costs money, speed and attention.
- **Target skills:** SP-4 to Adapt; DE-1 to Adapt; DE-6 to Adapt; CO-6 to Adapt
- **Methods:** Explain → Specify → Evaluate
- **Outcome (measured at unit end):** SP-4: spots the constraint a trimmed context lost. DE-1: accepts or rejects each removal. DE-6: justifies each cut against the token budget. CO-6: explains why context is a budget, with an example and a non-example.
- **Topics:** context window; token budget; relevance; keeping constraints; ordering; cost of extra context
- **Prerequisites:** AI-0.3; AI-2.2 | **Importance:** Core

#### AI-2.3 Zero-shot, one-shot and few-shot prompting

- **Objective:** Can choose between zero-, one- and few-shot prompting from task ambiguity, output needs and evaluation evidence, and pick examples that do not encode accidental patterns.
- **The concept (Explain):** Examples help only if they improve results on cases the examples did not come from.
- **Target skills:** BU-2 to Apply; VE-3 to Apply; DE-1 to Apply; DE-6 to Apply
- **Methods:** Explain → Modify → Debug & Validate → Evaluate
- **Outcome (measured at unit end):** BU-2: refines the examples. VE-3: tests whether examples help on a held-out set. DE-1: checks the examples for an accidental pattern. DE-6: keeps or drops them with the measured result.
- **Topics:** zero-, one- and few-shot; choosing examples; accidental patterns; measuring the benefit
- **Prerequisites:** AI-2.2; AI-5.1; AI-5.5 | **Importance:** Core

#### AI-2.5 Diagnose prompt and context failures with smallest-change experiments

- **Objective:** Can find whether poor behaviour comes from the task, instructions, context, examples, model, retrieval or output constraints, changing one variable at a time.
- **The concept (Explain):** Change one thing, run the same cases, and write down what happened.
- **Target skills:** SP-4 to Adapt; VE-3 to Adapt; VE-5 to Adapt; BU-5 to Adapt
- **Methods:** Explain → Specify → Debug & Validate → Modify
- **Outcome (measured at unit end):** SP-4: names the missing detail behind a failure. VE-3: states one hypothesis. VE-5: reruns and records whether it held. BU-5: keeps each change as a separate reversible version.
- **Topics:** hypothesis per change; one variable at a time; reruns; recording results; reversible changes
- **Prerequisites:** AI-2.1; AI-2.4; AI-5.5 | **Importance:** Core

#### AI-2.7 Conversation history and memory (new unit)

- **Objective:** Can manage multi-turn state: what history to resend, summarise or drop, and what to store between sessions.
- **The concept (Explain):** The model does not keep a conversation; your code rebuilds it each turn.
- **Target skills:** CO-2 to Adapt; BU-1 to Adapt; DE-6 to Adapt; CO-5 to Adapt
- **Methods:** Explain → Trace → Modify → Evaluate
- **Outcome (measured at unit end):** CO-2: traces what the model actually saw on turn five. BU-1: adapts a single-turn app to keep history. DE-6: compares resending, summarising and storing memory by cost and quality. CO-5: maps how history and memory flow into each request.
- **Topics:** message history; rebuilding context each turn; summarising and trimming; session versus long-term memory; privacy of stored memory
- **Prerequisites:** AI-2.4 | **Importance:** Core

#### AI-2.8 Prompts as versioned, reviewed artifacts (new unit)

- **Objective:** Can store, version, review and roll back prompts and settings like other code.
- **The concept (Explain):** A prompt change is a code change; keep a version and a way back.
- **Target skills:** BU-5 to Adapt; VE-5 to Adapt; DE-1 to Adapt; BU-4 to Adapt
- **Methods:** Explain → Modify → Debug & Validate → Evaluate
- **Outcome (measured at unit end):** BU-5: makes one prompt change per version. VE-5: proves each version with the eval set. DE-1: accepts or rejects a tool-suggested prompt rewrite with the results. BU-4: keeps prompts readable and separate from code.
- **Topics:** prompts in files; versions and diffs; a prompt change reviewed in a pull request; rolling back; linking a version to its eval results
- **Prerequisites:** AI-2.5 | **Importance:** Core | **Integration link:** Git / Version Control

#### AI-2.6 Prompting and reasoning patterns

- **Objective:** Can recognise and choose prompting and reasoning patterns (iterative prompting, chaining, critique-and-revise, self-consistency, chain-of-thought, tree-of-thought) from the task and evaluation evidence.
- **The concept (Explain):** A named technique is only worth using if the eval shows it helps.
- **Target skills:** CO-4 to Apply; SP-3 to Apply; VE-3 to Apply; DE-6 to Apply
- **Methods:** Explain → Decompose → Debug & Validate → Evaluate
- **Outcome (measured at unit end):** CO-4: explains what each pattern is for. SP-3: splits a hard task into a checked two-step chain. VE-3: tests a pattern against a single prompt. DE-6: picks one with accuracy and cost as the reason.
- **Topics:** iterative prompting; chaining; critique-and-revise; self-consistency; chain-of-thought as a pattern; tree-of-thought awareness; evidence over technique names
- **Prerequisites:** AI-2.1; AI-2.2; AI-2.5 | **Importance:** Supporting | **Integration link:** AI-4.x; AI-5.x; AI-10.x; AI-11.x


### Stage 3: Structured outputs and deterministic boundaries

#### AI-3.1 Schema-constrained outputs

- **Objective:** Can define a schema, request schema-conformant output, and tell structural validity from semantic correctness.
- **The concept (Explain):** Valid structure does not mean correct content.
- **Target skills:** BU-3 to Adapt; VE-1 to Adapt; DE-1 to Adapt; CO-1 to Adapt
- **Methods:** Explain → Build → Debug & Validate → Evaluate → Predict
- **Outcome (measured at unit end):** BU-3: uses the provider's structured-output feature from its docs. VE-1: writes checks showing schema-valid output can carry wrong values. DE-1: accepts or rejects a generated schema with a reason. CO-1: predicts which output will be schema-valid before running.
- **Topics:** schemas; structured output features; structural versus semantic validity; schema design
- **Prerequisites:** AI-1.1; AI-2.1 | **Importance:** Core

#### AI-3.2 Validate model output beyond schema shape

- **Objective:** Can validate business and domain rules after structured generation instead of assuming a valid schema means correct values.
- **The concept (Explain):** Treat model output like user input: check the rules, not only the shape.
- **Target skills:** BU-1 to Adapt; VE-1 to Adapt; VE-6 to Adapt; BU-2 to Adapt
- **Methods:** Explain → Modify → Debug & Validate
- **Outcome (measured at unit end):** BU-1: adds business-rule validation to an AI-written extractor. VE-1: writes schema-valid but wrong cases. VE-6: confirms they are rejected. BU-2: refines the validation to the stated business rules.
- **Topics:** range, total and existence checks; business rules; rejecting plausible wrong values
- **Prerequisites:** AI-3.1 | **Importance:** Core

#### AI-3.3 Failure handling for refusal, truncation, invalid or incomplete output

- **Objective:** Can detect and handle refusal, incomplete and invalid output explicitly.
- **The concept (Explain):** Not every response is usable data.
- **Target skills:** VE-2 to Adapt; VE-4 to Adapt; DE-1 to Adapt; CO-2 to Adapt
- **Methods:** Explain → Debug & Validate → Evaluate → Trace
- **Outcome (measured at unit end):** VE-2: finds where AI-written code treats a refusal as valid data. VE-4: reads the stop reason and error fields. DE-1: judges a proposed retry-on-everything fix. CO-2: traces the states a response can be in (complete, truncated, refused, invalid).
- **Topics:** refusals; truncation and stop reasons; invalid output; retry versus fail; explicit states
- **Prerequisites:** AI-3.1; AI-3.2 | **Importance:** Core


### Stage 4: Tool and function calling

#### AI-4.1 Tool contracts

- **Objective:** Can design a tool or function contract whose name, description, parameters and result give the model enough to choose and call it correctly.
- **The concept (Explain):** A tool description is the interface the model reads; unclear descriptions cause wrong calls.
- **Target skills:** SP-2 to Adapt; SP-4 to Adapt; BU-4 to Adapt; DE-1 to Adapt
- **Methods:** Explain → Specify → Modify → Evaluate
- **Outcome (measured at unit end):** SP-2: writes the contract. SP-4: names the detail that made the model pick the wrong tool. BU-4: keeps tools small and non-overlapping. DE-1: accepts or rewrites an AI-drafted set of tools.
- **Topics:** tool name, description, parameters and results; overlapping tools; typed arguments; result meaning
- **Prerequisites:** AI-3.1 | **Importance:** Core | **Integration link:** Software Design / OOD / LLD (interfaces)

#### AI-4.2 The model, tool, result, model loop

- **Objective:** Can detect a requested tool call, validate arguments, run trusted code, return the result and continue generation.
- **The concept (Explain):** The model asks; your code decides whether and how to run the tool.
- **Target skills:** BU-1 to Apply; BU-3 to Apply; VE-4 to Apply; VE-6 to Apply
- **Methods:** Explain → Modify → Build → Debug & Validate
- **Outcome (measured at unit end):** BU-3: implements the loop from the provider docs. BU-1: adds argument validation. VE-4: reads the error from a bad call. VE-6: tests missing and wrongly typed arguments.
- **Topics:** tool-call detection; argument validation; executing trusted code; returning results; loop termination
- **Prerequisites:** AI-4.1; soft: BE-5.1, BE-5.4 (distrust third-party responses) | **Importance:** Core | **Integration link:** Backend Engineering

#### AI-4.3 Tool execution under application authority

- **Objective:** Can separate model intent from authorised action and enforce permissions, validation, side-effect limits and confirmations outside the model.
- **The concept (Explain):** The model may ask for anything; only the application decides what is allowed.
- **Target skills:** SP-1 to Adapt; VE-6 to Adapt; DE-5 to Adapt
- **Methods:** Explain → Specify → Debug & Validate → Direct
- **Outcome (measured at unit end):** SP-1: asks what each tool may change. DE-5: moves permission checks, an allowlist and a confirmation out of the prompt into code. VE-6: tests that a request outside the model's authority is refused.
- **Topics:** permissions; allowlists; side-effect limits; confirmation steps; enforcing outside the model
- **Prerequisites:** AI-4.2 | **Importance:** Core

#### AI-4.4 Evaluate tool selection and argument quality

- **Objective:** Can build cases with expected tool or no-tool behaviour and diagnose failures from tool descriptions, overlapping tools, ambiguous intent or model behaviour.
- **The concept (Explain):** Test which tool the model picks, not only whether the final answer reads well.
- **Target skills:** VE-1 to Adapt; VE-3 to Adapt; DE-1 to Adapt; CO-1 to Adapt
- **Methods:** Explain → Debug & Validate → Evaluate → Predict
- **Outcome (measured at unit end):** VE-1: writes cases with expected tool or no-tool behaviour. VE-3: traces each failure to a cause, one fix at a time. DE-1: accepts or rejects a fix. CO-1: predicts which tool the model will pick for each case before running.
- **Topics:** expected tool choices; ambiguous requests; argument checks; overlap; failure causes
- **Prerequisites:** AI-4.2; AI-5.2 | **Importance:** Core


### Stage 6: Embeddings and semantic retrieval

#### AI-6.1 Embeddings at application-engineering depth

- **Objective:** Can explain that an embedding maps input to a vector useful for similarity and tell it from generative output.
- **The concept (Explain):** An embedding is a list of numbers where nearby items mean similar things.
- **Target skills:** CO-1 to Apply; CO-4 to Apply; CO-6 to Apply; DE-2 to Apply
- **Methods:** Explain → Predict → Direct
- **Outcome (measured at unit end):** CO-1: predicts which sentence pairs score most similar. CO-4: explains each surprise in one sentence. DE-2: asks a tool to explain a similarity result instead of giving it the answer.
- **Topics:** vectors; similarity; embedding versus generation; what embeddings do and do not capture
- **Prerequisites:** AI-0.3 | **Importance:** Core

#### AI-6.2 Semantic similarity and retrieval

- **Objective:** Can embed documents and queries, search by similarity through a store or index, and inspect the candidates.
- **The concept (Explain):** Retrieval returns the nearest items, which may not be the right ones.
- **Target skills:** BU-3 to Apply; VE-6 to Apply; DE-4 to Apply; CO-5 to Apply
- **Methods:** Explain → Build → Debug & Validate → Direct
- **Outcome (measured at unit end):** BU-3: embeds a document set and queries a vector store from its docs. DE-4: reads the store's docs for index and distance choices. VE-6: tries empty, long and off-topic queries. CO-5: sketches how documents, queries and results flow through the store.
- **Topics:** embedding documents and queries; vector stores; similarity search; inspecting results
- **Prerequisites:** AI-6.1 | **Importance:** Core | **Integration link:** Database / SQL (vector-capable stores)

#### AI-6.3 Similarity, top-k, thresholds and metadata filters

- **Objective:** Can tune candidate count, threshold and filters from retrieval evidence and explain precision and recall trade-offs.
- **The concept (Explain):** Nearest is not always relevant; measure what you retrieve.
- **Target skills:** VE-3 to Adapt; DE-6 to Adapt
- **Methods:** Explain → Debug & Validate → Evaluate
- **Outcome (measured at unit end):** VE-3: tests settings against labelled queries. DE-6: picks one with the trade-off stated.
- **Topics:** top-k; thresholds; filters; precision and recall; labelled queries
- **Prerequisites:** AI-6.2 | **Importance:** Core | **Integration link:** Practical DSA


### Stage 7: RAG data and ingestion

#### AI-7.1 Ingestion with source traceability

- **Objective:** Can ingest documents while keeping stable source identity, metadata and provenance.
- **The concept (Explain):** Every chunk must be traceable back to the page it came from.
- **Target skills:** SP-3 to Adapt; BU-1 to Adapt; BU-3 to Adapt; DE-1 to Adapt
- **Methods:** Explain → Decompose → Modify → Build → Evaluate
- **Outcome (measured at unit end):** SP-3: splits an ingestion script into stages. BU-1: adapts it to keep stable document IDs. BU-3: uses a loader library. DE-1: accepts or rejects a library's defaults.
- **Topics:** stable source IDs; metadata; provenance; pipeline stages; loader libraries
- **Prerequisites:** AI-6.1 | **Importance:** Core

#### AI-7.5 Parse documents before chunking (new unit)

- **Objective:** Can turn PDFs, tables and scans into usable text and check the result before it is indexed.
- **The concept (Explain):** Bad parsing becomes bad retrieval; check the text before you chunk it.
- **Target skills:** BU-3 to Adapt; VE-1 to Adapt; VE-6 to Adapt
- **Methods:** Explain → Build → Debug & Validate
- **Outcome (measured at unit end):** BU-3: parses a PDF with a library from its docs. VE-1: writes checks for lost tables, headers and order. VE-6: tries a scan, a two-column page and an empty page.
- **Topics:** text extraction; layout, tables and columns; OCR awareness; cleaning; checking parsed text
- **Prerequisites:** AI-7.1 | **Importance:** Core

#### AI-7.2 Chunking strategy

- **Objective:** Can compare fixed-size, structural, semantic and content-aware chunking and validate the choice against retrieval tasks.
- **The concept (Explain):** Chunk size should come from the content and the questions, not convention.
- **Target skills:** SP-1 to Adapt; VE-3 to Adapt; DE-6 to Adapt
- **Methods:** Explain → Specify → Debug & Validate → Evaluate
- **Outcome (measured at unit end):** SP-1: asks what questions the chunks must answer. VE-3: tests chunking against the retrieval eval set. DE-6: keeps the option the evidence supports.
- **Topics:** fixed, heading-based, semantic chunking; size and overlap; testing against queries
- **Prerequisites:** AI-7.1; AI-5.2 | **Importance:** Core

#### AI-7.3 Metadata and enrichment

- **Objective:** Can add titles, sections, entities, timestamps or permissions when they enable filtering, ranking, traceability or access control.
- **The concept (Explain):** Add metadata only when it enables something.
- **Target skills:** BU-4 to Apply; DE-1 to Apply; DE-5 to Apply; BU-2 to Apply
- **Methods:** Explain → Modify → Evaluate → Direct
- **Outcome (measured at unit end):** BU-4: keeps metadata small and consistent. DE-1: rejects a suggestion to attach a summary to every chunk. DE-5: adds permission metadata for access control. BU-2: refines the metadata scheme to what the filters need.
- **Topics:** metadata for filters, ranking, traceability and access control; avoiding bloat
- **Prerequisites:** AI-7.1 | **Importance:** Core

#### AI-7.4 Re-ingestion, updates and deletion

- **Objective:** Can keep indexes in step with changing sources and avoid duplicate or stale chunks.
- **The concept (Explain):** An index that is not updated returns old answers with confidence.
- **Target skills:** BU-1 to Adapt; VE-1 to Adapt; VE-2 to Adapt; VE-5 to Adapt
- **Methods:** Explain → Modify → Debug & Validate
- **Outcome (measured at unit end):** VE-2: finds why a re-ingestion job leaves stale and duplicate chunks. BU-1: fixes it. VE-1 and VE-5: prove the fix with update and delete checks that failed before.
- **Topics:** updates; deletions; duplicates; stale chunks; idempotent ingestion
- **Prerequisites:** AI-7.1; soft: BE-6.3 (transaction boundaries) | **Importance:** Core | **Integration link:** Backend / Database data lifecycle


### Stage 8: Retrieval and grounded generation

#### AI-8.1 Query, retrieve, context, generate pipeline

- **Objective:** Can build a standard RAG flow with retrieval, context assembly, prompt and generation as separately inspectable stages.
- **The concept (Explain):** RAG is four stages; keep each one visible so you can see which one failed.
- **Target skills:** SP-3 to Adapt; BU-1 to Adapt; BU-3 to Adapt; CO-5 to Adapt
- **Methods:** Explain → Decompose → Modify → Build
- **Outcome (measured at unit end):** CO-5: sketches the data flow between the stages. SP-3: splits an AI-generated single function into stages. BU-1: keeps its answers. BU-3: uses the retrieval store and model client.
- **Topics:** retrieve, assemble, prompt, generate; inspectable stages; data flow
- **Prerequisites:** AI-6.2; AI-7.2; AI-2.2 | **Importance:** Core

#### AI-8.2 Semantic, keyword, hybrid and multi-query retrieval

- **Objective:** Can tell when vector-only retrieval fails and test alternative strategies from observed query and source behaviour.
- **The concept (Explain):** Vector search misses exact terms; test what your queries really need.
- **Target skills:** VE-3 to Adapt; DE-4 to Adapt; DE-6 to Adapt; DE-2 to Adapt
- **Methods:** Explain → Debug & Validate → Direct → Evaluate
- **Outcome (measured at unit end):** VE-3: finds queries where vector-only retrieval misses exact terms. DE-4: reads the store's docs for hybrid options. DE-6: chooses with the measured result. DE-2: asks a tool to explain how hybrid scoring works before using it.
- **Topics:** semantic and keyword search; hybrid retrieval; multi-query; measuring by query type
- **Prerequisites:** AI-8.1; AI-5.2 | **Importance:** Core

#### AI-8.3 Reranking

- **Objective:** Can recognise when candidates are found but poorly ordered and add a reranking stage only when evaluation shows value.
- **The concept (Explain):** Add a reranker only when the right chunk is found but ranked too low.
- **Target skills:** BU-3 to Apply; DE-1 to Apply; DE-6 to Apply
- **Methods:** Explain → Build → Evaluate
- **Outcome (measured at unit end):** BU-3: adds a reranker from its docs. DE-1: keeps it only if the eval gain is real. DE-6: weighs it against added latency.
- **Topics:** candidate retrieval versus ranking; rerankers; cost and latency
- **Prerequisites:** AI-8.1; AI-6.3 | **Importance:** Supporting

#### AI-8.4 Context that keeps source boundaries

- **Objective:** Can assemble retrieved evidence with source identity and delimiters that reduce instruction and data confusion and support attribution.
- **The concept (Explain):** Retrieved text is data, not instructions; label and fence it.
- **Target skills:** SP-2 to Adapt; BU-2 to Adapt; DE-5 to Adapt; CO-6 to Adapt
- **Methods:** Explain → Specify → Modify → Direct
- **Outcome (measured at unit end):** SP-2: specifies the context format. BU-2: refines a context builder so each chunk carries its source ID inside delimiters. DE-5: ensures retrieved text cannot read as instructions. CO-6: explains why retrieved text is data and not instructions, with an example and a non-example.
- **Topics:** source IDs; delimiters; instruction versus data; attribution support
- **Prerequisites:** AI-8.1; AI-2.4 | **Importance:** Core

#### AI-8.5 Missing, conflicting or insufficient evidence

- **Objective:** Can instruct and check a grounded system to abstain, qualify or surface conflicts instead of inventing answers.
- **The concept (Explain):** Saying 'not found' is a correct answer.
- **Target skills:** SP-1 to Adapt; VE-1 to Adapt; VE-6 to Adapt; DE-1 to Adapt
- **Methods:** Explain → Specify → Debug & Validate → Evaluate
- **Outcome (measured at unit end):** SP-1: states what the system must do in each evidence case. VE-1: writes cases where the answer is absent or sources conflict. VE-6: tries near-miss questions. DE-1: judges answers that sound confident.
- **Topics:** abstaining; conflicting sources; qualified answers; no-evidence cases
- **Prerequisites:** AI-8.4; AI-2.2 | **Importance:** Core

#### AI-8.6 Verifiable source attribution

- **Objective:** Can connect generated claims to retrieved source metadata without inventing references.
- **The concept (Explain):** A citation counts only if it points at something that was retrieved.
- **Target skills:** BU-1 to Apply; VE-1 to Apply; VE-2 to Apply
- **Methods:** Explain → Modify → Debug & Validate
- **Outcome (measured at unit end):** BU-1: adapts a generator to cite chunk IDs. VE-1: writes a check that fails when a cited source is not in the retrieval trace. VE-2: finds an invented citation in someone else's output.
- **Topics:** citing chunk IDs; checking citations against the trace; fabricated references
- **Prerequisites:** AI-7.1; AI-8.4 | **Importance:** Core


### Stage 9: RAG evaluation and diagnosis

#### AI-9.1 Evaluate retrieval separately from generation

- **Objective:** Can find whether a failure came from ingestion, chunking, indexing, query, ranking, context assembly or generation.
- **The concept (Explain):** Check each stage in order before you blame the prompt.
- **Target skills:** SP-3 to Adapt; VE-2 to Adapt; VE-3 to Adapt; DE-2 to Adapt
- **Methods:** Explain → Decompose → Debug & Validate → Direct
- **Outcome (measured at unit end):** VE-2: finds the failing stage in an unfamiliar RAG system. VE-3: tests one hypothesis. SP-3: splits the pipeline into checkable stages. DE-2: asks a tool to explain the pipeline's code rather than to fix it.
- **Topics:** stage-by-stage diagnosis; retrieval metrics; generation checks
- **Prerequisites:** AI-8.1; AI-5.2 | **Importance:** Core

#### AI-9.2 Groundedness, relevance and completeness

- **Objective:** Can define and apply RAG quality criteria and check whether claims are supported by the retrieved context.
- **The concept (Explain):** A claim is grounded only if the retrieved text supports it.
- **Target skills:** VE-1 to Adapt; DE-1 to Adapt; DE-4 to Adapt
- **Methods:** Explain → Debug & Validate → Evaluate → Direct
- **Outcome (measured at unit end):** VE-1: marks unsupported claims in 20 answers. DE-1: accepts or rejects an AI judge's verdict. DE-4: checks the evaluation guidance in current docs.
- **Topics:** groundedness; relevance; completeness; judge use and limits
- **Prerequisites:** AI-9.1; AI-5.3 | **Importance:** Core

#### AI-9.3 Improve RAG with evidence-driven experiments

- **Objective:** Can change one retrieval, chunking, ranking or context variable, rerun the eval set and keep the change only if the evidence improves.
- **The concept (Explain):** Keep a change only when the metric rises and no case gets worse.
- **Target skills:** BU-5 to Adapt; VE-3 to Adapt; VE-5 to Adapt; DE-1 to Adapt
- **Methods:** Explain → Modify → Debug & Validate → Evaluate
- **Outcome (measured at unit end):** BU-5: makes one small reversible change. VE-3: states what it should fix. VE-5: reruns the eval set. DE-1: keeps or drops it with per-case evidence.
- **Topics:** single-variable experiments; per-case regression; keeping or dropping changes
- **Prerequisites:** AI-9.1; AI-9.2; AI-5.5 | **Importance:** Core


### Stage 10: Agents and AI workflows

#### AI-10.1 Workflow, orchestration or agent loop

- **Objective:** Can decide whether a task needs a fixed pipeline, conditional orchestration or a model-directed agent.
- **The concept (Explain):** Use an agent only when the next step cannot be known ahead of time.
- **Target skills:** SP-1 to Adapt; SP-3 to Adapt; DE-3 to Adapt; DE-6 to Adapt
- **Methods:** Explain → Specify → Decompose → Direct → Evaluate
- **Outcome (measured at unit end):** SP-1: asks how predictable the task is. SP-3: splits it into steps. DE-3: decides which choices the model may make. DE-6: compares three designs by control and cost.
- **Topics:** fixed pipeline; orchestration; agent loop; predictability; control; cost
- **Prerequisites:** AI-0.4; AI-4.2 | **Importance:** Core

#### AI-10.2 Agent instructions, tools and stop conditions

- **Objective:** Can define an agent's task, tools, constraints, state, iteration limits and stop conditions.
- **The concept (Explain):** An agent needs a task, a tool list and a way to stop.
- **Target skills:** SP-2 to Adapt; BU-2 to Adapt; DE-3 to Adapt; DE-5 to Adapt
- **Methods:** Explain → Specify → Modify → Direct
- **Outcome (measured at unit end):** SP-2: writes the agent's spec. BU-2: refines an AI-drafted agent into one with limits. DE-3: says which decisions stay with the application. DE-5: restricts tools and authority.
- **Topics:** agent task and tools; state; iteration caps; stop conditions; ReAct pattern; keeping authority in the application
- **Prerequisites:** AI-4.1; AI-10.1 | **Importance:** Core | **Integration link:** AI-2.6; AI-4.x; AI-11.x

#### AI-10.3 Single-agent tool-use loop

- **Objective:** Can implement an agent that selects tools, receives results, updates state and stops on explicit conditions.
- **The concept (Explain):** An agent loop is a model, tools, state and a stop rule.
- **Target skills:** BU-1 to Apply; BU-3 to Apply; VE-1 to Apply; VE-6 to Apply
- **Methods:** Explain → Modify → Build → Debug & Validate
- **Outcome (measured at unit end):** BU-3: implements a ReAct-style loop. BU-1: adds a step limit. VE-1: writes a check for stopping. VE-6: tests a task that would loop forever without the limit.
- **Topics:** tool selection; state updates; termination; step limits
- **Prerequisites:** AI-10.2; AI-4.2 | **Importance:** Core

#### AI-10.4 Prefer the simpler workflow

- **Objective:** Can remove agentic complexity when a fixed workflow is more reliable, cheaper, faster or easier to validate.
- **The concept (Explain):** If a fixed workflow does as well, use it.
- **Target skills:** VE-3 to Adapt; DE-1 to Adapt; DE-6 to Adapt; CO-4 to Adapt
- **Methods:** Explain → Debug & Validate → Evaluate
- **Outcome (measured at unit end):** VE-3: runs both on the same eval set. DE-1: replaces the agent if the workflow is as good. DE-6: compares cost and speed. CO-4: explains what the agent was meant to do that the workflow also does.
- **Topics:** agent versus workflow on the same cases; cost; speed; validation
- **Prerequisites:** AI-10.1; AI-5.5 | **Importance:** Core

#### AI-10.5 Choose and read an AI framework (new unit)

- **Objective:** Can decide whether to use an AI framework for RAG or agents, read its code, and keep the application's own boundaries.
- **The concept (Explain):** A framework is a set of decisions made for you; read them before you depend on them.
- **Target skills:** CO-3 to Adapt; DE-2 to Adapt; DE-4 to Adapt; DE-6 to Adapt
- **Methods:** Explain → Direct → Evaluate
- **Outcome (measured at unit end):** CO-3: reads framework code and finds where the prompt and model call happen. DE-2: asks a tool to explain the framework's flow. DE-4: checks its docs and version. DE-6: compares using it with plain code.
- **Topics:** frameworks for RAG and agents; reading their code; hidden prompts and defaults; lock-in; when plain code is simpler
- **Prerequisites:** AI-8.1; AI-10.3 | **Importance:** Supporting


### Stage 11: Agent evaluation and control

#### AI-11.1 Evaluate tool-use quality

- **Objective:** Can measure whether an agent chose the right tools, valid arguments, avoided unnecessary calls and used results correctly.
- **The concept (Explain):** Check each tool call, not only the final answer.
- **Target skills:** VE-1 to Adapt; VE-2 to Adapt; DE-1 to Adapt
- **Methods:** Explain → Debug & Validate → Evaluate
- **Outcome (measured at unit end):** VE-1: scores runs for right tool, valid arguments and unnecessary calls. VE-2: finds the run where a tool result was misused. DE-1: accepts or rejects the agent's choices.
- **Topics:** tool-choice scoring; argument validity; unnecessary calls; use of results
- **Prerequisites:** AI-10.3; AI-5.2 | **Importance:** Core

#### AI-11.2 Evaluate end-to-end task completion

- **Objective:** Can define success for multi-step tasks and judge the outcome, not only the reasoning.
- **The concept (Explain):** Judge the final state, not how reasonable the steps sounded.
- **Target skills:** SP-2 to Adapt; VE-1 to Adapt; VE-6 to Adapt; CO-6 to Adapt
- **Methods:** Explain → Specify → Debug & Validate
- **Outcome (measured at unit end):** SP-2: defines success by final state. VE-1: writes cases for it. VE-6: finds a case where the reasoning sounds right but the result is wrong. CO-6: explains what end-to-end success means, with an example and a non-example.
- **Topics:** task success criteria; final-state checks; multi-step evaluation
- **Prerequisites:** AI-11.1; AI-5.3 | **Importance:** Core

#### AI-11.3 Inspect agent traces

- **Objective:** Can read traces of tool calls, state, retrieval and output to find where an agent went wrong.
- **The concept (Explain):** A trace shows what happened; read it before trusting the model's explanation.
- **Target skills:** CO-2 to Adapt; SP-3 to Adapt; VE-2 to Adapt; VE-3 to Adapt
- **Methods:** Explain → Trace → Decompose → Debug & Validate
- **Outcome (measured at unit end):** CO-2: writes the state after each step before reading the model's account. SP-3: splits the run into steps. VE-2: finds where it diverged. VE-3: tests one hypothesis about why.
- **Topics:** trace reading; state per step; divergence points; hypotheses
- **Prerequisites:** AI-10.3; AI-11.1 | **Importance:** Core


### Stage 12: AI safety, security and data boundaries

#### AI-12.1 Direct and indirect prompt injection

- **Objective:** Can explain how untrusted user or retrieved content may override instructions and design boundaries that do not depend on the model resisting.
- **The concept (Explain):** Any text the model reads can try to give it orders.
- **Target skills:** CO-3 to Adapt; CO-6 to Adapt; VE-6 to Adapt; DE-5 to Adapt
- **Methods:** Explain → Debug & Validate → Direct
- **Outcome (measured at unit end):** CO-6: explains injection in own words with an example and a non-example. CO-3: reads an AI-built assistant and finds where untrusted text reaches the instructions. VE-6: plants a direct and an indirect injection. DE-5: proposes a boundary that does not rely on the model.
- **Topics:** direct injection; indirect injection through retrieved documents; boundaries; defence in depth
- **Prerequisites:** AI-2.2; AI-8.4 | **Importance:** Core

#### AI-12.2 Validate and constrain output before side effects

- **Objective:** Can treat model output as untrusted input and apply validation, permissions, allowlists or checks before consequential actions.
- **The concept (Explain):** Check model output the way you check user input.
- **Target skills:** VE-1 to Adapt; VE-6 to Adapt; DE-5 to Adapt; CO-1 to Adapt
- **Methods:** Explain → Debug & Validate → Direct → Predict
- **Outcome (measured at unit end):** VE-1: writes hostile outputs that must be blocked. DE-5: puts an allowlist and deterministic checks between model output and a SQL tool. VE-6: tries outputs that look valid. CO-1: predicts which hostile outputs get through the check before running.
- **Topics:** output as untrusted input; allowlists; schema and rule checks; side effects
- **Prerequisites:** AI-3.2; AI-4.3 | **Importance:** Core

#### AI-12.3 Minimise agent functionality, permissions and autonomy

- **Objective:** Can restrict tools, scopes, credentials and iteration to what the task needs.
- **The concept (Explain):** Give the agent the least it needs.
- **Target skills:** SP-1 to Adapt; DE-3 to Adapt; DE-5 to Adapt
- **Methods:** Explain → Specify → Direct
- **Outcome (measured at unit end):** SP-1: asks what the task really needs. DE-3: decides what to take away. DE-5: cuts a broad config down with a reason for each cut.
- **Topics:** least privilege; scopes; credentials; autonomy limits; excessive agency
- **Prerequisites:** AI-10.2; AI-4.3 | **Importance:** Core

#### AI-12.6 Moderation and unsafe content (new unit)

- **Objective:** Can decide where input and output moderation belongs and handle flagged content.
- **The concept (Explain):** Unsafe content needs a decision point you control.
- **Target skills:** VE-1 to Adapt; DE-5 to Adapt; DE-6 to Adapt
- **Methods:** Explain → Debug & Validate → Direct → Evaluate
- **Outcome (measured at unit end):** VE-1: writes cases of unsafe and borderline input and output. DE-5: places a moderation check in the flow. DE-6: compares a provider moderation service with your own rules.
- **Topics:** input and output moderation; provider moderation tools; false positives and negatives; handling flagged content
- **Prerequisites:** AI-12.2 | **Importance:** Core

#### AI-12.7 Abuse and unbounded consumption (new unit)

- **Objective:** Can limit how much one user, request or agent loop can spend or consume.
- **The concept (Explain):** Without limits, one request can cost as much as a thousand.
- **Target skills:** SP-4 to Adapt; VE-6 to Adapt; DE-5 to Adapt
- **Methods:** Explain → Specify → Debug & Validate → Direct
- **Outcome (measured at unit end):** SP-4: finds the missing limit in an AI-built feature. VE-6: tests huge input, repeated calls and long loops. DE-5: adds proportionate limits.
- **Topics:** rate limits; token and cost caps; input size limits; loop limits; abuse patterns
- **Prerequisites:** AI-12.2; AI-0.3; soft: BE-12.3 (resource consumption at API boundaries) | **Importance:** Core

#### AI-12.5 Prevent leakage through prompts, logs, traces and outputs

- **Objective:** Can find AI-specific leakage paths and design redaction, access, storage and logging boundaries.
- **The concept (Explain):** Anything you log can leak; log what you need, not what you have.
- **Target skills:** VE-2 to Adapt; VE-6 to Adapt; DE-5 to Adapt; CO-5 to Adapt
- **Methods:** Explain → Debug & Validate → Direct
- **Outcome (measured at unit end):** VE-2: finds where AI-written tracing logs full prompts with personal data. DE-5: adds redaction and access limits. VE-6: checks the sensitive field no longer appears. CO-5: maps where prompts, outputs and traces flow into logs and storage.
- **Topics:** leakage paths; redaction; logging boundaries; access to traces
- **Prerequisites:** AI-12.4; AI-11.3; soft: BE-12.2 (excessive data exposure), BE-13.1 (structured logs) | **Importance:** Core | **Integration link:** AI Governance (bridge); Backend Security


### Stage 13: Reliability, observability and failure diagnosis

#### AI-13.1 Failure taxonomy

- **Objective:** Can classify a bad outcome to model, prompt, retrieval, tool, provider or application before changing anything.
- **The concept (Explain):** Name the failing part before you change anything.
- **Target skills:** SP-3 to Adapt; VE-3 to Adapt; VE-4 to Adapt; CO-2 to Adapt
- **Methods:** Explain → Decompose → Debug & Validate → Trace
- **Outcome (measured at unit end):** SP-3: splits a request into its parts. VE-3: classifies ten bad outcomes with evidence. VE-4: reads the provider errors involved. CO-2: traces the request state through each stage to find where it changed.
- **Topics:** model, prompt, retrieval, tool, provider and application failures; evidence for each
- **Prerequisites:** AI-8.1; AI-4.2; AI-1.1 | **Importance:** Core

#### AI-13.2 Provider failures and incomplete responses

- **Objective:** Can tell rate limits, transport errors, context limits, refusals, incomplete output and tool failures apart and handle each.
- **The concept (Explain):** Each failure needs its own handling.
- **Target skills:** VE-4 to Adapt; VE-6 to Adapt; DE-1 to Adapt
- **Methods:** Explain → Debug & Validate → Evaluate
- **Outcome (measured at unit end):** VE-4: reads the errors. VE-6: tries over-length input and rate limits. DE-1: rejects a blanket retry that would resend over-length requests.
- **Topics:** rate limits; transport errors; context limits; incomplete output; handling per failure
- **Prerequisites:** AI-1.1; AI-3.3; soft: BE-14.1 (timeout, retry and backoff policy) | **Importance:** Core | **Integration link:** Backend resilience

#### AI-13.3 Trace one AI request

- **Objective:** Can keep enough trace data to rebuild a request across model, retrieval and tools without exposing sensitive content.
- **The concept (Explain):** A trace is a map of one request.
- **Target skills:** BU-1 to Adapt; BU-3 to Adapt; VE-4 to Adapt; CO-2 to Adapt
- **Methods:** Explain → Modify → Build → Debug & Validate → Trace
- **Outcome (measured at unit end):** BU-3: adds spans for retrieval, model and tool calls. BU-1: fits them into an existing pipeline. VE-4: rebuilds a failed request from the trace without raw prompts. CO-2: follows one request's state through the spans.
- **Topics:** spans; trace metadata; latency and usage; avoiding sensitive content
- **Prerequisites:** AI-13.1; soft: BE-13.1, BE-13.2 (structured logs, request correlation) | **Importance:** Core | **Integration link:** Backend observability

#### AI-13.4 Connect production traces back to evaluation

- **Objective:** Can turn real failures into regression cases.
- **The concept (Explain):** Every real failure should become a test.
- **Target skills:** VE-1 to Adapt; VE-5 to Adapt; DE-1 to Adapt
- **Methods:** Explain → Debug & Validate → Evaluate
- **Outcome (measured at unit end):** VE-1: writes three regression cases from production failures. VE-5: shows each fails on the current version. DE-1: decides which belong in the suite.
- **Topics:** failures to cases; regression suites; choosing representative cases
- **Prerequisites:** AI-13.3; AI-5.2; AI-5.5 | **Importance:** Core


### Stage 14: Latency, cost and resource efficiency

#### AI-14.1 Latency by component

- **Objective:** Can separate model, retrieval, tool, network and application time to see where latency is spent.
- **The concept (Explain):** Measure before you optimise.
- **Target skills:** VE-3 to Adapt; DE-1 to Adapt; CO-2 to Adapt
- **Methods:** Explain → Debug & Validate → Evaluate → Trace
- **Outcome (measured at unit end):** VE-3: measures time per stage. DE-1: rejects a model switch when the time is spent in retrieval. CO-2: traces one request's time through each stage.
- **Topics:** per-stage timing; where time goes; measurement before change
- **Prerequisites:** AI-13.3 | **Importance:** Core

#### AI-14.2 Token and context cost

- **Objective:** Can estimate and compare token use and find prompt bloat, excessive retrieval or extra agent steps.
- **The concept (Explain):** Cost follows tokens.
- **Target skills:** CO-1 to Apply; DE-6 to Apply
- **Methods:** Explain → Predict → Evaluate
- **Outcome (measured at unit end):** CO-1: predicts a request's token cost. DE-6: names the largest cost driver and compares fixes.
- **Topics:** input and output tokens; context size; retrieval depth; agent steps
- **Prerequisites:** AI-0.3; AI-2.4 | **Importance:** Supporting

#### AI-14.3 Optimise from measured requirements

- **Objective:** Can compare smaller models, caching, batching, retrieval depth and workflow shape using evaluation plus latency and cost evidence.
- **The concept (Explain):** Optimise against numbers you measured.
- **Target skills:** VE-3 to Adapt; DE-6 to Adapt; BU-5 to Adapt
- **Methods:** Explain → Debug & Validate → Evaluate → Modify
- **Outcome (measured at unit end):** VE-3: tests each option. BU-5: makes each change separately. DE-6: chooses with the trade-off stated.
- **Topics:** model size; caching; batching; retrieval depth; workflow shape
- **Prerequisites:** AI-1.3; AI-5.5; AI-14.1; AI-14.2 | **Importance:** Core


### Stage 15: Model and provider lifecycle and customization

#### AI-15.1 Model upgrades as behaviour changes

- **Objective:** Can evaluate a candidate model version before migrating and find regressions.
- **The concept (Explain):** A new model version is a behaviour change.
- **Target skills:** VE-2 to Adapt; VE-3 to Adapt; DE-1 to Adapt; DE-2 to Adapt
- **Methods:** Explain → Debug & Validate → Evaluate → Direct
- **Outcome (measured at unit end):** VE-2: finds per-case format and tool-use regressions. VE-3: tests why. DE-1: decides whether to migrate. DE-2: asks a tool to explain a model changelog rather than to decide the migration.
- **Topics:** regression evaluation on a candidate model; format, tool, latency and cost changes
- **Prerequisites:** AI-1.4; AI-5.5 | **Importance:** Core

#### AI-15.2 Provider substitution

- **Objective:** Can isolate provider integration while keeping real differences between providers.
- **The concept (Explain):** Do not pretend providers are identical.
- **Target skills:** SP-3 to Adapt; BU-1 to Adapt; BU-4 to Adapt; DE-6 to Adapt
- **Methods:** Explain → Decompose → Modify → Evaluate
- **Outcome (measured at unit end):** SP-3: splits shared and provider-specific parts. BU-1: adapts the AI-1.2 boundary to a second provider. BU-4: keeps a feature only one supports. DE-6: compares with a lowest-common-denominator wrapper.
- **Topics:** provider boundary; capability differences; wrapper trade-offs
- **Prerequisites:** AI-1.2; AI-15.1 | **Importance:** Core

#### AI-15.3 Prompting, retrieval, tools or fine-tuning

- **Objective:** Can find the source of a capability gap and avoid fine-tuning when context, retrieval, instructions or tools are the real issue.
- **The concept (Explain):** Find the cause before you pick the cure.
- **Target skills:** SP-1 to Adapt; SP-4 to Adapt; DE-6 to Adapt; CO-4 to Adapt
- **Methods:** Explain → Specify → Evaluate
- **Outcome (measured at unit end):** SP-1: asks why answers miss company policy. SP-4: finds the policy is missing from context. DE-6: chooses among prompting, retrieval, tools and fine-tuning with a reason. CO-4: explains what a fine-tuning request is meant to fix and whether it fits.
- **Topics:** diagnosing capability gaps; fine-tuning as a last step
- **Prerequisites:** AI-2.5; AI-8.1; AI-4.2; AI-5.1 | **Importance:** Core

#### AI-15.4 Fine-tuning at decision depth

- **Objective:** Can explain what supervised tuning can and cannot solve and what data and evaluation it needs. (Goal level: Understand; Apply evidence is recorded if it appears.)
- **The concept (Explain):** Fine-tuning changes behaviour, not what the model knows about your documents.
- **Target skills:** CO-4 to Understand; CO-6 to Understand; DE-1 to Understand
- **Methods:** Explain → Evaluate
- **Outcome (measured at unit end):** CO-6: explains it in own words with an example and a non-example. CO-4: explains what a tuning proposal would fix. DE-1: gives a verdict on it.
- **Topics:** supervised tuning; dataset and evaluation needs; when it does not help
- **Prerequisites:** AI-15.3 | **Importance:** Supporting


### Stage 16: Multimodal and emerging capability awareness

#### AI-16.1 Modalities as different contracts

- **Objective:** Can name validation, size, evaluation, privacy and interface differences between text, image, audio and other modalities. (Goal level: Understand; Apply evidence is recorded if it appears.)
- **The concept (Explain):** Each modality has its own input rules, limits and risks.
- **Target skills:** CO-3 to Understand; DE-1 to Understand; DE-5 to Understand
- **Methods:** Explain → Evaluate → Direct
- **Outcome (measured at unit end):** CO-3: reads a plan to reuse the text pipeline for images. DE-1: judges it. DE-5: lists what it misses (validation, size, privacy, injected text in images).
- **Topics:** image, audio and other inputs; file size and format; privacy; evaluation; injected text
- **Prerequisites:** AI-0.1; AI-5.1 | **Importance:** Supporting

#### AI-16.2 Validate emerging capabilities

- **Objective:** Can tell preview features from stable ones and check current official docs before depending on them.
- **The concept (Explain):** A preview feature can change or disappear.
- **Target skills:** DE-1 to Apply; DE-4 to Apply; DE-6 to Apply
- **Methods:** Explain → Evaluate → Direct
- **Outcome (measured at unit end):** DE-4: checks a recommended feature in current official docs. DE-1: accepts or rejects it. DE-6: compares depending on it with a fallback.
- **Topics:** preview versus stable; official docs; fallbacks
- **Prerequisites:** AI-1.4 | **Importance:** Core


### Stage 17: Integrated AI engineering

#### AI-17.1 Design from a measurable requirement

- **Objective:** Can turn a bounded requirement into model and deterministic responsibilities, context, retrieval and tool needs, quality criteria, safety limits and operational targets.
- **The concept (Explain):** A design starts from what must be measurable.
- **Target skills:** SP-1 to Adapt; SP-2 to Adapt; SP-3 to Adapt; DE-6 to Adapt
- **Methods:** Explain → Specify → Decompose → Evaluate
- **Outcome (measured at unit end):** SP-1: resolves or states open questions. SP-2: writes the design. SP-3: splits it into parts. DE-6: compares two designs.
- **Topics:** responsibilities; retrieval and tools; quality criteria; safety limits; operating targets
- **Prerequisites:** AI-0.4; AI-5.1; selected units | **Importance:** Core

#### AI-17.2 Implement with explicit boundaries

- **Objective:** Can build a multi-part AI feature whose provider calls, prompts, retrieval, tools and validation stay inspectable and replaceable.
- **The concept (Explain):** Each part has one job and one place.
- **Target skills:** BU-2 to Adapt; BU-3 to Own; BU-5 to Adapt; DE-3 to Adapt
- **Methods:** Explain → Modify → Build → Direct
- **Outcome (measured at unit end):** DE-3: has an AI build the pipeline piece by piece. BU-2: refines each piece to spec. BU-5: delivers each piece as a small pull request. BU-3: integrates the parts and rejects any that hides a provider call or prompt in unrelated code.
- **Topics:** multi-component AI feature; boundaries; replaceable parts; small pull requests
- **Prerequisites:** AI-17.1; Backend integration; selected Stage 2-10 units; soft: BE-15.1 (multi-file backend by responsibility), BE-17.2 | **Importance:** Core | **Integration link:** Backend Engineering; Database / SQL

#### AI-17.3 Build and run a regression suite

- **Objective:** Can evaluate the feature on representative cases and keep failures as regression tests.
- **The concept (Explain):** Run the suite before you claim an improvement.
- **Target skills:** BU-1 to Adapt; VE-1 to Adapt; VE-5 to Adapt; BU-4 to Adapt
- **Methods:** Explain → Modify → Debug & Validate
- **Outcome (measured at unit end):** VE-1: builds the suite. BU-1: adapts it to new cases. VE-5: shows it catches a planted prompt regression. BU-4: keeps the suite easy to extend.
- **Topics:** representative cases; past failures; regression runs
- **Prerequisites:** AI-5.5; AI-17.2 | **Importance:** Core

#### AI-17.4 Security review of inputs, outputs, retrieval and tools

- **Objective:** Can find injection, leakage, tool-permission, unsafe-output, excessive-agency and resource risks and add proportionate controls.
- **The concept (Explain):** Review each way untrusted text or data can get in or out.
- **Target skills:** VE-2 to Adapt; VE-6 to Adapt; DE-5 to Adapt; CO-5 to Adapt
- **Methods:** Explain → Debug & Validate → Direct
- **Outcome (measured at unit end):** VE-2: finds risks in the integrated feature. VE-6: tests each risk. DE-5: adds a control with a test. CO-5: maps how untrusted data flows into and out of the feature.
- **Topics:** injection; leakage; permissions; unsafe output; excessive agency; resource limits
- **Prerequisites:** AI-12.1; AI-12.2; AI-12.3; AI-12.4; AI-12.6; AI-12.7 | **Importance:** Core

#### AI-17.5 Diagnose a failure from trace evidence

- **Objective:** Can find the failing boundary in a trace, test a targeted correction and say whether it fixes the cause.
- **The concept (Explain):** Find the boundary that failed, then test a fix for that boundary only.
- **Target skills:** SP-3 to Adapt; VE-3 to Own; VE-4 to Own; DE-1 to Adapt
- **Methods:** Explain → Decompose → Debug & Validate → Evaluate
- **Outcome (measured at unit end):** SP-3: splits the request path. VE-4: reads the errors and traces. VE-3: tests one targeted correction. DE-1: decides whether it fixes the cause or only the symptom.
- **Topics:** trace reading; failing boundary; targeted correction; cause versus symptom
- **Prerequisites:** AI-13.3; AI-13.4 | **Importance:** Core

#### AI-17.6 Improve without hidden regression

- **Objective:** Can change model, prompt, context, retrieval, tools or pipeline and show the target improved with no unacceptable regression.
- **The concept (Explain):** Prove the gain and prove nothing else got worse.
- **Target skills:** BU-5 to Adapt; VE-3 to Adapt; VE-5 to Adapt; DE-6 to Adapt
- **Methods:** Explain → Modify → Debug & Validate → Evaluate
- **Outcome (measured at unit end):** BU-5: moves one step at a time. VE-3: states the target. VE-5: shows the gain with eval and latency or cost evidence. DE-6: weighs the trade-off.
- **Topics:** one change at a time; evaluation plus operating evidence; no hidden regression
- **Prerequisites:** AI-14.3; AI-17.3 | **Importance:** Core

#### AI-17.7 Evidence without claim leakage

- **Objective:** Can tell what an integrated artifact shows for AI Engineering as opposed to Backend, Database, Software Design, System Architecture or Projects.
- **The concept (Explain):** Claim only what the artifact shows.
- **Target skills:** CO-4 to Apply; DE-1 to Apply
- **Methods:** Explain → Evaluate
- **Outcome (measured at unit end):** CO-4: explains what the artifact demonstrates. DE-1: rejects a claim the artifact does not support.
- **Topics:** evidence ownership; claim limits; separating roadmaps
- **Prerequisites:** AI-17.2 | **Importance:** Core | **Integration link:** Backend Engineering; Database / SQL; System Architecture; Projects / Capstones; AI Governance (bridge)

## Skill coverage (target skills, whole roadmap)

Rule used: a skill gets sufficient practice when it is a target in at least 6 units, in at least three of the four bands (Stages 0-4, 5-9, 10-13, 14-17, by the old Stage label), and reaches Adapt or higher.

| Skill | Units | Stages 0-4 | Stages 5-9 | Stages 10-13 | Stages 14-17 | Highest level |
| --- | --- | --- | --- | --- | --- | --- |
| CO-1 | 7 | 4 | 1 | 1 | 1 | Adapt |
| CO-2 | 6 | 2 | 0 | 3 | 1 | Adapt |
| CO-3 | 6 | 3 | 0 | 2 | 1 | Adapt |
| CO-4 | 8 | 3 | 1 | 1 | 3 | Adapt |
| CO-5 | 6 | 2 | 2 | 1 | 1 | Adapt |
| CO-6 | 8 | 2 | 3 | 2 | 1 | Adapt |
| SP-1 | 12 | 4 | 3 | 3 | 2 | Adapt |
| SP-2 | 7 | 2 | 2 | 2 | 1 | Adapt |
| SP-3 | 14 | 4 | 4 | 3 | 3 | Adapt |
| SP-4 | 6 | 4 | 0 | 1 | 1 | Adapt |
| BU-1 | 14 | 6 | 4 | 2 | 2 | Adapt |
| BU-2 | 7 | 3 | 2 | 1 | 1 | Adapt |
| BU-3 | 12 | 4 | 5 | 2 | 1 | Own |
| BU-4 | 7 | 4 | 1 | 0 | 2 | Adapt |
| BU-5 | 6 | 2 | 1 | 0 | 3 | Adapt |
| VE-1 | 20 | 5 | 8 | 6 | 1 | Adapt |
| VE-2 | 10 | 1 | 4 | 3 | 2 | Adapt |
| VE-3 | 18 | 4 | 6 | 3 | 5 | Own |
| VE-4 | 6 | 2 | 0 | 3 | 1 | Own |
| VE-5 | 8 | 2 | 3 | 1 | 2 | Adapt |
| VE-6 | 17 | 5 | 4 | 7 | 1 | Adapt |
| DE-1 | 28 | 9 | 8 | 4 | 7 | Adapt |
| DE-2 | 7 | 2 | 3 | 1 | 1 | Adapt |
| DE-3 | 7 | 1 | 1 | 4 | 1 | Adapt |
| DE-4 | 9 | 3 | 4 | 1 | 1 | Adapt |
| DE-5 | 14 | 2 | 2 | 8 | 2 | Adapt |
| DE-6 | 23 | 7 | 5 | 4 | 7 | Adapt |

All 27 skills meet the rule. 81 units: 3 with two targets, 25 with three, 53 with four. Habits H-1 to H-3 are recorded every session and are not listed.

## Decisions (approved by Asheesh 2026-10-18)

1. **Evaluation foundations (AI-5.1 to AI-5.5) is taught right after AI-2.2**, and **AI-12.4 right after AI-1.1.** IDs are unchanged.
2. **New units:** AI-1.5 streaming, AI-2.7 conversation history and memory, AI-2.8 prompts as versioned artifacts, AI-7.5 document parsing, AI-10.5 choosing and reading an AI framework, AI-12.6 moderation, AI-12.7 abuse and unbounded consumption. MCP and local or open models stay out of scope for now.
3. **Spine rule:** AI Engineering, like Python and Backend, must train all 27 skills enough. Companion roadmaps cover only the skills they naturally train, with an academy-wide check.
4. **Own** only at AI-17.2 (BU-3) and AI-17.5 (VE-3, VE-4); everything else tops out at Adapt.
5. **AI-15.4 and AI-16.1** are tracked at Understand.
6. **Python entry point:** Python through Stage 8 (PY-8.2, PY-8.3, PY-8.4) before AI-1.1.

7. **Four-target units kept as drafted** (53 of 81). Asheesh approved without asking for a trim; the over-covered skills (DE-1, VE-1, VE-3, DE-6) can be trimmed later if learners find the units heavy.
8. **No early prompt-injection unit.** AI-2.2 already keeps untrusted text out of the instruction slot (DE-5); AI-12.1 stays in Stage 12.
9. **Backend is a soft prerequisite only where a unit names a BE unit**; no other roadmap is a named prerequisite yet. Named soft prerequisites to Database, Software Design, DSA and Git are added in a link pass after those roadmaps are upgraded.

## Project links

Projects follow the Projects & Capstones Integration Layer (P0 to P4). A project is not a substitute for the units: it integrates them, and evidence stays with the roadmap that owns it (see AI-17.7). Each unit's Outcome task is the P0 exercise.

**Portfolio and pull requests (Asheesh, 2026-10-18).** Every project below is built to be shown in a portfolio and is delivered through pull requests, not direct commits to the main branch. From P1: small pull requests, each with a description of what changed and why, and the eval or test result that backs it. From P2: at least one review round (the learner reviews another's pull request or answers review on their own) and automatic checks on every pull request. From P3: the pull request history is part of the evidence, and AI-assisted pull requests are marked as such. PR skills are owned by the Git roadmap; see the open item below.

The projects below are suggested starting points, each with a few primary units; a project brief names its own primary and secondary targets before it starts.

| Project | Maturity | Primary units | Secondary units | Other roadmaps |
| --- | --- | --- | --- | --- |
| P1-AI-1 Structured extractor with a first eval set | P1 | AI-2.1, AI-3.1, AI-3.2, AI-5.2 | AI-1.1, AI-5.1, AI-5.5 | Python |
| P1-AI-2 Tool-calling assistant with an authority boundary | P1 | AI-4.1, AI-4.2, AI-4.3 | AI-4.4, AI-12.2 | Backend (soft) |
| P1-AI-3 Embedding search over a small document set | P1 | AI-6.2, AI-6.3, AI-7.1 | AI-7.2, AI-7.5 | Database / SQL |
| P2-AI-1 Grounded document Q&A with an eval suite | P2 | AI-8.1, AI-8.4, AI-8.5, AI-9.1, AI-9.3 | AI-7.2, AI-7.4, AI-8.6, AI-5.5 | Database / SQL, Backend |
| P2-AI-2 Single agent with limits and a trace review | P2 | AI-10.2, AI-10.3, AI-11.2, AI-11.3 | AI-10.4, AI-12.3, AI-13.3 | Software Design |
| P3-AI-1 Portfolio: hardened Q&A service | P3 | AI-17.3, AI-17.4, AI-17.5 | AI-12.6, AI-12.7, AI-13.4, AI-14.3 | Backend |
| P4-AI-1 Capstone: AI product across roadmaps | P4 | AI-17.1, AI-17.2, AI-17.6 | AI-17.7 | Backend (BE-17.6), Database / SQL, System Architecture |

**Open item (PR skills):** the Git roadmap has only one pull-request unit (GIT-3.4, basic workflow), and the sequence puts Git 3 and later after Python 12-13, later than the first P1 projects. Writing a good pull request description, keeping pull requests small, answering review, reviewing someone else's, reading automatic checks and handling AI-written pull requests are not units yet. They are planned as part of the Git upgrade (moved earlier), with this roadmap's projects as the practice.

Not yet done: detailed teaching tasks per unit. The app does not read this roadmap yet; app work is paused for roadmaps beyond Python.
