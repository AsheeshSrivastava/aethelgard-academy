# PY-0.1: Python as an Executing Program

> **The Concept:** Python runs statements in order, and each statement can change the program's state.

---

## 1. Operational Context: The Intake Reception Desk

Welcome to your first backend assignment on the **Intake Desk Spine**.

Imagine you are deploying the reception terminal for a municipal assistance center. When a citizen arrives at the desk:
1. The terminal pauses and prompts for their name (**Ingress** via `input()`).
2. The program captures the entered text into computer memory (**State** via a `variable`).
3. The program formats and outputs their verification record to the screen (**Egress** via `print()`).

---

## 2. Operational Reference Desk (Official Anchors)

In professional software development, consulting documentation is an engineer's everyday workbench tool. Below are the official documentation anchors for the tools you are using today:

| Term | Role in the System | Official Documentation |
| :--- | :--- | :--- |
| **Comments (`#`)** | Human-readable notes ignored by Python; used as pseudocode blueprints. | [Python Comments Syntax](file:///d:/01-Project/lms/reference/upstream/python-docs/tutorial/introduction.md) |
| **`input()`** | Built-in function that pauses execution and **returns** whatever text the user types as a string (`str`). | [Python Built-in input()](file:///d:/01-Project/lms/reference/upstream/python-docs/tutorial/introduction.md) |
| **Variables (`=`)** | A labeled reference in memory that captures and holds a value. | [Python Execution Model & Names](file:///d:/01-Project/lms/reference/upstream/python-docs/reference/executionmodel.md) |
| **`print()`** | Built-in function that outputs data to the terminal console. | [Python Formatted Output](file:///d:/01-Project/lms/reference/upstream/python-docs/tutorial/inputoutput.md) |
| **f-strings (`f"..."`)** | Modern string formatting that dynamically injects variables into text inside `{curly_braces}`. | [Python Formatted String Literals](file:///d:/01-Project/lms/reference/upstream/python-docs/tutorial/inputoutput.md) |

Want more on any of these? Read the concept notes: [[comments-in-python]], [[variables]] and [[print-function]].

---

## 3. Key Mental Models to Master

### A. Execution Order: Statement by Statement
Python reads your script strictly from **top to bottom**. Line 1 runs before Line 2. A variable does not exist in memory until the line that creates it has executed.

### B. Functions and Return Values
When you call `input("Enter name: ")`:
- Python displays the prompt.
- The user types their name and presses `Enter`.
- The function finishes and **returns** the text.
- The `=` operator catches that returned text and stores it in your [[variables|variable]]:
  ```python
  applicant_name = input("Enter name: ")
  ```

### C. Screen Output vs. Code Layout
Leaving a blank line in your Python file does **not** create a blank line on the terminal. To print a blank line on the terminal, you must explicitly call the [[print-function|output function]] with no arguments:
```python
print()
```

---

## 4. Local Workflow Instructions

1. **Pull the Exercise:**
   ```bash
   uv run lms pull PY-0.1
   ```
2. **Open in Zed or VS Code:**
   Open `workspace/PY-0.1/solution.py`.
3. **Follow the Numbered Steps:**
   Complete Steps 1 through 6 under the pseudocode comments.
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
   uv run lms explain PY-0.1 "Python executes statements top-to-bottom in order, input() returns text that a variable stores, and calling print() with no arguments outputs a blank line."
   ```
