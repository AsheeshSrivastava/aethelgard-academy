# Architectural Blueprint: The 79-Unit Unforced Operational Narrative Spine

> **Status:** APPROVED & ACTIVE  
> **Governed by:** `reference/Python Subject Roadmap v4.md` (79 Core Python Units + 32 Slotted Units = 111 Total Path Sequence)  
> **Core Domain:** *The Municipal Emergency Voucher & Public Assistance Logistics Network ("MEVAN")*  
> **Target Persona:** Non-traditional career switchers from operations, public policy, and social services transitioning into Python Backend & AI Systems Architecture.

---

## 1. Executive Summary: Why This Narrative Survives All 79 Units

Traditional programming stories (such as the legacy biohack detective mystery) fail before Unit 30 because they use **decorative fiction**: a dramatic backdrop pasted onto abstract exercises. When the fiction meets language abstractions (like `class Pen` or context managers), the story breaks, power-creep exhausts the learner, and adult professionals feel patronized.

The **Operational Narrative Spine** is an **evolutionary systems metaphor**. Instead of an artificial mystery, the learner experiences the authentic lifecycle of a mission-critical public service:
- It begins at a **single physical intake desk** with a paper form and a terminal prompt (`input()`, `print()`).
- As municipal needs grow, manual methods collapse under real-world stress: dirty data, duplicate claims, conflicting statutory policies, corrupted files, and disaster traffic spikes.
- Every Python language feature is introduced as the **exact architectural remedy** to an operational failure.

```
THE EVOLUTIONARY LIFECYCLE (UNITS 1 TO 111)

STAGE 0: THE RECEPTION TERMINAL (Units 1-3)
  │ Primitives: Terminal input, execution sequence, AI assistance boundaries.
  ▼
STAGE 1: THE ELIGIBILITY LEDGER (Units 4-12)
  │ Data Ingress: Types, normalization, string sanitization, asserts, sets, dicts, nested dossiers (PY-1.9).
  ▼
STAGE 2: BATCH QUEUE & LOGIC DISPATCH (Units 13-17)
  │ Control Flow: Statutory decision trees, queue iteration, debugging, comprehensions.
  ▼
STAGE 3: THE POLICY ASSESSMENT PIPELINE (Units 18-23)
  │ Modular Logic: Pure functions, interface boundaries, rule decomposition.
  ▼
[PAUSE 1: Practical DSA Stage 0 — Algorithmic Complexity in Registry Searches (Units 24-27)]
  ▼
STAGE 4: DEFENSIVE SERVICE BOUNDARIES (Units 28-31)
  │ Robustness: Exception hierarchies, boundary validation, failure contracts.
  ▼
[PAUSE 2: Git Stage 0 — Versioning Statutory Policy Code & Branching (Units 32-35)]
  ▼
STAGE 5: MULTI-AGENCY PACKAGE ARCHITECTURE (Units 36-40)
  │ Decoupling: Modules, package namespaces, CLI entry points, reading legacy code.
  ▼
STAGE 6: CITIZEN CASE DOMAIN ENTITIES (Units 41-49)
  │ Domain Modeling: Dataclasses, properties, special methods, polymorphism, composition.
  ▼
[PAUSE 3: Software Design Stage 0 — SOLID Invariants & Liskov Substitutability (Units 50-53)]
  ▼
STAGE 7: HIGH-VOLUME STREAMING & RESOURCE SAFETY (Units 54-59)
  │ Protocols: Generators for 500k-record streaming, decorators, context managers (`with`), typing protocols.
  ▼
STAGE 8: PERSISTENCE, EXTERNAL APIS & DISK I/O (Units 60-66)
  │ Integration: Pathlib, CSV/JSON census ingestion, regex matching, environment config, HTTP services, timezones.
  ▼
[PAUSE 4: Practical DSA Stage 1 — Priority Queues for Emergency Triage & Tree Topologies (Units 67-70)]
  ▼
STAGE 9: REGULATORY AUDIT & AUTOMATED VERIFICATION (Units 71-76)
  │ Quality Assurance: Pytest suites, mocking external government APIs, mutation testing, profiling.
  ▼
STAGE 10: DEPENDENCIES & CONTAINER RELEASE GATES (Units 77-81)
  │ Platform Ops: Virtual environment isolation, lockfiles, distributable wheels, CI quality gates.
  ▼
STAGE 11: EMERGENCY SURGE TRAFFIC & ASYNC CONCURRENCY (Units 82-86)
  │ Concurrency: Thread/process pools, async event loops, concurrent HTTP gathers, resilient task cancellation.
  ▼
[PAUSE 5: Git Stage 1 — Collaborative Remotes, PR Workflows & History Audits (Units 87-90)]
  ▼
STAGE 12: INHERITING & REFACTORING LEGACY SYSTEMS (Units 91-95)
  │ Systems Evolution: Codebase navigation, library evaluation, layered architecture, characterization tests.
  ▼
[PAUSE 6: Software Design Stage 1, Git Stage 2, AI-Assisted Engineering (Units 96-107)]
  ▼
STAGE 13: AUTONOMOUS MUNICIPAL SUBSYSTEM & AI ARCHITECT (Units 108-111)
  │ Synthesis: Interchangeable pluggable ports, integration verification, owning AI-directed architecture.
  ▼
PHASE 2: STATUTORY RAG & AUTONOMOUS POLICY AGENTS (Phase 2 Units)
  │ AI Systems: BM25/Vector retrieval, DSPy optimization, provenance firewalls across 1,000 pages of municipal bylaws.
```

