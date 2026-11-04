# PY-1.2: Numbers, Booleans and None

> **Draft for owner approval (2026-11-04).** Only what the Make step needs. Concept: every value has a type, and the type decides what operations mean.

---

## 1. Operational Context: Weighing a Donation

A supplier drops off rice at the pantry. The clerk types the price per kilogram and the number of kilograms, and the counter needs the donation's value for the records.

## 2. Key Mental Models to Master

### A. Every value has a type
`12` is an `int`, `12.5` is a `float`, `True` is a `bool`, and `None` means "no value yet". The type decides what `+` and `*` mean.

### B. `input()` always gives text
`input()` returns a `str`, even when the clerk types `40`. `"40" * 3` is `"404040"`, not `120`. Turn text into a number first with `int()` or `float()`.

### C. Text that is not a number stops the program
`float("forty")` stops with a `ValueError`. In this unit the clerk always types numbers. PY-2.1 turns away an empty or out-of-range answer with a clear message, and PY-4.3 does the same for text that is not a number.

### D. Rounding
`round(99.999, 2)` gives `100.0`. Money and weights are rounded before they are recorded.

## 3. Make

Write the donation calculator from a blank file. The Build step checks it with tests you cannot see.
