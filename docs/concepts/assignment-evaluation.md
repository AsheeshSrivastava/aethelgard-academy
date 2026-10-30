---
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