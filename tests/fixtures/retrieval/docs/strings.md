# Working with strings

## Joining and formatting
An f-string puts values inside text: `f"Hello {name}, you have {count} items"`. Add a format after a colon, such as `{price:.2f}` for two decimal places. You cannot add a number to a string with plus. `"Total: " + 5` raises `TypeError: can only concatenate str (not "int") to str`, so convert with `str(5)` or use an f-string.

## Splitting and joining
`"a,b,c".split(",")` returns the list `['a', 'b', 'c']`. With no argument, `split()` breaks on any whitespace. The reverse is `",".join(parts)`, where the text before `.join` goes between the items. Every item must already be a string.

## Cleaning text
`strip()` removes spaces and newlines from both ends, `lower()` and `upper()` change case, and `replace("old", "new")` swaps text. Strings are immutable, so these methods return a new string and the original is unchanged. You must assign the result: `name = name.strip()`.

## Searching and slicing
`"py" in text` tests for a substring. `text.find("py")` returns the position or -1, while `text.index("py")` raises `ValueError` when it is missing. Slices work as on lists: `text[:3]` gives the first three characters. `startswith` and `endswith` test the ends.
