# TW-0.1: What a README Is For

> **The Concept:** A README answers, in order, what this does, what you need first, how to run it, what a run looks like, and where it stops working.

---

## 1. Operational Context: The Volunteer Who Cannot Start

A new volunteer joins the pantry on a Saturday. The coordinator says: "The door-sign script is in the folder. Print today's sign." The volunteer opens the folder and finds `door_sign.py`. Nothing else.

They do not know what it asks for, what to install, or which command starts it. They wait for the coordinator, who is busy. The script works perfectly, and it is still useless to them.

A **README** is the short file next to your code that a stranger reads first. Often that stranger is you, a month later.

---

## 2. The Five-Point Checklist

Every README in this course answers five questions:

1. **What it does.** One or two sentences, in plain words.
2. **What you need first.** Python version, `uv`, and any setup step.
3. **How to run it.** The **exact** command, ready to copy.
4. **A sample run.** Real input, and the output the script really prints.
5. **Limits.** What it does not do, so nobody relies on it for that.

---

## 3. A Weak README and a Good One

`door_sign.py` asks for the opening time and prints a sign.

**Weak:**

```text
Door sign script. Run it and type the time. Works great.
```

It says roughly what it does. It never says what to install, gives no command, shows no run, and "works great" is not a limit.

**Good:**

```text
What it does: prints today's door sign with the opening time.
What you need first: Python 3.12 or newer, and uv installed.
How to run it: uv run door_sign.py
Sample run:
  Opening time: 9am
  PANTRY OPEN TODAY FROM 9AM
Limits: one sign per run; it does not check that the time is real.
```

A volunteer can now run it alone, and knows what to expect.

---

## 4. How to Use the Checklist

When you read any README, go down the five points and ask: *is this here, and could a stranger act on it?* A point that is present but vague ("run the file") is not met.

You will do this next with READMEs for other pantry scripts. Then try the playground: it holds a small script with an empty README for you to fill.
