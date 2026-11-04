# PY-0.2: Reading a Small Python Application

> **Draft for owner approval (2026-11-04).** Concept: a small application has an entry point, logic, data handling and configuration, and each file has a job.

---

## 1. Operational Context: The PantryFlow Intake App

The pantry's intake script has grown. It is now five files in one folder, and a new volunteer has to change it next week. Before anyone edits a line, you read the app and write down what each file is for.

```text
pantry_app/
  main.py        the entry point: run this file
  intake.py      cleans and checks what the clerk types
  allocation.py  decides how many parcels a family gets
  store.py       saves and loads family records (a JSON file today)
  settings.py    values that change between pantries, such as the stock reserve
```

## 2. Key Mental Models to Master

### A. Every file has one job
Read each file and finish the sentence "This file ...". If the sentence needs "and" twice, the file is doing too much. `intake.py` cleans and checks input. It does not decide parcels, and it does not save anything.

### B. The entry point starts the flow
`main.py` is the only file you run. It imports the others and calls them in order. The other files never import `main.py`.

### C. Data moves in one direction
When a family registers, the data moves like this:

```text
clerk types -> main.py -> intake.clean() -> allocation.parcels_for() -> store.save()
```

Each step receives a value, returns a value, and passes it on. Drawing this line is how you find where a bug can live.

### D. Python and its neighbours
`store.py` writes a JSON file today. A database could replace it later; that would be a change to `store.py` only. Sending a pickup SMS would be an outside service. Python calls it, but the SMS network is not Python. Knowing where Python stops keeps your map honest.

## 3. Local Workflow Instructions

1. Read the playground code top to bottom before running it.
2. Above each function, write a one-line comment saying what its job is.
3. Run it. The printed slip must stay the same.
