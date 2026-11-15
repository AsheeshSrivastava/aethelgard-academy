# Working with dictionaries

## Keys and values
A dictionary stores pairs of a key and a value. Write one with curly braces: `person = {"name": "Asha", "age": 31}`. Look up a value with its key: `person["name"]`. Keys must be hashable, so strings, numbers and tuples work but lists do not.

## Missing keys
Reading a key that is not there raises `KeyError: 'email'`. Use `person.get("email")` to get None instead, or `person.get("email", "unknown")` to choose a default. Test with `"email" in person` before you read when you need to branch. `setdefault` reads a key and adds it with a default in one step.

## Looping over a dictionary
A plain `for key in person` loop visits the keys. Use `person.items()` to get each key and value together, `person.keys()` for keys only and `person.values()` for values only. Do not add or delete keys while looping, because Python raises `RuntimeError: dictionary changed size during iteration`.

## Updating and merging
Assign to a key to add or replace it. `person.update(other)` copies every pair from `other` into `person`. The `|` operator joins two dictionaries into a new one, and the right side wins when both have the same key. `del person["age"]` removes a pair, and `pop` removes it and hands back the value.
