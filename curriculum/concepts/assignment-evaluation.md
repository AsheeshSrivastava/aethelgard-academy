---
id: assignment-evaluation
title: Right-to-left assignment order
category: Execution model
summary: In a line with =, Python works out the right side first, then gives the result the name on the left.
status: draft
units: ["PY-0.1"]
related: ["variables", "expressions", "sequential-execution"]
aliases: ["assignment", "right hand side", "evaluation order", "="]
doc_url: https://docs.python.org/3/reference/simple_stmts.html#assignment-statements
---

We read a line from left to right. Python handles a line with `=` the other way round.

1. **The right side first.** Python works out the [[expressions|expression]]. If it holds a call such as `input()`, that call runs to the end and gives back a value.
2. **The left side second.** Python gives that value the name on the left.

```python
applicant = input("Name: ")
# Step 1: input() runs and gives back the text that was typed.
# Step 2: the name applicant now points to that text.
```

## Why it matters

The `=` sign does not mean "is equal to". It means "give this value this name". That is why a line can use a [[variables|variable]] on both sides:

```python
name = "  Amara  "
name = name.strip()
print(name)
```

```text
Amara
```
