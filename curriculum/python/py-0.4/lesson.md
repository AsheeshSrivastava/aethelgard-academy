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
