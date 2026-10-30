---
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