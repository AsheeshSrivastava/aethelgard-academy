---
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