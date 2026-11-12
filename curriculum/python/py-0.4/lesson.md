# Unit PY-0.4: Run a First Program

## Why it matters

At the PantryFlow intake desk, people type their name as `" meera "` or `"MEERA"`. The desk officer needs a clean slip to read aloud. By the end of this lesson you can turn messy typing into that slip.

Most work you already know follows the same three steps: something comes in, you tidy it, and something goes out. A first program does the same. At the end you will also write a short README for it, so a stranger can run it.

---

## Run a script

A program is a text file that Python reads and runs from top to bottom. Three steps run any program.

```steps
caption: Picture to remember: a recipe card. Write it, save it, follow it.

title: Check Python
code: python --version
result: Python 3.12.4
note: If the command is not found, Python is not installed, or your computer cannot find it.

title: Save the file
code: welcome.py
result: a text file that ends in .py
note: Save before you run. Python reads what is saved on disk, not what is only on your screen.

title: Run it
code: uv run welcome.py
result: Name:
note: Python runs the file from the top and stops at the end.
```

On some computers the command is `python3`, not `python`. In this course we run files with `uv run`.

You can also try one line at a time at the **interactive prompt**, called the REPL. Type `python` in the terminal and press Enter. It shows `>>>` when it is ready, and you do not type the `>>>`. The app's playground also lets you try a line without setting anything up.

| | Interactive prompt (REPL) | Script file |
| --- | --- | --- |
| You type | one line, then Enter | a whole file, then run it |
| Shows results | `2 + 3` shows `5` straight away | only what `print()` shows |
| Good for | trying a small idea | a program you will run again |

> **Key idea:** a script runs the same way each time. Only what people type changes.

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

Run the same program twice with different typing. The three steps stay the same. Only the slip changes: `" meera "` gives `Name: Meera`, and `"JOSEPH"` gives `Name: Joseph`.

Want more on any of these? Read the concept notes: [[built-in-input]], [[variables]], [[expressions]], [[formatted-strings]], [[print-function]] and [[standard-streams]].

---

## Comments

A **comment** starts with `#`. Python skips it. It is a note for the next reader, who may be you in a month.

```python
# Ask for the name, then print the slip
name = input("Name: ")  # the desk officer reads this aloud
```

A good comment says *why*, not what the line already says. A `#` inside quotes, as in `"Room #4"`, is ordinary text, not a comment. See [[comments-in-python]].

```quickcheck
id: py-0.4-comments
question: Which line does Python skip when it runs the file?
A: `name = input("Name: ")`
B: `# Ask for the name`
C: `print("Room #4")`
```

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

## Your first README

A README is a short file beside your script. It is for someone who has never seen the script, including you in a month. Five points cover it. Here they are for the slip program:

| Point | The slip program's answer |
| --- | --- |
| What it does | Prints a slip with a clean name and service. |
| What you need first | Python 3.12 or newer, and uv. |
| How to run it | `uv run checkin.py` |
| A sample run | One real run, pasted in. |
| Limits | One person per run; it does not save anything. |

> **Key idea:** copy the sample run from a real run, never from memory. TW-0.1 and TW-0.2 go deeper on READMEs.

---

## Verify in the Official Docs

Open the [`input()` entry](https://docs.python.org/3/library/functions.html#input) in the Python docs. Find the sentence that says what type `input()` returns. Then read what it strips from the end of the line, and what it leaves alone.

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
