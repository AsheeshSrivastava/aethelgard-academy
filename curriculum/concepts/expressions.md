---
id: expressions
title: Expressions
category: Core tools
summary: An expression is any piece of code that Python can work out to a single value.
status: approved
units: ["PY-0.4"]
related: ["variables", "print-function"]
aliases: ["expression", "evaluate", "value", "statement"]
doc_url: https://docs.python.org/3/reference/expressions.html
---

An expression is a piece of code that gives a value. Python works it out, and what comes back can be stored or shown.

| Expression | Its value |
| --- | --- |
| `7` | `7` |
| `"amara"` | `"amara"` |
| `2 + 3` | `5` |
| `"  amara ".strip()` | `"amara"` |
| `str(7)` | `"7"` |

A [[variables|variable]] on its own is also an expression: its value is what it holds.

## Where they go

Anywhere Python needs a value. The three places you see most:

```python
queue_number = 2 + 3                  # The right side of =
print("TICKET-" + str(queue_number))  # Inside print()
print(f"Ticket {queue_number + 1}")   # Inside the {} of an f-string
```

```text
TICKET-5
Ticket 6
```

The inside of [[print-function|print()]] is an expression, and so is each `{}` in an f-string. That is why you can do small sums there.

## Expression or statement

A **statement** is a full instruction. An **expression** is a value inside one.

```python
name = "amara".title()
```

The whole line is a statement: it tells Python to store something. The part on the right, `"amara".title()`, is the expression that gives `"Amara"`.

## How Python works one out

Python goes from the inside out, and from left to right along a chain:

```python
name = "   amara OKAFOR ".strip().title()
```

First `.strip()` gives `"amara OKAFOR"`. Then `.title()` works on that and gives `"Amara Okafor"`.

## Watch out

**The value's type decides what `+` does.** Two numbers add. Two pieces of text join.

```python
print(2 + 3)
print("2" + "3")
```

```text
5
23
```

Text and a number cannot be mixed, so `"TICKET-" + 7` stops with a `TypeError`. Turn the number into text first: `"TICKET-" + str(7)`.