---

## 2. Complete Unit-by-Unit Operational Map (All 79 Core Python Units + 32 Slotted Units)

### Stage 0: Foundations & Mental Models (Units 1–3)

| Path # | Unit ID | Roadmap Unit Title | Operational Domain Scenario | Target Invariant Learned |
| :---: | :---: | :--- | :--- | :--- |
| **1** | **PY-0.4** | Run a first program | **The Intake Desk Terminal:** A citizen arrives at the desk requesting emergency housing relief. The clerk runs `solution.py`, prompts for applicant details via `input()`, prints an egress confirmation receipt with `print()`, and reads a first type error. | *All data arriving across the system boundary enters as untrusted text.* |
| **2** | **PY-0.1** | Python as an executing program | **Tracing the Intake Life-Cycle:** Tracking state transitions step-by-step through an execution table as citizen claims are bound to memory names from top to bottom. | *Python executes statements sequentially; each statement deterministically transforms program state.* |
| **3** | **PY-0.3** | Tool help versus your own reasoning | **The Policy Automation Boundary:** An AI assistant suggests code to automate applicant eligibility scoring. The engineer audits the code against municipal policy invariants, identifying unverified assumptions. | *Tools generate syntax; the human systems architect owns developer intent, validation, and accountability.* |

---

### Stage 1: Data Ingress, Types, Sequences & Mappings (Units 4–12)

| Path # | Unit ID | Roadmap Unit Title | Operational Domain Scenario | Target Invariant Learned |
| :---: | :---: | :--- | :--- | :--- |
| **4** | **PY-1.2** | Numbers, booleans and None | **Financial Eligibility Calculator:** Converting string input into integer dependents and float monthly income; computing poverty threshold ratios, handling missing phone records (`None`), and guarding currency precision with `decimal`. | *Values possess strict types that govern legal operations; never perform raw arithmetic on unparsed boundary text.* |
| **5** | **PY-1.7** | Text | **Voucher Formatting & Identity Sanitization:** Slicing national identity numbers, stripping accidental whitespace, normalizing casing, and building structured voucher issuance keys with f-strings. | *Strings are immutable sequences; text normalization requires purposeful transformation.* |
| **6** | **PY-1.1** | Names, objects and expressions | **Dossier Memory & Aliasing:** Tracking municipal caseworker assignments in memory. Demonstrating that reassigning a variable label does not mutate or overwrite the underlying applicant object. | *Variable names are pointers to objects; binding is not copying.* |
| **7** | **PY-1.8** | Checking code with assert | **Defending Municipal Budget Invariants:** Placing executable `assert` statements throughout the calculation pipeline to prove disbursed relief amounts never drop below zero or exceed allocation caps. | *Assertions are executable contracts that halt execution instantly upon invariant violation.* |
| **8** | **PY-1.3** | Lists and tuples | **Intake Queue & Fixed Station Coordinates:** Managing the ordered daily queue of waiting citizens (`list`) alongside the immutable GPS and license coordinates of the relief station (`tuple`). | *Use lists for ordered, evolving collections; use tuples for fixed, immutable composite records.* |
| **9** | **PY-1.9** | Copies, aliases and nested data | **Multi-Member Household Records:** Managing nested family records with shared residential addresses. Using deep copies to update an individual member's status without accidentally mutating the entire family cluster. | *Mutating a nested mutable structure affects all references unless explicitly deep-copied.* |
| **10** | **PY-1.4** | Mappings | **The Citizen Case Dossier:** Replacing parallel, error-prone lists with structured key-value dictionaries indexed by unique Citizen National ID for $O(1)$ lookups. | *Mappings provide direct semantic association and constant-time key retrieval.* |
| **11** | **PY-1.5** | Choosing data structures | **The Registry Architecture Audit:** Evaluating data structures under operational stress: choosing sets for instant duplicate detection, dicts for fast case lookups, and lists for chronological audit logs. | *System constraints dictate structure: choose data structures based on access patterns and mutation safety.* |
| **12** | **PY-1.6** | Specialised collections & stdlib | **Relief Station Supply Inventory:** Using `collections.Counter` to tally relief food/blanket supplies across depots, `defaultdict` to group claims by municipal district, and `deque` for FIFO lines. | *Standard library data structures solve common operational patterns with battle-tested efficiency.* |

---

### Stage 2: Control Flow, Iteration & Comprehensions (Units 13–17)

| Path # | Unit ID | Roadmap Unit Title | Operational Domain Scenario | Target Invariant Learned |
| :---: | :---: | :--- | :--- | :--- |
| **13** | **PY-2.1** | Conditions | **Statutory Eligibility Decision Trees:** Implementing multi-tier public assistance policy rules (`if`/`elif`/`else`) evaluating household size, emergency severity, and income thresholds. | *Conditionals must exhaustively cover operational boundaries without silent fall-throughs.* |
| **14** | **PY-2.2** | Iteration | **Batch Intake Queue Processing:** Iterating through 1,000 emergency disaster relief submissions, validating eligibility rules, and accumulating total relief funds disbursed. | *Iterate defensively; avoid mutating a collection while iterating over it.* |
| **15** | **PY-2.5** | Debugging basics | **Diagnosing Queue Crashes:** Using print debugging, state tracing, and reading traceback line numbers when a malformed record crashes the batch queue runner. | *Errors are clues: isolate the line, inspect the local state, and verify assumptions before patching.* |
| **16** | **PY-2.3** | Comprehensions | **Batch Normalization & Extraction:** Using list and dictionary comprehensions to extract high-priority claim IDs and normalize incoming phone numbers in a single readable line. | *Comprehensions express clear mapping and filtering transformations without manual loop overhead.* |
| **17** | **PY-2.4** | Choosing control flow | **Streamlined Policy Dispatch:** Refactoring deeply nested `if-else` pyramids into early guard clauses and clean policy lookup tables. | *Flat is better than nested: reduce cyclomatic complexity to make operational rules audit-ready.* |

