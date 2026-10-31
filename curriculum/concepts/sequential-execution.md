---
id: sequential-execution
title: Top-to-bottom execution
category: Execution model
summary: Python runs statements one at a time, from the top of the file to the bottom.
status: draft
units: ["PY-0.1", "PY-0.4"]
related: ["variables", "assignment-evaluation"]
aliases: ["execution order", "line by line", "statements", "top to bottom", "NameError"]
doc_url: https://docs.python.org/3/reference/executionmodel.html
---

Python runs your file one statement at a time, starting at the top. Each line finishes completely before the next one starts.

```python
station = "Desk A"
print(f"Location: {station}")
```

```text
Location: Desk A
```

The second line can read `station` because the first line has already run.

## Watch out

**Python never looks ahead.** Your eyes can jump to the end of a file. Python cannot. A [[variables|variable]] does not exist until the line that creates it has run, so using it earlier stops the program:

```python
print(station)
station = "Desk A"
```

```text
NameError: name 'station' is not defined
```

**When reading code, go line by line.** To predict what a program does, start at the top and write down what each variable holds after each line. This habit is called tracing.
