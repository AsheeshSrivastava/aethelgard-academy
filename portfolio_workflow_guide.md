# The Production-Grade AI Engineering Portfolio Playbook
## A Step-by-Step Blueprint for Systems-Minded Builders

---

## 1. Introduction: Your Background is Your Superpower

If you are entering the tech industry from the **social sector** with a **6-year employment gap**, your biggest worry might be: *"Can I compete with 22-year-old computer science grads who type code fast?"*

Here is the truth from someone who reviews portfolios and hires engineers:

1. **AI has commoditized fast typing.** Anyone can prompt an AI to write a Python script or a React component in 10 seconds. Writing raw syntax is no longer a rare skill.
2. **The Social Sector is Pure Systems Thinking.** In the social sector, you worked with complex human problems: limited budgets, unpredictable human behavior, community feedback loops, policy constraints, and high-stakes edge cases. 
3. **AI Engineering is exactly the same.** An AI model is non-deterministic (it acts like an unpredictable person, not a calculator). It needs guardrails, budgets, clear contracts, and monitoring.

When a hiring manager looks at your repository, they are not checking if you memorized algorithms. They are looking for **maturity, structural judgment, and reliability**. This playbook gives you the exact workflow to prove it.

---

## 2. The 30-Day Project Workflow Overview

We divide the creation of your production-grade portfolio project into **7 distinct phases**. Do not skip ahead to writing code before completing the thinking phases.

```
┌────────────────────────────────────────────────────────────────────────┐
│ Phase 1: Problem & Constraints (What & Why) ──► docs/architecture/    │
├────────────────────────────────────────────────────────────────────────┤
│ Phase 2: System Boundaries & ADRs (How it connects) ──► docs/adr/      │
├────────────────────────────────────────────────────────────────────────┤
│ Phase 3: Core Logic & Mock Engine (Runs without API keys) ──► src/core │
├────────────────────────────────────────────────────────────────────────┤
│ Phase 4: AI Gateway & Failure Handling (Resilience) ──► src/ai/        │
├────────────────────────────────────────────────────────────────────────┤
│ Phase 5: The Evaluation Harness (Automated grading) ──► evals/         │
├────────────────────────────────────────────────────────────────────────┤
│ Phase 6: Telemetry & Cost Modeling (FinOps) ──► docs/architecture/    │
├────────────────────────────────────────────────────────────────────────┤
│ Phase 7: Packaging & The 2-Minute README ──► README.md                │
└────────────────────────────────────────────────────────────────────────┘
```

---

## Phase 1: Project Selection & Problem Framing (Days 1–3)

### Goal
Define a real problem with measurable real-world constraints before touching a code editor.

> [!TIP]
> **Project Idea Tip for Social Sector Backgrounds:**
> Leverage your previous domain knowledge! Building a *"Multilingual Intake Triage System for Public Legal Aid"* or a *"Policy Document Question-Answering System with Conflict Detection"* will sound ten times more compelling and authentic in an interview than another generic "Customer Support Chatbot".

### What Document to Write
Create: `docs/architecture/01-problem-statement.md`

### How to Write It (Template in Simple English)
```markdown
# Problem Framing: Public Service Intake Assistant

## 1. The Real-World Problem
Case workers at legal aid clinics spend 35% of their day sorting intake inquiries, 
identifying urgency (e.g., pending eviction in 24 hours vs. general query), 
and routing to specialized attorneys.

## 2. Why Existing Solutions Fail
Standard keyword search misses urgent nuance. Calling a giant AI model (like GPT-4) 
on every intake message is too expensive ($0.04 per inquiry) and risks leaking 
sensitive personal information.

## 3. Measurable Success Targets (Our Constraints)
- Latency: Must return triage results in under 1.5 seconds.
- Accuracy: >95% accuracy in flagging urgent eviction/custody deadlines.
- Cost: Operating budget must stay under $0.005 per intake.
- Privacy: Zero Personally Identifiable Information (PII) stored in external logs.
```

---

## Phase 2: System Architecture & Decision Records (Days 4–7)

### Goal
Decide how the pieces will talk to each other and record *why* you chose specific tools over others.

### Key Concepts in Plain English
* **Separation of Concerns:** Keep business rules (e.g., "is this case urgent?") separate from the AI tool you use. If you switch from OpenAI to an open-source model later, you shouldn't have to rewrite your entire project.
* **Architecture Decision Record (ADR):** A short 1-page note explaining: "We had a choice between X and Y. We chose X because of reasons A and B, even though it has downside C."

### What Documents to Write
1. `docs/architecture/02-system-design.md` (High-level data flow diagram)
2. `docs/adr/0001-record-architecture-decisions.md`
3. `docs/adr/0002-data-storage-and-retrieval.md`