---

### Stage 3: Functions, Scope, Interfaces & Decomposition (Units 18–23)

| Path # | Unit ID | Roadmap Unit Title | Operational Domain Scenario | Target Invariant Learned |
| :---: | :---: | :--- | :--- | :--- |
| **18** | **PY-3.1** | Function calls and scope | **Isolating Benefit Calculations:** Encapsulating welfare benefit calculation math into pure functions, preventing local temporary calculation state from polluting registry scope. | *Functions create scope boundaries; pure functions produce deterministic output from explicit inputs.* |
| **19** | **PY-3.6** | Recursion | **Navigating Dependent Household Trees:** Writing a recursive traversal function to calculate total relief allowances across complex multi-generational family trees and sub-dependents. | *Recursive solutions require explicit base cases and monotonic progress toward termination.* |
| **20** | **PY-3.2** | Function interfaces | **The Station API Contract:** Designing clear, explicit parameter signatures for `evaluate_citizen_claim(applicant, income, urgent=False)` with keyword arguments and defaults. | *Call interfaces must be obvious, self-documenting, and resistant to argument-ordering errors.* |
| **21** | **PY-3.3** | Functions as values | **Pluggable Disaster Relief Policies:** Passing custom policy calculation functions as first-class arguments into a universal intake pipeline (e.g. Flood Policy vs Winter Relief Policy). | *Higher-order functions allow runtime customization of business logic without code duplication.* |
| **22** | **PY-3.4** | Coherent functions | **Refactoring Monolithic Intake:** Decomposing a 200-line intake script into small, single-responsibility functions (parsing, validating, scoring, printing). | *A function owns exactly one operational job; high coherence reduces cognitive load and testing friction.* |
| **23** | **PY-3.5** | Decomposing a requirement | **From Municipal Ordinance to System:** Translating a 10-page municipal climate assistance decree into an end-to-end decomposed software workflow. | *Break complex institutional requirements into small, independently verifiable functional blocks.* |

---

### Slotted Pause 1: Practical DSA Stage 0 (Units 24–27)

| Path # | Unit ID | Roadmap Unit Title | Operational Domain Scenario | Target Invariant Learned |
| :---: | :---: | :--- | :--- | :--- |
| **24** | **DSA-0.1** | Growth and operation costs | **Registry Scaling Limits:** Measuring the growth in execution time when searching 100 vs 1,000,000 citizen records using linear scan. | *Algorithmic complexity $O(n)$ dictates system survival as population data scales.* |
| **25** | **DSA-0.2** | Finding nested work | **Eliminating Redundant Verification:** Detecting and removing $O(n^2)$ nested loops where every applicant was redundantly compared against all previous claims. | *Nested loops over shared data structures create hidden exponential performance cliffs.* |
| **26** | **DSA-0.3** | Theory versus measured runtime | **Benchmarking Field Hardware:** Profiling theoretical Big-O predictions against actual wall-clock execution on low-spec municipal field terminals. | *Hardware caches and Python interpreter overhead affect real-world runtime alongside Big-O theory.* |
| **27** | **DSA-0.4** | Sorting and binary search | **Fast National Registry Lookups:** Sorting citizen rosters by national identification number and implementing $O(\log n)$ binary search lookups. | *Pre-sorted data enables logarithmic search, reducing lookup latency from seconds to microseconds.* |

---

### Stage 4: Failure Contracts, Exceptions & Defensive Boundaries (Units 28–31)

| Path # | Unit ID | Roadmap Unit Title | Operational Domain Scenario | Target Invariant Learned |
| :---: | :---: | :--- | :--- | :--- |
| **28** | **PY-4.1** | Exception flow | **Handling Downstream System Outages:** Tracing how unhandled network errors and parse failures bubble up the call stack, crashing field desks. | *Exceptions alter normal control flow; unhandled exceptions terminate process state.* |
| **29** | **PY-4.2** | Failure contracts | **Explicit System Boundaries:** Defining explicit contracts for functions when invalid citizen inputs arrive (raising typed exceptions vs returning `Result` objects). | *A function contract must explicitly declare its failure modes alongside its return types.* |
| **30** | **PY-4.3** | Validation | **Hardening the Ingress Barrier:** Validating tax IDs, dates of birth, and residency proofs at the entry perimeter before data enters core calculations. | *Validate at the system boundary; internal business logic should operate only on verified data.* |
| **31** | **PY-4.4** | Making failures explicit | **The Domain Error Hierarchy:** Authoring custom exception classes (`MunicipalRegistryError`, `IncomeVerificationFailedError`, `DuplicateDisbursementError`). | *Typed domain exceptions allow callers to distinguish expected operational anomalies from fatal crashes.* |

---

### Slotted Pause 2: Git Stage 0 (Units 32–35)

