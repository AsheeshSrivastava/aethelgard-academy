---
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