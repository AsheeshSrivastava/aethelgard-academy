---
id: ai-reasoning-boundary
title: Tool help versus your own reasoning
category: AI discipline
summary: AI can write code, but you own whether it is right.
status: approved
units: ["PY-0.3"]
related: []
aliases: ["DE-3", "AI code", "ownership", "verify AI output", "review AI code"]
doc_url: https://docs.python.org/3/tutorial/errors.html
---

An AI tool can give you code that looks right in seconds. It has no accountability for that code. You do.

- The developer owns correctness, the checks at each boundary, and what happens when the code is live.
- Check AI code against the official documentation.
- Test it with real, messy data before you trust it.

## The rule

If you cannot explain a line of AI code, you cannot safely use it. Owning code means you can explain it, check it, and show how it could fail.

## An example from the intake desk

An AI tool wrote a ticket ID that worked on clean names. Real applicants typed spaces around their names, the spaces ended up inside the ticket, and the barcode scanner rejected it. The code had no syntax error. The AI had assumed clean data, and nobody had checked that assumption.
