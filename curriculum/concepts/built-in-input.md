---
id: built-in-input
title: input() function
category: Core tools
summary: input() pauses the program, reads what the person types, and always gives it back as text.
status: approved
units: ["PY-0.1", "PY-0.4"]
related: ["print-function", "variables", "assignment-evaluation", "standard-streams"]
aliases: ["input", "keyboard", "ingress", "stdin", "read text"]
doc_url: https://docs.python.org/3/library/functions.html#input
---

`input()` is how a program takes data in. At the intake desk, it is the moment the terminal waits for an applicant's name. That first step is called ingress.

When Python reaches `input()`, three things happen:

1. It shows the prompt, the text inside the brackets.
2. It stops and waits until the person types something and presses Enter.
3. It gives back what was typed, as text, without the Enter.

```python
citizen_name = input("Enter citizen name: ")
print(citizen_name)
```

Python does the right side first, so the program waits at `input()` and only then stores the text. See [[assignment-evaluation]].

## Watch out

**`input()` always gives back text.** If someone types `100`, you get the text `"100"`, not the number 100. Python never guesses, and that protects real data: a guess could drop the leading zero from an ID like `"01234"`. Changing text into a number is a step you write yourself.

**`input()` keeps spaces.** People type in messy ways, so clean the text with `.strip()` before you use it.
