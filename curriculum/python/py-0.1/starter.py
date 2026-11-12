"""Unit PY-0.1: Python as an executing program

You are following one visitor through the intake desk.
Python runs each line in order, and some lines change what a name points at.
Your job is to make those changes, then write down the state at each step.

Lines starting with '#' are comments. Python skips them.
"""

# Part 1: one name, a changing value

# Step 1 (done for you): take the visitor's name and set their status.
visitor = input("Visitor name: ")
status = "waiting"
print(visitor, status)

# Step 2: point status at the text "called".
# Then print visitor and status, the same way as the line above.
# (Your code here)


# Part 2: two names, one value

# Step 3: make a new name, previous_status, that points at the same value as status.
# Use status on the right side, not the text itself.
# (Your code here)


# Step 4: point status at the text "served". Do not change previous_status.
# (Your code here)


# Step 5: print status and previous_status, in that order.
# (Your code here)


# Part 3: a state table, filled in before you run anything

# Read these three lines and follow them in your head:
#     seen = 0
#     seen = seen + 1
#     seen = seen + 2
#
# Step 6: write the number seen points at after each line.
seen_after_line_1 = ...
seen_after_line_2 = ...
seen_after_line_3 = ...