### How to Write an ADR (Template)
```markdown
# ADR 0002: Choosing PostgreSQL with pgvector over a Standalone Vector Database

## Status: Accepted

## Context
Our intake system requires both standard database data (case worker IDs, timestamps, 
urgency flags) and semantic similarity search (matching client descriptions to legal codes).

## Options Considered
1. Dedicated Vector DB (Pinecone / Qdrant)
2. Relational Database with Vector Extension (PostgreSQL + pgvector)

## Decision
We chose PostgreSQL with the pgvector extension.

## Why We Chose It
1. Simplicity: Avoids managing two separate databases and synchronizing state.
2. ACID Guarantees: Case updates and embeddings are stored in a single atomic transaction.
3. Cost: Fits into standard, low-cost existing infrastructure.

## Trade-offs Accepted
- pgvector search speeds can degrade if data grows beyond 5 million vectors without indexing, 
  which is acceptable for our current 100,000 cases/year volume.
```

---

## Phase 3: The "Zero-Key" Mock Engine & Core Logic (Days 8–12)

### Goal
Build the deterministic business logic and a local "Mock Mode" so anyone can test your project immediately without spending money or signing up for API keys.

### Key Concepts in Plain English
* **Mocking:** Creating a fake version of an external service. When you flip `MOCK_AI=true`, instead of calling an expensive cloud API, the system returns an instant pre-written response.
* **Why this wins interviews:** Reviewers have zero friction. They clone your repo, run one command, and it works instantly.

### Implementation Checklist
1. Build your core domain models in `src/core/` (e.g., `CaseReport`, `TriagePriority`, `UserSession`).
2. Build an AI Interface / Protocol:
   ```python
   # src/ai/clients/base.py
   class LLMClientProtocol(Protocol):
       def generate_triage(self, text: str) -> TriageOutput: ...
   ```
3. Create two implementations:
   * `src/ai/clients/real_client.py` (Calls the actual model API)
   * `src/ai/clients/mock_client.py` (Returns instant test fixtures)
4. Add unit tests in `tests/unit/` verifying that your core business logic handles edge cases cleanly.

---

## Phase 4: The AI Gateway & Failure Handling (Days 13–18)

### Goal
Wrap the AI model in safety gear so it never crashes your application.

### Key Concepts in Plain English
* **Non-Determinism:** Computers usually give the exact same answer every time. AI models are probabilistic—they might give a great answer 98 times and output broken nonsense on the 99th.
* **Graceful Degradation:** When something breaks (e.g., the internet drops or the AI fails), the app shouldn't show a generic white screen or crash. It should fall back to a safe backup option.

### What Failures You Must Handle in Code
1. **Bad Formatting:** The AI returns plain text instead of the required JSON $\to$ *Catch the error and run a quick repair or fallback parser.*
2. **Rate Limits / Timeouts (HTTP 429 / 504):** The API is overloaded $\to$ *Automatically wait and retry with exponential backoff, then switch to a secondary backup model.*
3. **Malicious or Garbage Input:** A user pastes prompt injection (e.g., *"Ignore all previous instructions"*) $\to$ *Sanitize input at the gate before passing it to the model.*
4. **Low Confidence:** The model's retrieval score is very low $\to$ *Output "I cannot find a confident answer, escalating to a human staff member" instead of inventing facts.*

### Document to Write
`docs/architecture/03-resilience-and-fallbacks.md`

---

## Phase 5: The Evaluation Harness (The "Automated Exam") (Days 19–23)

### Goal
Prove scientifically that your AI system works accurately, rather than just saying "I tested it and it looks good."

### Key Concepts in Plain English
* **Evaluation Harness:** A test suite specifically for AI. You create a list of 50–100 realistic test questions where you already know the right answer ("Golden Dataset"). Your evaluation script runs all of them and grades the AI.
* **Hallucination Detection:** Checking whether the AI made up facts that weren't in your reference documents.

### What to Put in `evals/`
* `evals/datasets/golden_dataset.json`:
  ```json
  [
    {
      "input": "My landlord changed the locks this morning and threw my clothes out.",
      "expected_urgency": "EMERGENCY_IMMEDIATE",
      "expected_category": "ILLEGAL_LOCKOUT"
    }
  ]
  ```
* `evals/run_evals.py`: A script you can run with `python evals/run_evals.py` that prints a clean scorecard:
  ```
  Evaluations Summary (100 test cases):
  - Urgency Classification Accuracy: 97.0%
  - Hallucination Rate: 1.0%
  - Average Latency: 420ms
  - Average Cost per Query: $0.0028
  ```

---

## Phase 6: Observability & FinOps (Cost Modeling) (Days 24–27)

### Goal
Show that you understand how a production system is monitored and paid for in the real world.

