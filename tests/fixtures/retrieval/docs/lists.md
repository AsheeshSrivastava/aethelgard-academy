# Working with lists

## Creating and changing a list
A list holds items in order. Write it with square brackets, such as `scores = [4, 8, 15]`. You can change a list after you create it, so lists are called mutable. Assign to an index to replace an item: `scores[0] = 5`.

## Adding and removing items
Use `append` to add one item at the end and `extend` to add every item from another list. Use `insert` to put an item at a position. `remove` deletes the first item equal to a value, and `pop` removes and returns the item at an index. Methods such as `append`, `extend` and `sort` change the list in place and return None. A line like `scores = scores.append(3)` therefore sets `scores` to None, and the next call fails with `AttributeError: 'NoneType' object has no attribute 'append'`.

## Slicing
A slice takes part of a list: `items[1:3]` gives the items at index 1 and 2. The end index is not included. Negative indexes count from the end, so `items[-1]` is the last item. A slice makes a new list, which is a quick way to copy one: `copy = items[:]`.

## Sorting
`list.sort()` sorts the list in place. The built-in `sorted(items)` returns a new sorted list and leaves the original alone. Pass `reverse=True` for largest first, or `key=len` to sort by length. An `IndexError: list index out of range` means you asked for a position past the last item.