| Path # | Unit ID | Roadmap Unit Title | Operational Domain Scenario | Target Invariant Learned |
| :---: | :---: | :--- | :--- | :--- |
| **32** | **GIT-0.1** | Repository state & history | **Auditing Policy Changes:** Initializing Git for the municipal relief system; tracking working tree, staging index, and commit history for regulatory review. | *Git provides an immutable, cryptographically verifiable ledger of software evolution.* |
| **33** | **GIT-0.2** | Diffs, staging & commits | **Documenting Operational Fixes:** Staging atomic policy bug fixes with clear, audit-compliant commit messages explaining operational intent. | *Commits must be atomic units of verified change with descriptive rationale.* |
| **34** | **GIT-0.3** | Branches, HEAD and merging | **Parallel Station Features:** Creating isolated feature branches for winter relief voucher rules and safely merging them into main. | *Branches isolate experimental or concurrent development without destabilizing production trunk.* |
| **35** | **GIT-0.4** | Resolving merge conflicts | **Reconciling Conflicting Regulations:** Resolving git merge conflicts when two engineering teams update household benefit rules simultaneously. | *Conflicts represent genuine domain divergence; resolve them by understanding intent, not guessing.* |

---

### Stage 5: Modules, Packages, Entry Points & Reading Codebases (Units 36–40)

| Path # | Unit ID | Roadmap Unit Title | Operational Domain Scenario | Target Invariant Learned |
| :---: | :---: | :--- | :--- | :--- |
| **36** | **PY-5.1** | Modules and imports | **Separating Registry State from UI:** Splitting the monolithic intake file into `storage.py`, `rules.py`, and `interface.py` using standard `import` syntax. | *Modules decompose complex codebases into separate namespaces and reusable files.* |
| **37** | **PY-5.2** | Splitting code across modules | **Eliminating Circular Coupling:** Restructuring module dependencies so high-level policy rules do not circularly depend on low-level terminal UI scripts. | *Dependencies must point in one direction; circular imports reveal architectural boundary failure.* |
| **38** | **PY-5.3** | Packages | **Multi-Department Namespace:** Organizing modules into formal packages (`mevan.intake`, `mevan.eligibility`, `mevan.disbursement`). | *Packages group related modules under clear domain namespaces with clean public boundaries.* |
| **39** | **PY-5.4** | Entry points | **The Field Terminal CLI (`__main__`):** Implementing standard `if __name__ == "__main__":` entry points and configuring executable package execution (`python -m mevan`). | *Entry points establish clean application startup boundaries distinct from importable library code.* |
| **40** | **PY-0.2** | Reading a small application | **Inheriting a Field Office Repo:** Reading, diagramming, and mentally executing an unfamiliar 500-line emergency shelter program inherited from another district. | *Reading and tracing existing code is a primary engineering skill prerequisite to changing it.* |

---

### Stage 6: Object-Oriented Domain Engineering, Dataclasses & Composition (Units 41–49)

| Path # | Unit ID | Roadmap Unit Title | Operational Domain Scenario | Target Invariant Learned |
| :---: | :---: | :--- | :--- | :--- |
| **41** | **PY-6.1** | Classes, instances and state | **The Citizen Case Entity:** Encapsulating applicant data and state transitions into an active, self-contained `CitizenCase` class. | *Objects bundle state with the operations that read and mutate that state.* |
| **42** | **PY-6.2** | Constructing objects | **Invariant Enforcement in `__init__`:** Guaranteeing that no `CitizenCase` can be created without mandatory validation, timestamps, and legal district codes. | *Constructors must enforce object invariants from the moment of creation.* |
| **43** | **PY-6.3** | Instance, class & static methods | **Factory Methods & Station Counters:** Using `@classmethod` for alternative constructors (`CitizenCase.from_csv_row()`) and static utility calculators. | *Use instance methods for state, class methods for alternate constructors, and static methods for pure helpers.* |
| **44** | **PY-6.4** | Controlled object interfaces | **Property Encapsulation (`@property`):** Protecting citizen voucher balances from direct mutation; providing read-only properties with internal validation. | *Expose controlled attributes via properties to enforce business invariants during mutation.* |
| **45** | **PY-6.8** | Special methods | **Pythonic Case Operations:** Implementing `__str__`, `__repr__`, `__len__`, and `__eq__` so cases can be compared by National ID and cleanly printed in logs. | *Special dunder methods integrate domain objects seamlessly with Python's language protocols.* |
| **46** | **PY-6.9** | Data classes and named values | **Type-Safe Policy Records (`@dataclass`):** Replacing raw dictionaries with type-annotated, frozen dataclasses for immutable audit records. | *Dataclasses provide clean boilerplate-free representations for structured domain records.* |
| **47** | **PY-6.5** | Inheritance and resolution | **Relief Category Hierarchies:** Modeling `HousingVoucher` and `NutritionVoucher` inheriting shared traits from `BenefitVoucher`, understanding MRO. | *Inheritance models 'is-a' relationships; understand method resolution order to prevent hidden overrides.* |
| **48** | **PY-6.6** | Polymorphism & shared contracts | **Uniform Disbursement Processing:** Iterating over a mixed queue of housing, food, and medical vouchers, calling `.disburse()` uniformly on all. | *Polymorphism allows heterogeneous objects satisfying a common contract to be processed identically.* |
| **49** | **PY-6.7** | Composition & responsibility | **Assembling the Field Station Subsystem:** Favoring composition over inheritance: a `ReliefStation` is composed of a `QueueManager`, a `PolicyEngine`, and an `AuditLedger`. | *Favor composition over inheritance to create flexible, loosely coupled systems.* |