### Key Concepts in Plain English
* **Telemetry / Tracing:** Recording a timeline for every user request (e.g., "Request took 600ms total: 50ms in database, 530ms in AI call, 20ms in response validation").
* **FinOps (Financial Operations):** Calculating exactly what this application will cost the organization as it grows.

### What Document to Write
Create: `docs/architecture/economics.md`

### How to Write the Economics Document (Example)
```markdown
# Financial Operations (FinOps) & Scaling Analysis

## Scenario: 50,000 Inquiries / Month

### Option A: Naive Architecture
- Direct call to Frontier LLM for 100% of queries
- No caching layer
- Monthly Estimated Cost: $1,750 / month

### Option B: Our Architected System
- Semantic Cache: Resolves 28% of repetitive general questions at $0.00
- Fast Tier-1 Model: Handles 60% of simple triage at $0.0008/call
- Frontier Model: Reserved only for top 12% complex cases
- Monthly Estimated Cost: $285 / month

### Conclusion:
Our architecture achieves an 83.7% cost reduction while preserving 99%+ accuracy 
on high-urgency cases.
```

---

## Phase 7: Packaging & The "2-Minute" README (Days 28–30)

### Goal
Present your work so an executive, client, or technical lead can understand its brilliance in under 120 seconds.

### The 2-Minute Hiring Manager Rule
A reviewer spends an average of 90 to 120 seconds on your GitHub repository before deciding to book an interview or move on. 

They will **not** read 3,000 lines of code first. They look for:
1. What does this do? (1-sentence elevator pitch)
2. Can I see it working? (A 10-second GIF or diagram)
3. Can I run it immediately? (A 1-line copy-paste command)
4. Did this person think about edge cases and costs? (Links to ADRs and Eval results)

### Recommended `README.md` Layout
```markdown
# CaseFlow AI: Resilient Legal Aid Intake & Triage Engine

> An open-source, fault-tolerant AI triage system designed to categorize high-urgency 
> legal aid inquiries while protecting client privacy and controlling token spend.

![System Architecture Diagram](docs/assets/architecture-diagram.png)

## Key Highlights
- **Engineered for Reliability:** Built-in circuit breakers, PII scrubbing, and fallback routing.
- **Cost-Optimized:** Tiered routing and semantic caching cut monthly inference costs by 83%.
- **Zero-Key Mock Mode:** Fully testable locally in 10 seconds without cloud API keys.
- **Evaluated on Golden Dataset:** 97% accuracy on emergency classification; <1% hallucination.

## Quickstart (Run in 30 Seconds)
```bash
# Clone and run with zero configuration (uses built-in mock engine)
git clone https://github.com/yourname/caseflow-ai
cd caseflow-ai
MOCK_AI=true docker compose up
```

## System Architecture & Decisions
- [System Architecture & Data Flow](docs/architecture/02-system-design.md)
- [ADR 0002: Why pgvector over standalone vector DB](docs/adr/0002-data-storage-and-retrieval.md)
- [Evaluation Harness & Benchmark Results](evals/README.md)
- [Unit Economics & Scaling Projections](docs/architecture/economics.md)


---

## 3. How to Present Your 6-Year Gap & Career Switch

When interviewing or writing your portfolio introduction, never apologize for your employment gap or your background. Frame it with authority:

| What NOT to Say | How to Say It (Systems Thinking Frame) |
| :--- | :--- |
| *"I have a 6-year gap and I'm just learning to code now with AI tools."* | *"I took time away to focus on personal and community priorities, and I am bringing over a decade of systems-level thinking from the social sector into software engineering."* |
| *"I built this chatbot project following a tutorial."* | *"I designed this intake triage architecture specifically to address the cost, privacy, and reliability bottlenecks that prevent non-profits from adopting AI in production."* |
| *"AI wrote most of my code."* | *"I used modern AI pair-programming to accelerate implementation, allowing me to focus my engineering effort where it matters most: system boundaries, resilience, automated evaluations, and unit economics."* |

---

## 4. Master Checklist

- [ ] **Phase 1:** `docs/architecture/01-problem-statement.md` defines clear numeric constraints.
- [ ] **Phase 2:** Clean folder structure with business logic separate from AI code.
- [ ] **Phase 2:** At least 2 Architecture Decision Records (ADRs) explaining real trade-offs.
- [ ] **Phase 3:** `MOCK_AI=true` allows running the app and tests with zero API keys.
- [ ] **Phase 4:** Handled rate limits, invalid JSON, low-confidence scores, and prompt injection.
- [ ] **Phase 5:** An automated `run_evals.py` script that grades the system against a golden dataset.
- [ ] **Phase 6:** `docs/architecture/economics.md` modeling cost savings at scale.
- [ ] **Phase 7:** A high-impact `README.md` with an architecture diagram and 30-second run command.
