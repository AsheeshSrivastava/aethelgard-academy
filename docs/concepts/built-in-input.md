---
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
3. Strips the trailing newline (`\n`) and **always returns a text string (`str`)**.

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