---

### Slotted Pause 3: Software Design Stage 0 (Units 50–53)

| Path # | Unit ID | Roadmap Unit Title | Operational Domain Scenario | Target Invariant Learned |
| :---: | :---: | :--- | :--- | :--- |
| **50** | **SD-0.1** | Framing design problems | **Balancing Audit vs Latency Trade-offs:** Framing trade-offs between instant citizen dispatches and exhaustive synchronous database verification. | *Every architectural decision trades one operational quality for another; frame trade-offs explicitly.* |
| **51** | **SD-0.2** | Interfaces & dependency direction | **Inverting Storage Dependencies:** Decoupling business logic from raw disk storage by introducing formal interface boundaries. | *High-level business policies must not depend on low-level storage details; both depend on abstractions.* |
| **52** | **SD-0.3** | SOLID as change reasoning | **Evaluating System Fragility:** Applying SOLID principles to refactor a fragile voucher engine so adding new vouchers requires zero core edits. | *SOLID principles guide system evolution so software grows by extension rather than risky modification.* |
| **53** | **SD-0.4** | Substitutability (Liskov & ISP) | **Proving Voucher Interchangeability:** Ensuring any specialized emergency grant can substitute for a standard voucher without breaking caller contracts. | *Subtypes must satisfy all behavioral expectations and invariant guarantees of their parent contracts.* |

---

### Stage 7: Iterators, Generators, Decorators & Context Managers (Units 54–59)

| Path # | Unit ID | Roadmap Unit Title | Operational Domain Scenario | Target Invariant Learned |
| :---: | :---: | :--- | :--- | :--- |
| **54** | **PY-7.1** | Iterables and iterators | **Custom Station Queue Traversal:** Implementing `__iter__` and `__next__` on custom `CaseQueue` objects to enable natural `for case in queue:` iteration. | *The iterator protocol decouples collection internal storage from external sequential traversal.* |
| **55** | **PY-7.2** | Generators | **Streaming 500,000 Historical Records:** Writing generator functions with `yield` to process massive municipal census logs without exhausting server RAM. | *Generators evaluate lazily on-demand, enabling bounded-memory streaming across massive datasets.* |
| **56** | **PY-7.3** | Decorators | **Audit Interceptors & Telemetry:** Writing `@audit_logged` and `@timing_metric` decorators to monitor caseworker transactions and measure execution times. | *Decorators wrap functions transparently to inject cross-cutting concerns without modifying core logic.* |
| **57** | **PY-7.4** | Context managers | **Safe Registry Transactions (`with`):** Authoring custom context managers (`with atomic_voucher_transaction(db):`) ensuring lock releases on unexpected failures. | *Context managers guarantee resource acquisition and cleanup invariants across normal and exceptional exits.* |
| **58** | **PY-7.5** | Type annotations | **Eliminating Runtime Type Bugs:** Annotating function arguments, return types, and complex generic collections; validating with static type checkers. | *Type annotations make interface contracts explicit and catch structural defects before runtime.* |
| **59** | **PY-7.6** | Interface-style type contracts | **Runtime Protocol Ports (`typing.Protocol`):** Creating structural subtyping protocols for pluggable storage and payment notification adapters. | *Protocols define flexible, structurally verified interface boundaries without requiring rigid inheritance.* |

---

### Stage 8: Files, Structured Data, Patterns, Config, CLI & HTTP (Units 60–66)

| Path # | Unit ID | Roadmap Unit Title | Operational Domain Scenario | Target Invariant Learned |
| :---: | :---: | :--- | :--- | :--- |
| **60** | **PY-8.1** | Files and paths | **Resilient File Storage (`pathlib`):** Safely creating, writing, and atomically replacing regional registry ledger files across different OS environments. | *Use `pathlib.Path` for platform-agnostic, safe, and atomic filesystem operations.* |
| **61** | **PY-8.2** | Structured data | **CSV & JSON Inter-Agency Interchange:** Parsing municipal census CSV files and serializing official relief vouchers to validated JSON schemas. | *Structured serialization must preserve types and handle schema discrepancies defensively.* |
| **62** | **PY-8.6** | Pattern matching in text | **Sanitizing Identification Formats:** Using regular expressions to validate and parse phone numbers, tax IDs, and postal codes across regional offices. | *Regular expressions validate boundary formatting and extract structured tokens from raw text.* |
| **63** | **PY-8.3** | Configuration | **Station Configuration Management:** Loading database URLs, regional poverty lines, and station IDs from external `.env` and JSON configuration files. | *Separate code from configuration: operational parameters must change without modifying source code.* |
| **64** | **PY-8.7** | Command-line programs & subprocess | **The Municipal Administration Tool:** Building a full-featured CLI with `argparse` and managing system sub-processes to execute verification tools. | *Production command-line utilities provide structured arguments, clear help text, and proper exit codes.* |
| **65** | **PY-8.4** | Calling HTTP services | **National Identity Registry Integration:** Querying the upstream national welfare verification API over HTTP, handling headers, timeouts, and errors. | *External networks are unreliable: always configure timeouts, handle status codes, and expect failure.* |
| **66** | **PY-8.5** | Dates, times and timezones | **Timezone-Aware Audit Timestamps:** Parsing timestamps with `zoneinfo` and `datetime`, computing 30-day voucher expiration windows across UTC boundaries. | *Store and calculate all operational timestamps in UTC; localize only for human display at the boundary.* |

