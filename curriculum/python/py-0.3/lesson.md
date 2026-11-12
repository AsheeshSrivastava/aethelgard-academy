# PY-0.3: Tool Help versus Your Own Reasoning

> **The Concept:** A tool can help with code, but the developer still owns the intent, the checking and the decision.

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

Use these three habits every time you work with an AI tool:

1. **Own the intent (before you ask).**
   Write down what goes in, what the program does with it, and what comes out, before you ask a tool anything. Then ask for one specific piece of help, such as: *"Show me the string method that removes spaces at both ends of text."*

   In this course you write your own code. A tool can remind you of syntax, look up a method, draft boilerplate for a function you have already designed, or draft a document such as a README. The logic of your program stays yours. When a tool's code confuses you, ask it to explain, not to rewrite.
2. **Own the checking (after the tool answers).**
   Never keep a tool's code until you have checked what it assumes. Ask:
   - *What happens if the input is empty?*
   - *What happens if the input has spaces?*
   - *What happens if the input has unexpected punctuation?*
3. **Own the decision (before it ships).**
   If a bug stops the intake desk, you cannot tell the pantry coordinator, *"The AI wrote it."* You sign off on the change.

---

## 3. The Ownership Matrix (DE-3)

| Task | Category | Why |
| :--- | :--- | :--- |
| **Looking up syntax or a method name, or drafting boilerplate for a function you designed** | **`DELEGATE_OK`** | Routine help. You still read and check what comes back. |
| **Deciding requirements and privacy rules** | **`MUST_OWN`** | Only you know the policy, legal and people limits. |
| **Deciding what counts as correct, and which cases matter** | **`MUST_OWN`** | A tool can run checks or suggest cases, but you decide what the right answer is. If a tool writes both the code and its checks, the checks can repeat the code's own mistakes. |

---

## 4. The Source of Truth (DE-4)

When an AI chatbot and the official documentation disagree:
- **The chatbot** predicts likely text. It can describe a method that does not exist, and sound sure about it.
- **Running the code and reading the official Python documentation** settle the question.

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
   uv run lms explain PY-0.3 "I can hand a tool lookups, boilerplate and document drafts. I own the intent, I decide what counts as correct and check the tool's assumptions, and I make the final decision."
   ```
