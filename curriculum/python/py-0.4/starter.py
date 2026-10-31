"""Unit PY-0.4: Run a first program

Operational Context:
You are building the intake desk for an operations center.
When an applicant arrives, the desk collects their name and ward code. People type
in messy ways, so the desk cleans the text before it prints a confirmation slip.

This practice is not graded. Run it, try messy input, and use Verify as often as you like.
"""

# Step 1: The desk asks for the raw details. input() always returns text.
raw_name = input("Applicant Name: ")
raw_ward = input("Ward Code: ")

# Step 2: Clean the name. Remove spaces at the ends, then use title case.
# Example: "   amara OKAFOR " should become "Amara Okafor"
clean_name = ...

# Step 3: Clean the ward code. Remove spaces at the ends, then use capitals.
# Example: " north-01 " should become "NORTH-01"
clean_ward = ...

# Step 4: Build the ticket by joining "TICKET-" and the queue number.
# The number must become text first, so use str().
# Example: "TICKET-7"
queue_number = 7
ticket = ...

# Step 5: Print the slip in exactly this format, using an f-string:
# REGISTRATION CONFIRMED: Amara Okafor [WARD-NORTH-01] TICKET-7
# (Your code here)

