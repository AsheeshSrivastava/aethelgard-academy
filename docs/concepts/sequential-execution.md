---
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