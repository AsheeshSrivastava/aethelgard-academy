---
id: comments-in-python
title: Comments in Python
category: Core tools
summary: A comment is a note for people, and Python skips it.
status: draft
units: ["PY-0.1"]
related: ["print-function", "variables"]
aliases: ["#", "comment", "hash", "pseudocode", "notes in code"]
doc_url: https://docs.python.org/3/reference/lexical_analysis.html#comments
---

A comment starts with `#`. Python ignores everything from the `#` to the end of that line.

```python
# Ask the applicant for their name.
name = input("Name: ")

print(name)  # This comment sits after working code.
```

The first line does nothing when the program runs. The last line still runs its `print()`, and only the part after `#` is skipped.

## Why write them

**To plan before you code.** At the intake desk, you can write the steps as comments first, then fill in the code under each one. This is called pseudocode.

```python
# Read the applicant's name.
# Clean the spaces from the name.
# Print the confirmation.
```

**To say why.** The code already shows what it does. A comment earns its place when it says something the code cannot, such as why a step is there.

```python
# The scanner rejects tickets that hold spaces.
name = name.strip()
```

## Watch out

**A `#` inside quotes is not a comment.** It is part of the text, so this prints the whole line:

```python
print("Ticket #7")
```

```text
Ticket #7
```

**Python never checks a comment.** If you change the code and forget the comment, the comment is now wrong and nothing warns you. Update them together.
