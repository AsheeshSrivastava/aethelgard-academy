---
id: variables
title: Variables
category: Core tools
summary: A variable is a name that points to a value, so your program can use it later.
status: approved
units: ["PY-0.1", "PY-0.4"]
related: ["expressions", "print-function"]
aliases: ["variable", "=", "assignment", "name", "store a value", "state"]
doc_url: https://docs.python.org/3/reference/executionmodel.html#naming-and-binding
---

A variable is a name for a value. Think of a label tied to a file at the intake desk: the label lets you find the file again.

```python
applicant_name = input("Name: ")
print(applicant_name)
```

## What `=` means

In Python, `=` does not mean "is equal to". It means "work out the right side, then give that value this name".

So Python always does the right side first. That is why this line makes sense:

```python
name = "   amara   "
name = name.strip()
print(name)
```

```text
amara
```

The second line reads the old value, cleans it, and points `name` at the new text. The right side here is an [[expressions|expression]].

## Choosing a name

- Use letters, digits and underscores. A name cannot start with a digit.
- Capitals matter: `name` and `Name` are two different variables.
- Say what the value is. `zone_code` tells the next reader far more than `x`.

## Watch out

**A variable does not exist until its line has run.** Python goes from top to bottom, so this fails on the first line:

```python
print(zone)
zone = "NORTH-01"
```

```text
NameError: name 'zone' is not defined
```

**Spelling counts.** If you store `zone_code` and later type `zone_cod`, Python treats it as a name that does not exist and gives the same `NameError`.

**Text from `input()` stays text.** If someone types `7`, the variable holds the text `"7"`, not the number 7.
