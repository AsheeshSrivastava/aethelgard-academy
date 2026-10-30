"""Seed concept markdown notes into docs/concepts/."""

from pathlib import Path

CONCEPTS = {
    'built-in-input.md': '''---
id: built-in-input
title: input() Built-in Function
category: Core Primitives
doc_url: https://docs.python.org/3/library/functions.html#input
units: ["PY-0.1", "PY-0.4"]
---

# `input()` Built-in Function

> **Operational Role:** Pauses program execution, displays a prompt, and reads raw text across the system boundary via standard input (`stdin`).

---

## 1. Execution Invariants

The `input()` function performs three deterministic steps:
1. Displays the prompt argument to standard output (`stdout`).
2. **Suspends program execution**, waiting for the user to type and press `Enter`.
3. Strips the trailing newline (`\\n`) and **always returns a text string (`str`)**.

> [!WARNING] The Type Guard Invariant
> Python will **never** automatically convert `"100"` into an integer `100`. In public intake desks and data pipelines, automatic guessing causes silent corruption (e.g. dropping leading zeros from identification numbers like `"01234"`). Type conversion must always be explicit.

---

## 2. Right-to-Left Evaluation Order

In assignment statements, Python evaluates the right-hand side first:

```python
# Step A: Right side evaluates (pauses on keyboard, returns 'Sarah')
# Step B: Left side binds variable name 'citizen_name' to that return value
citizen_name = input("Enter citizen name: ")
```

---

## 3. Official Python Documentation Anchor
- [Python Standard Library Built-in Functions: input()](https://docs.python.org/3/library/functions.html#input)
''',
    'built-in-print.md': '''---
id: built-in-print
title: print() Built-in Function
category: Core Primitives
doc_url: https://docs.python.org/3/library/functions.html#print
units: ["PY-0.1", "PY-0.4"]
---

# `print()` Built-in Function

> **Operational Role:** Transmits formatted text and runtime state to the terminal standard output stream (`stdout`).

---

## 1. Execution Invariants

- `print()` evaluates all arguments, converts them to strings, separates them with spaces (by default), and terminates with a newline character.
- **The Blank Line Invariant:** An empty `print()` call emits a newline character to standard output, producing an intentional visual separator line. Empty whitespace lines in code are ignored by Python and do not appear on screen.

> [!NOTE] Whitespace in Code vs Terminal Output
> Leaving 5 blank lines between statements in `solution.py` affects human readability only. It produces zero blank lines on the user terminal. To output a blank line on screen, you must explicitly invoke `print()`.

---

## 2. Syntax Usage Patterns

```python
# 1. Output literal text
print("Intake Desk Active")

# 2. Output an empty blank line
print()

# 3. Modern string interpolation with f-strings
print(f"Citizen: {citizen_name}")
```

---

## 3. Official Python Documentation Anchor
- [Python Standard Library Built-in Functions: print()](https://docs.python.org/3/library/functions.html#print)
''',
    'sequential-execution.md': '''---
id: sequential-execution
title: Sequential Statement Execution (Top-to-Bottom)
category: Execution Model
doc_url: https://docs.python.org/3/reference/executionmodel.html
units: ["PY-0.1", "PY-0.4"]
---

# Sequential Statement Execution (Top-to-Bottom)

> **Operational Role:** Python reads, parses, and executes program statements strictly one by one in sequential line order.

---

## 1. The Line-by-Line Invariant

- Statement on Line 1 executes completely before Statement on Line 2 begins.
- Variables and state created on Line N do not exist in memory prior to Line N. Referencing an identifier before its line executes immediately terminates the program with a `NameError`.

> [!IMPORTANT] Execution Flow vs Mental Jumping
> As an adult learner, your eyes might jump ahead to inspect output statements, but the Python interpreter **never jumps ahead**. It marches top-to-bottom without skipping steps.

---

## 2. Visualizing State Progression

```python
# Time T0: Variable 'station' does not exist yet
station = "Desk A"   # Time T1: 'station' is allocated in memory

# Time T2: Safe to read 'station' because Line 2 already ran
print(f"Location: {station}")
```

---

## 3. Official Python Documentation Anchor
- [Python Language Reference § Execution Model: Structure of a program](https://docs.python.org/3/reference/executionmodel.html)
''',
    'assignment-evaluation.md': '''---
id: assignment-evaluation
title: Right-to-Left Assignment Order
category: Execution Model
doc_url: https://docs.python.org/3/reference/simple_stmts.html#assignment-statements
units: ["PY-0.1"]
---

# Right-to-Left Assignment Order

> **Operational Role:** In any assignment statement (`target = expression`), Python evaluates the entire right-hand expression to a concrete value before binding the name on the left.

---

## 1. The Evaluation Mechanism

In natural languages, we read left to right. But in Python assignment statements, the cognitive flow is **Right-to-Left**:

1. **Phase 1 (Right-Hand Side):** The expression is evaluated. If it contains function calls like `input()`, they run to completion and return a value.
2. **Phase 2 (Left-Hand Side):** The assignment operator `=` takes the returned object and creates an association (a label) pointing to it in memory.

```python
applicant = input("Name: ")
# ^               ^
# |               Step 1: Executes first, captures input, returns string
# Step 2: Binds label 'applicant' to that returned string
```

> [!TIP] Memory Mental Model
> The `=` sign in Python does **not** mean algebraic equality; it means **assignment** (binding a name to an object).

---

## 2. Official Python Documentation Anchor
- [Python Language Reference § Simple Statements: Assignment](https://docs.python.org/3/reference/simple_stmts.html#assignment-statements)
''',
    'variables-memory.md': '''---
id: variables-memory
title: Variables & Identifiers in Memory
category: State & Memory
doc_url: https://docs.python.org/3/reference/executionmodel.html#naming-and-binding
units: ["PY-0.1"]
---

# Variables & Identifiers in Memory

> **Operational Role:** Named references in memory that point to data objects, allowing state to be preserved and passed between system operations.

---

## 1. Key Invariants

- Variables in Python are **names that reference objects** in computer memory.
- Python variables do not require static type declarations; they infer their type dynamically from the object they reference.
- Variable names should be descriptive, lowercase, with words separated by underscores (`snake_case`).

```python
# Clear operational naming
citizen_name = "Marcus Vance"
intake_station_id = "STATION-04"
```

---

## 2. Official Python Documentation Anchor
- [Python Language Reference § Execution Model: Naming and Binding](https://docs.python.org/3/reference/executionmodel.html#naming-and-binding)
''',
    'formatted-strings.md': '''---
id: formatted-strings
title: Formatted String Literals (f-strings)
category: String Formatting
doc_url: https://docs.python.org/3/tutorial/inputoutput.html#formatted-string-literals
units: ["PY-0.1", "PY-0.4"]
---

# Formatted String Literals (f-strings)

> **Operational Role:** Modern, high-performance string interpolation that dynamically evaluates Python expressions inside `{curly_braces}`.

---

## 1. Usage Syntax

Prefix the opening quote with an `f` (or `F`). Any identifier or valid expression inside `{...}` is evaluated at runtime:

```python
name = "Elena Rostova"
desk = 3
print(f"Citizen: {name} assigned to Desk {desk}")
```

> [!NOTE] Evaluation at Runtime
> f-strings are evaluated at the exact instant the line runs, converting variables into their string representations.

---

## 2. Official Python Documentation Anchor
- [Python Tutorial § Input and Output: Formatted String Literals](https://docs.python.org/3/tutorial/inputoutput.html#formatted-string-literals)
''',
    'comments-pseudocode.md': '''---
id: comments-pseudocode
title: Comments as Pseudocode Blueprints
category: Engineering Discipline
doc_url: https://docs.python.org/3/tutorial/introduction.html#first-steps-towards-programming
units: ["PY-0.1", "PY-0.3"]
---

# Comments as Pseudocode Blueprints

> **Operational Role:** Human-readable explanations beginning with `#` that Python ignores completely; used to decompose requirements into operational steps before writing syntax.

---

## 1. The Decomposition Practice

In professional software development, writing code without pseudocode leads to syntax paralysis. Using numbered comments scaffolds the problem:

```python
# Step 1: Ingress - Prompt citizen for their identifier
citizen_id = input("Enter ID: ")

# Step 2: Egress - Format and confirm receipt
print(f"Receipt logged for ID: {citizen_id}")
```

---

## 2. Official Python Documentation Anchor
- [Python Tutorial § First Steps: Comments](https://docs.python.org/3/tutorial/introduction.html#first-steps-towards-programming)
''',
    'standard-streams.md': '''---
id: standard-streams
title: Standard Streams (stdin, stdout, stderr)
category: System Architecture
doc_url: https://docs.python.org/3/library/sys.html#sys.stdin
units: ["PY-0.1", "PY-0.4"]
---

# Standard Streams (stdin, stdout, stderr)

> **Operational Role:** The fundamental input and output communication channels connecting an operating system process to the outside world.

---

## 1. The Three Universal Channels

1. **`stdin` (Standard Input):** Ingress channel. `input()` reads from `stdin`.
2. **`stdout` (Standard Output):** Normal egress channel. `print()` writes to `stdout`.
3. **`stderr` (Standard Error):** Diagnostic channel. Unhandled exceptions and errors are routed here without corrupting data pipelines.

---

## 2. Official Python Documentation Anchor
- [Python Standard Library § sys: Standard Streams](https://docs.python.org/3/library/sys.html#sys.stdin)
''',
    'ai-reasoning-boundary.md': '''---
id: ai-reasoning-boundary
title: Tool Help vs Developer Reasoning (Skill: DE-3)
category: AI Discipline
doc_url: https://docs.python.org/3/tutorial/errors.html
units: ["PY-0.3"]
---

# Tool Help vs Developer Reasoning (DE-3)

> **Operational Role:** Establishing the cognitive ownership boundary between automated AI code generation and human architectural responsibility.

---

## 1. The Developer Ownership Mandate

- AI models produce plausible syntax, but have zero accountability.
- The human developer owns correctness, boundary checks, and production safety.
- Code suggested by AI must be audited against official documentation and tested against deterministic assertions before merging.

> [!IMPORTANT] The Golden Rule of AI Engineering
> If an AI generates a snippet you do not understand line-by-line, you cannot safely deploy it. Ownership requires the ability to explain, verify, and falsify every statement.

---

## 2. Official Python Documentation Anchor
- [Python Tutorial § Errors and Exceptions](https://docs.python.org/3/tutorial/errors.html)
'''
}


def main():
    out_dir = Path("docs/concepts")
    out_dir.mkdir(parents=True, exist_ok=True)
    for fname, content in CONCEPTS.items():
        (out_dir / fname).write_text(content.strip(), encoding="utf-8")
        print(f"Wrote docs/concepts/{fname}")


if __name__ == "__main__":
    main()