---

### Slotted Pause 4: Practical DSA Stage 1 (Units 67–70)

| Path # | Unit ID | Roadmap Unit Title | Operational Domain Scenario | Target Invariant Learned |
| :---: | :---: | :--- | :--- | :--- |
| **67** | **DSA-1.1** | Stacks, queues & priority queues | **Emergency Triage Priority Queuing:** Implementing priority queues (`heapq`) to ensure critical medical claims jump ahead of standard vouchers. | *Priority queues provide $O(\log n)$ triage ordering for time-critical resource allocation.* |
| **68** | **DSA-1.2** | Trees & hierarchical data | **Regional Administration Hierarchies:** Modeling city $\rightarrow$ district $\rightarrow$ field office administrative hierarchies using tree structures. | *Tree structures represent nested ownership, inheritance, and cascading operational authority.* |
| **69** | **DSA-1.3** | Graphs, BFS/DFS & dependencies | **Relief Distribution Topologies:** Modeling road networks and depot delivery routes as graphs, finding shortest delivery paths using BFS/Dijkstra. | *Graphs model arbitrary connectivity and multi-hop dependency networks across operational hubs.* |
| **70** | **DSA-1.4** | Choosing under changing constraints | **Surge Load Architecture Adaptation:** Adapting data structures dynamically when relief station RAM is constrained during severe winter blackouts. | *Engineers re-evaluate and swap data structures when operational constraints shift.* |

---

### Stage 9: Debugging, Logging & Pytest Behavioral Verification (Units 71–76)

| Path # | Unit ID | Roadmap Unit Title | Operational Domain Scenario | Target Invariant Learned |
| :---: | :---: | :--- | :--- | :--- |
| **71** | **PY-9.1** | Debugging | **Live Execution Inspection (`pdb`):** Setting breakpoints and inspecting variable scope in an active registry service to diagnose state race conditions. | *Interactive debuggers let you pause time, inspect live state, and verify code behavior at execution.* |
| **72** | **PY-9.2** | Logging and runtime evidence | **Production Audit Logging:** Replacing raw `print` statements with structured, leveled logs (`INFO`, `WARNING`, `ERROR`) formatting audit-compliant JSON. | *Logs are operational telemetry: output structured, leveled, context-rich evidence for operators and auditors.* |
| **73** | **PY-9.3** | Behavioural tests with pytest | **Automated Statute Verification:** Authoring automated Pytest suites verifying that eligibility calculation functions adhere to legal statutory mandates. | *Automated tests turn regulatory specifications into reproducible, executable proofs.* |
| **74** | **PY-9.4** | Isolating code under test | **Mocking Upstream Government APIs:** Creating mock adapters and test doubles for the national identity HTTP service to keep tests fast and offline. | *Isolate code under test from external side-effects to achieve fast, deterministic verification.* |
| **75** | **PY-9.5** | When passing is not proof | **Mutation Testing & Boundary Falsification:** Intentionally injecting subtle errors into benefit logic to prove that the test suite actually catches edge-case failures. | *A passing test suite proves nothing if tests are not capable of failing when invariants are violated.* |
| **76** | **PY-9.6** | Measuring runtime | **Pipeline Throughput Profiling:** Using `cProfile` and `timeit` to detect execution bottlenecks across the daily 10,000-citizen batch run. | *Profile before optimizing: measure exact bottlenecks rather than optimizing based on intuition.* |

---

### Stage 10: Environments, Dependencies & Quality Gates (Units 77–81)

| Path # | Unit ID | Roadmap Unit Title | Operational Domain Scenario | Target Invariant Learned |
| :---: | :---: | :--- | :--- | :--- |
| **77** | **PY-10.1** | Environments | **Virtual Environment Isolation:** Managing clean project environments with `uv`/`venv`, isolating project dependencies from host OS packages. | *Isolate Python environments to prevent dependency pollution and ensure reproducible execution.* |
| **78** | **PY-10.2** | Dependencies | **Lockfiles & Reproducible Builds:** Pinning exact package versions and hashes in `pyproject.toml` and lockfiles to eliminate supply-chain drift. | *Unpinned dependencies cause silent production failures; lock every deployment deterministically.* |
| **79** | **PY-10.3** | Project metadata & packaging | **Building the Relief Platform Wheel:** Packaging the codebase into a distributable Python wheel with metadata, dependencies, and CLI hooks. | *Standard packaging formats enable reliable distribution, installation, and deployment across platforms.* |
| **80** | **PY-10.4** | Diagnosing install failures | **Resolving Broken Dependencies:** Diagnosing package version conflicts, missing binary dependencies, and path corruptions on field machines. | *Understand package dependency resolution algorithms to diagnose and repair installation failures.* |
| **81** | **PY-10.5** | Quality gates | **Enforcing Code Standards (`ruff`, `pyright`):** Setting up automated linters and type checkers that reject non-compliant code before deployment. | *Automated quality gates maintain code hygiene and enforce architectural constraints before merge.* |

---

### Stage 11: Concurrency, Threads, Processes & Asynchronous I/O (Units 82–86)

