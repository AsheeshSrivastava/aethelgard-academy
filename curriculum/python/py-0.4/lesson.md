# Unit PY-0.4: Run a First Program

## The Operational Context: The Communication Cycle

In operations, logistics, and policy systems, every process follows a disciplined communication cycle:
1. **Ingress (Intake):** External actors provide raw data across the system boundary.
2. **Transformation (Processing):** The system validates, normalizes, and structures the state.
3. **Egress (Output):** The system delivers a deterministic, confirmed response.

In Python, this exact lifecycle is managed through three core primitives:
- `input()`: Pauses program execution and reads text entered across the system boundary. **Key rule:** `input()` *always* returns a text string, even if the user typed numbers!
- String formatting: Packaging clean, normalized records (such as f-strings: `f"REGISTRATION: {name}"`).
- `print()`: Transmits the packaged message to the standard output stream (`stdout`).

Want more on any of these? Read the concept notes: [[variables]], [[expressions]] and [[print-function]].

---

## Everyday Tools: Cleaning Text

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
