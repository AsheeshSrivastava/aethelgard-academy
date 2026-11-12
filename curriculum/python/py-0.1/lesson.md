# PY-0.1: Python as an Executing Program

> **The Concept:** Python runs statements in order, and each statement can change the program's state.

---

## Why it matters

In PY-0.4 you ran a program that took a name in and printed a slip. This unit looks inside that run.

When a script gives the wrong answer, the fix starts with one question: what did each name hold at each line? By the end of this unit you can follow a short script line by line and write down what it holds.

---

## One statement at a time

A Python file is a list of statements. Python runs them one at a time, from top to bottom. A line cannot use something that a later line creates. Lines that start with `#` are [[comments-in-python|comments]], which Python skips. See [[sequential-execution]].

```python
print("Desk open")
print()
queue = 3
print("Waiting:", queue)
```

```text
Desk open

Waiting: 3
```

`print()` with nothing inside shows an empty line. A blank line in your file shows nothing at all.

---

## Statements and expressions

An **expression** is a piece of code that works out to a value: `3`, `"desk"`, `queue + 1`, `input()`.

A **statement** is a whole instruction that Python carries out, such as `queue = queue + 1` or `print(queue)`.

Most statements hold expressions. Python works out the expressions first, then does what the statement says. See [[expressions]].

Every value has a kind. `"waiting"` is text (`str`). `0` is a whole number (`int`). The kind decides what you can do with it: you can add 1 to `0`, but not to `"0"`.

---

## Names point at values

`=` gives a name to a value. In `queue = 3`, Python works out the right side, gets the value `3`, and points the name `queue` at it. See [[variables]].

Think of a name as a label tied to a value, not a box that holds it. If a later line says `queue = 4`, the label moves to the new value. Nothing else changes.

This matters when two names share a value:

```python
lead = "Ravi"
backup = lead
lead = "Lina"
print(lead, backup)
```

```text
Lina Ravi
```

Line 2 points `backup` at the value `lead` points at, which is `"Ravi"`. Line 3 moves only `lead`. `backup` still points at `"Ravi"`.

---

## State and the state table

A program's **state** is what each name holds at a given moment. Each assignment can change it.

To follow a script, write a **state table**: one row per line, with each name's value after that line runs.

```python
status = "waiting"
seen = 0
seen = seen + 1
status = "seen"
print(status, seen)
```

| After line | `status` | `seen` | Terminal shows |
| --- | --- | --- | --- |
| 1 | `"waiting"` | (no value yet) | |
| 2 | `"waiting"` | `0` | |
| 3 | `"waiting"` | `1` | |
| 4 | `"seen"` | `1` | |
| 5 | `"seen"` | `1` | `seen 1` |

Line 3 reads the old value of `seen`, adds 1, and points `seen` at the result. Line 5 changes nothing. `print()` only shows the state.

If the real output differs from what you predicted, find the first row where your table goes wrong. That row shows where your picture of the program slipped.

---

## Official docs

| Term | Official documentation |
| :--- | :--- |
| Names and binding | [Naming and binding](https://docs.python.org/3/reference/executionmodel.html#naming-and-binding) |
| Assignment (`=`) | [Assignment statements](https://docs.python.org/3/reference/simple_stmts.html#assignment-statements) |
| Expressions | [Expressions](https://docs.python.org/3/reference/expressions.html) |
| `input()` | [input()](https://docs.python.org/3/library/functions.html#input) |
| `print()` | [print()](https://docs.python.org/3/library/functions.html#print) |

Want more? Read the concept notes: [[sequential-execution]], [[expressions]], [[variables]] and [[assignment-evaluation]].

---

## Local Workflow Instructions

1. **Pull the Exercise:**
   ```bash
   uv run lms pull PY-0.1
   ```
2. **Open in Zed or VS Code:**
   Open `workspace/PY-0.1/solution.py`.
3. **Follow the Numbered Steps:**
   Complete Steps 2 to 6 under the comments.
4. **Test Interactively:**
   ```bash
   uv run python workspace/PY-0.1/solution.py
   ```
5. **Verify and Record Evidence:**
   ```bash
   uv run lms verify PY-0.1
   ```
6. **Submit Concept Check:**
   ```bash
   uv run lms explain PY-0.1 "Python runs each statement in order. An assignment works out the right side, then points the name at that value. Pointing one name at a new value does not move any other name."
   ```