| Path # | Unit ID | Roadmap Unit Title | Operational Domain Scenario | Target Invariant Learned |
| :---: | :---: | :--- | :--- | :--- |
| **82** | **PY-11.1** | Concurrency mental model | **The Disaster Surge Traffic Crisis:** Understanding CPU-bound vs I/O-bound bottlenecks when 50,000 citizens submit claims simultaneously after a flood. | *Concurrency is about dealing with lots of things at once; parallelism is about doing lots of things at once.* |
| **83** | **PY-11.5** | Threads and processes | **Parallel Verification Pools:** Using `ThreadPoolExecutor` for concurrent I/O lookups and `ProcessPoolExecutor` for CPU-heavy identity cryptography. | *Use threads for concurrent I/O operations; use separate processes to bypass the GIL for CPU-bound tasks.* |
| **84** | **PY-11.2** | Tracing async code | **The Async Event Loop Mental Model:** Tracing coroutine execution (`async`/`await`), tasks, and event loop scheduling on a single OS thread. | *Async code yields control cooperatively at `await` points, allowing a single thread to service thousands of I/O tasks.* |
| **85** | **PY-11.3** | Concurrent I/O | **High-Throughput Intake Service:** Querying 5 upstream municipal validation APIs concurrently using `asyncio.gather` to return instant citizen answers. | *Concurrent I/O completes in the duration of the slowest request, not the sum of all requests.* |
| **86** | **PY-11.4** | Async failures | **Resilient Async Error Boundaries:** Handling partial timeouts, connection resets, and task cancellations without crashing the background event loop. | *Async exceptions must be handled explicitly within coroutines or gathered defensively with `return_exceptions=True`.* |

---

### Slotted Pause 5: Git Stage 1 (Units 87–90)

| Path # | Unit ID | Roadmap Unit Title | Operational Domain Scenario | Target Invariant Learned |
| :---: | :---: | :--- | :--- | :--- |
| **87** | **GIT-1.1** | Remotes & divergence | **Syncing Municipal Regional Repos:** Fetching, pulling, and pushing changes between central headquarters and field office remote Git repositories. | *Remote tracking branches represent remote state; reconcile divergence through rebase or merge intentionally.* |
| **88** | **GIT-1.2** | The pull-request workflow | **Peer Reviewing Regulatory Changes:** Submitting pull requests with detailed verification evidence for peer review by senior municipal engineers. | *Pull requests provide a structured audit boundary where changes are inspected and verified before integration.* |
| **89** | **GIT-1.3** | Undo and recovery | **Emergency Policy Rollback:** Reverting a faulty deployment in production using `git revert` without altering historical audit trails. | *Use `git revert` for safe, public rollbacks; reserve `git reset` for private, unshared branch cleanup.* |
| **90** | **GIT-1.4** | Reading history for context | **Investigating Policy Provenance:** Using `git log` and `git blame` to determine who altered a voucher threshold, when, and under which regulatory ticket. | *Git history is an operational audit log explaining why the system reached its current state.* |

---

### Stage 12: Navigating Legacy Codebases, Documentation & Refactoring (Units 91–95)

| Path # | Unit ID | Roadmap Unit Title | Operational Domain Scenario | Target Invariant Learned |
| :---: | :---: | :--- | :--- | :--- |
| **91** | **PY-12.1** | Navigating an unfamiliar codebase | **Inheriting a 5,000-Line Legacy System:** Tracing symbol dependencies, call hierarchies, and data paths in an undocumented welfare system. | *Map entry points, core domain entities, and data flows before attempting to modify an unfamiliar codebase.* |
| **92** | **PY-12.2** | Learning a library from docs | **Evaluating an Official PDF Engine:** Reading official documentation to integrate a compliant digital voucher PDF library without unsafe blog snippets. | *Read official source docs and specifications to understand configuration, lifecycle, and security guarantees.* |
| **93** | **PY-12.3** | Organising a Python application | **Layered Architectural Refactor:** Restructuring sprawling legacy code into clean Presentation, Domain, Application, and Persistence layers. | *Clear architectural layering enforces separation of concerns and prevents cross-layer coupling.* |
| **94** | **PY-12.4** | Changing existing systems safely | **The Strangler Fig Migration:** Writing characterization tests around legacy calculation logic before strangling and replacing it with clean code. | *Pin down legacy behavior with characterization tests before refactoring internal implementation.* |
| **95** | **PY-12.5** | Refactoring | **Systemic Debt Elimination:** Extracting classes, reducing parameter lists, removing duplicate code, and proving all unit tests remain green. | *Refactoring alters internal structure without changing external behavior; verified tests are non-negotiable.* |

---

### Slotted Pause 6: Software Design Stage 1, Git Stage 2, AI-Assisted Engineering (Units 96–107)

