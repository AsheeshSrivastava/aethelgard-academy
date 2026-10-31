---
id: formatted-strings
title: f-strings
category: Core tools
summary: An f-string is text with values placed inside it, written in curly braces.
status: draft
units: ["PY-0.1", "PY-0.4"]
related: ["print-function", "expressions", "variables"]
aliases: ["f-string", "fstring", "formatted string", "string formatting", "curly braces", "{}"]
doc_url: https://docs.python.org/3/tutorial/inputoutput.html#formatted-string-literals
---

An f-string lets you build text from values. Put an `f` before the opening quote, then write each value inside `{}`.

```python
name = "Elena Rostova"
desk = 3
print(f"Citizen: {name} assigned to Desk {desk}")
```

```text
Citizen: Elena Rostova assigned to Desk 3
```

Anything inside `{}` is an [[expressions|expression]], so it can be more than a name:

```python
name = "  elena  "
print(f"Hello {name.strip().title()}")
```

```text
Hello Elena
```

## Watch out

**The `f` matters.** Without it, the braces are ordinary text:

```python
name = "Elena"
print("Hello {name}")
```

```text
Hello {name}
```

**The value is taken when the line runs.** The f-string uses what the variable holds at that moment. Changing the variable later does not change text you already made.
