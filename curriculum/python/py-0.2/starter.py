"""Unit PY-0.2: Reading a small Python application

Operational Context:
The PantryFlow intake app is normally five files. Here the same parts sit in one
file, each part marked with the file it would live in. Read it top to bottom.

Your task: above each function, write a one-line comment that says what its job is.
Run it after. The printed slip must not change.

This practice is not graded.
"""

# --- settings.py ---
STOCK_RESERVE = 5


# --- intake.py ---
def clean(name):
    return name.strip().title()


# --- allocation.py ---
def parcels_for(family_size):
    return 1 if family_size <= 2 else 2


# --- store.py ---
def save(records, name, parcels):
    records.append({"name": name, "parcels": parcels})
    return records


# --- main.py (the entry point) ---
records = []
name = clean("  asha rao ")
parcels = parcels_for(4)
records = save(records, name, parcels)
print(f"{name}: {parcels} parcels (records saved: {len(records)})")