| Path # | Unit ID | Roadmap Unit Title | Operational Domain Scenario | Target Invariant Learned |
| :---: | :---: | :--- | :--- | :--- |
| **96** | **SD-1.1** | Pattern intent & core set | **Applying GoF Patterns:** Applying Repository and Factory patterns to the voucher system to decouple storage from creation. | *Design patterns are codified solutions to recurring trade-offs; use them when their specific intent matches.* |
| **97** | **SD-1.2** | Pattern overuse & smells | **Pruning Premature Abstraction:** Removing unnecessary abstract factories and over-engineered interfaces that add complexity without benefit. | *Premature abstraction increases cognitive burden; design for current operational reality, not hypothetical futures.* |
| **98** | **SD-1.3** | Modelling state machines | **The Voucher Lifecycle State Machine:** Designing formal state machine transitions (`Submitted` $\rightarrow$ `UnderReview` $\rightarrow$ `Approved` $\rightarrow$ `Disbursed`). | *Explicit state machines prevent illegal state transitions and clarify complex entity lifecycles.* |
| **99** | **SD-1.4** | Producing & defending an LDD | **The Municipal Architecture Review:** Writing and defending a formal Low-Level Design (LLD) document before an executive governance board. | *An architect must clearly communicate design trade-offs, failure modes, and boundaries in written documentation.* |
| **100** | **GIT-2.1** | Git as safety net for agents | **Managing Autonomous AI Code Spikes:** Using Git branches, stashes, and clean diffs as the safety net when delegating coding tasks to AI agents. | *Never let an AI agent touch dirty worktrees; use clean git checkpoints to audit and reject unverified changes.* |
| **101** | **AAE-0.1** | Agent modes & human ownership | **Defining the Human-in-the-Loop Contract:** Distinguishing between copilot assistance, subagent delegation, and human engineering responsibility. | *AI agents are untrusted junior implementers; the human systems architect retains absolute ownership of intent.* |
| **102** | **AAE-0.2** | The task contract | **Authoring Precise Agent Briefs:** Formulating structured task specifications with clear inputs, outputs, invariants, and acceptance criteria. | *Ambiguous instructions produce hallucinated code; formal task contracts produce predictable implementations.* |
| **103** | **AAE-0.3** | Inspect before changing | **Grounding Agents in Codebase Reality:** Enforcing read-before-write workflows so AI inspects existing domain interfaces before generating code. | *Never let an agent write code without first inspecting existing interfaces, contracts, and test conventions.* |
| **104** | **AAE-0.4** | Context and instruction files | **Curating Repo Context:** Creating `AGENTS.md`, ADRs, and spec files that steer agent code generation toward architectural consistency. | *Context files steer agent behavior deterministically by establishing repository constraints and conventions.* |
| **105** | **AAE-0.5** | Permissions & least privilege | **Security Boundaries for Autonomous Code:** Sandboxing AI tools, restricting file write permissions, and preventing unvetted shell execution. | *Apply the principle of least privilege to agent capabilities: never grant autonomous access to sensitive keys or networks.* |
| **106** | **AAE-0.6** | Reviewing & verifying agent work | **No-Blind-Code Audit:** Reviewing agent-generated code with the 4 Plain-English Questions (Single Job, Ingress/Egress, Failure, Traceability). | *Never accept AI code without line-by-line understanding, independent test verification, and invariant audit.* |
| **107** | **AAE-0.7** | Steering & diagnosing failures | **Correcting Agent Deviations:** Diagnosing context drift, hallucinated APIs, and loop regressions; steering agents back to specification. | *When an agent fails, analyze root cause in the prompt or context rather than blindly retrying.* |

---

### Stage 13: Building Subsystems, Interchangeable Contracts & AI Ownership (Units 108–111)

| Path # | Unit ID | Roadmap Unit Title | Operational Domain Scenario | Target Invariant Learned |
| :---: | :---: | :--- | :--- | :--- |
| **108** | **PY-13.1** | Building a Python subsystem | **Synthesizing the Complete Relief Engine:** Assembling an end-to-end, multi-component municipal assistance engine from formal specifications. | *Synthesize cohesive subsystems by connecting verified components through explicit boundary contracts.* |
| **109** | **PY-13.2** | Interchangeable components | **Pluggable Ports & Adapters Architecture:** Swapping out local SQLite storage for PostgreSQL, or console prints for SMS dispatch, with zero core logic edits. | *Hexagonal ports and adapters isolate domain business rules from external technology and infrastructure churn.* |
| **110** | **PY-13.3** | An integrated, reliable workflow | **Production Reliability & Chaos Verification:** Running chaos injection tests (dropped DB connections, corrupted files, malformed JSON) to prove resilience. | *Production systems prove reliability by surviving hostile inputs, partial outages, and unexpected crashes gracefully.* |
| **111** | **PY-13.4** | Owning AI-assisted work | **The Systems Architect Capstone:** Directing AI agents to build a high-performance municipal relief service while independently verifying all invariants and audits. | *The master engineer leverages AI for rapid implementation while exercising rigorous architectural sovereignty.* |

---

## 3. Seamless Continuation into Phase 2: AI Engineering & Statutory RAG

When the learner completes Stage 13 (Unit 111), the exact same operational domain continues directly into **Phase 2 (AI Engineering Roadmap v2)**:
- **The Operational Challenge:** Field workers and citizens struggle to understand 1,500 pages of municipal relief bylaws, legal ordinances, and eligibility statutes.
- **The AI Solution:** Ingesting statutory documents into a **Two-Stage Provenance-Firewalled RAG Platform**:
  - Extracting chunks from official PDFs with metadata anchors.
  - Hybrid retrieval combining **BM25 lexical search** (for exact statute numbers) and **vector embeddings** (for semantic concepts).
  - Prompt optimization with **DSPy** to generate grounded answers with exact statutory citations.
  - Socratic AI companions that help citizens understand requirements without hallucinating legal advice.

---

## 4. Verification Check

- **Total Path Items:** 111
- **Core Python Units (`PY-*`):** Exactly 79
- **Slotted Units (`DSA`, `GIT`, `SD`, `AAE`):** Exactly 32
- **Narrative Breakdowns:** 0 (Every single unit directly advances the *Municipal Emergency Voucher & Public Assistance Logistics Network*).
