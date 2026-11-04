# PY-0.3: Tool Help versus Your Own Reasoning

> **The Concept:** A tool can write code, but the developer still owns the intent, the checking and the decision.

---

## 1. Operational Context: The Flawed AI Snippet

In the modern AI era, you will write code alongside powerful companions, code generators, and IDE assistants. 

Here is the operational reality of AI tools:
- **What AI is great at:** Emitting syntax boilerplate in seconds, translating common idioms, and looking up standard library patterns.
- **Where AI fails:** AI has no real-world accountability. It doesn't know your users, it doesn't face compliance audits, and it routinely makes invisible, dangerous assumptions about data cleanliness.

At our Intake Desk, an intern asked an AI tool: *"Write code to generate a ticket ID for an applicant."*
The AI emitted:
```python
f"INTAKE-2026-{raw_name.upper()}"
```
The code ran with zero syntax errors. But when real families arrived and entered `"   amara okafor   "`, the output was:
```text
INTAKE-2026-   AMARA OKAFOR   
```
The desk's barcode scanner rejected every ticket because of the embedded spaces! The AI assumed clean data; operational reality gave it messy input.

---

## 2. The Three Always-On Habits

As an aspiring AI Systems Architect, you must adopt three non-negotiable habits whenever working with AI tools:

1. **Own the Intent (Before prompting):**
   Define the exact Ingress $\rightarrow$ Transformation $\rightarrow$ Egress contract *before* asking an AI to generate code. Never ask: *"Write my intake script."* Instead ask: *"Show me the string method that removes leading and trailing whitespace in Python."*
2. **Own the Checking (After generation):**
   Never accept AI-generated code without checking its hidden assumptions. Ask:
   - *What happens if input is empty?*
   - *What happens if input has spaces?*
   - *What happens if input contains unexpected punctuation?*
3. **Own the Decision (At shipment):**
   If a bug crashes the intake desk, you cannot tell the pantry coordinator: *"The AI wrote it."* You are the engineer; you sign off on the commit.

---

## 3. The Ownership Matrix (DE-3)

| Engineering Task | Category | Rationale |
| :--- | :--- | :--- |
| **Looking up syntax or method names** | **`DELEGATE_OK`** | Looking up how `str.strip()` works or boilerplate syntax is routine tool assistance. |
| **Defining system requirements & privacy** | **`MUST_OWN`** | Only the human developer understands the policy, legal, and operational boundaries. |
| **Verifying edge cases against tests** | **`MUST_OWN`** | Tests and assertions prove the code satisfies reality; AI assertions are often circular. |

---

## 4. The Source of Truth (DE-4)

When an AI chatbot and official documentation disagree:
- **The Chatbot** is a statistical language model capable of hallucinating plausible-sounding methods that do not exist.
- **The Official Python Documentation & Test Suite** is the deterministic, authoritative source of truth.

---

## 5. Local Workflow Instructions

1. **Pull the Exercise:**
   ```bash
   uv run lms pull PY-0.3
   ```
2. **Open in Zed or VS Code:**
   Open `workspace/PY-0.3/solution.py`.
3. **Fix the AI Flaw and Fill in the Matrices:**
   - Strip whitespace and uppercase the name in Part 1.
   - Fill in `"DELEGATE_OK"` or `"MUST_OWN"` in Part 2.
   - Identify `"OFFICIAL_DOCS_AND_TESTS"` in Part 3.
4. **Verify Locally:**
   ```bash
   uv run lms verify PY-0.3
   ```
5. **Submit Concept Check (`CO-6`):**
   ```bash
   uv run lms explain PY-0.3 "A tool can generate syntax, but the developer must own the intent, verify edge cases against tests, and make the final decision."
   ```
