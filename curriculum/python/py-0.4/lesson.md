# Unit PY-0.4: Run a First Program

## Why it matters

At the PantryFlow intake desk, people type their name as `" meera "` or `"MEERA"`. The desk officer needs a clean slip to read aloud. By the end of this lesson you can turn messy typing into that slip.

Most work you already know follows the same three steps: something comes in, you tidy it, and something goes out. A first program does the same.

---

## In, clean, out

Python reads your file top to bottom. Most small programs follow the same three-step shape, and three built-in tools cover each step:

- `input()`: pauses the program and reads the text someone types.
- An f-string such as `f"Name: {name}"`: puts a value into a line of text.
- `print()`: shows the result on the screen.

```steps
caption: Picture to remember: a desk. Paper comes in, you tidy it, a slip goes out.

title: Take in
code: input("Name: ")
result: "  meera "
note: Waits for typing. Always gives back text.

title: Clean up
code: name.strip().title()
result: "Meera"
note: Fix spaces and capitals before you use it.

title: Send out
code: print(f"Name: {name}")
result: Name: Meera
note: Shows the result on the screen.
```

> **Key idea:** `input()` *always* hands you text, even when someone types a number. `"7"` is not `7`.

Want more on any of these? Read the concept notes: [[built-in-input]], [[variables]], [[expressions]], [[formatted-strings]], [[print-function]] and [[standard-streams]].

---

## Cleaning recipes

People type in messy ways, so real programs clean text as soon as it arrives. Learn these four as recipes. You do not need to know how they work yet.

| Tool | What it does | Example | Result |
| --- | --- | --- | --- |
| `.strip()` | Removes spaces at the two ends | `"  amara  ".strip()` | `"amara"` |
| `.title()` | Capitalises each word | `"amara okafor".title()` | `"Amara Okafor"` |
| `.upper()` | Makes every letter a capital | `"north-01".upper()` | `"NORTH-01"` |
| `str()` | Turns a value into text | `str(7)` | `"7"` |

You can ask the text to clean itself in one line, working left to right:

```python
name = "   amara OKAFOR ".strip().title()
```

**Notice the dot.** `str()` is a function: the value goes inside the brackets, like `print()`. `.strip()`, `.title()` and `.upper()` are called on the text with a dot. For now, treat that as how these tools are written; a later unit explains why.

**Keep the result.** These tools give you new text and leave the original alone. On its own, `name.strip()` changes nothing that you can use later. Store the result:

```python
name = name.strip()
```

**Tools have assumptions.** `.title()` follows a simple rule, so it gets some real names wrong: `"mcdonald".title()` gives `"Mcdonald"`, and `"van der berg".title()` gives `"Van Der Berg"`. It is fine for practice. In real work, check a tool against real data before you trust it.

```quickcheck
id: py-0.4-strip-upper
question: Someone types `  north-01 `. Which line gives `NORTH-01`?
A: `code.upper()`
B: `code.strip().upper()`
C: `code.title()`
```

---

## When Python stops: reading an error

Sooner or later a program stops with an error message. It is not a telling-off. It is Python saying where it got stuck and why.

Here is a two-line script with a typo in the second line:

```python
name = input("Name: ")
print("Welcome,", nmae)
```

Python runs line 1, waits for a name, then stops and shows this:

```text
Traceback (most recent call last):
  File "welcome.py", line 2, in <module>
    print("Welcome,", nmae)
                      ^^^^
NameError: name 'nmae' is not defined
```

Read it from the bottom up:

1. **The last line gives the type and the message.** `NameError` is the type. `name 'nmae' is not defined` says what went wrong.
2. **Above it is the line Python was running.** The `^^^^` marks the part it could not handle.
3. **Above that is the line number.** `line 2` tells you where to look.

Python stops at the first line it cannot run. Every line before it has already run, which is why `Name:` still appeared.

Three error types you will meet first:

| Type | What it means | A line that causes it |
| --- | --- | --- |
| `NameError` | Python does not know this name. It is misspelled, or used before the line that gives it a value. | `print(nmae)` |
| `TypeError` | An operation got the wrong kind of value, such as text joined to a number. Remember: `input()` always gives text. | `"TICKET-" + 7` |
| `SyntaxError` | The line is not written as Python expects. Python checks the whole file first, so no line runs at all. | `print("Zone:" zone)` (missing comma) |

When you meet an error, say three things before you change any code: the type, the line, and what the message means in plain words.

---

## Video Walkthrough

> [!TIP] Watch the walkthrough before writing code:
> **Video Walkthrough: Running Your First Program & The Communication Cycle**
> URL: `https://cdn.example.org/videos/py-0.4-communication-cycle.mp4` (Duration: 6m 00s)
> - **00:00** Interpreter Mental Model: Top-to-Bottom Execution
> - **01:45** Input Ingress: Why `input()` Always Returns Text
> - **03:30** Output Egress: Packaging with f-strings and `print()`
> - **04:50** Diagnosing Your First Error: Type, Message, Line Number

---

## Local Editor Instructions (Zed / VS Code)

1. Open your terminal in this workspace folder.
2. Edit `solution.py` using **Zed** (`zed solution.py`) or **VS Code** (`code solution.py`).
3. Run the automated verification test:
   ```bash
   uv run lms verify py-0.4
   ```
4. Once tests pass, submit your concept explanation:
   ```bash
   uv run lms explain py-0.4 "your mental model explanation"
   ```
