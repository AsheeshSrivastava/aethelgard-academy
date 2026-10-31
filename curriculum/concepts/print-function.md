---
id: print-function
title: print() function
category: Core tools
summary: print() shows values on the terminal, which is how a program talks back.
status: draft
units: ["PY-0.1", "PY-0.4"]
related: ["variables", "expressions", "comments-in-python"]
aliases: ["print", "output", "egress", "stdout", "show on screen"]
doc_url: https://docs.python.org/3/library/functions.html#print
---

`print()` shows a value on the terminal. It is the last step of the intake desk cycle: the program takes data in, changes it, then gives a result back. That last step is called egress.

```python
print("REGISTRATION CONFIRMED")
```

```text
REGISTRATION CONFIRMED
```

## What goes inside the brackets

**Text in quotes** is shown as it is. A name without quotes is a [[variables|variable]], so Python shows the value it holds.

```python
name = "Amara"
print("name")
print(name)
```

```text
name
Amara
```

**Several values, with commas.** `print()` puts one space between them.

```python
print("Hello", "Amara")
```

```text
Hello Amara
```

**Any [[expressions|expression]].** Python works out the value first, then shows it.

```python
print(2 + 3)
print(f"TICKET-{2 + 3}")
```

```text
5
TICKET-5
```

**Nothing at all.** An empty `print()` shows a blank line.

## Watch out

**A blank line in your code does not print a blank line.** Python skips blank lines in the file. To get one on the terminal, call `print()` with nothing inside.

**`print()` shows a value but does not keep it.** Once it is on the screen, your program cannot use it again. If you need the value later, store it in a variable first, then print the variable.
