---
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