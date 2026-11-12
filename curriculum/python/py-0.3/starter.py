"""Unit PY-0.3: Tool help versus your own reasoning

At the intake desk, an intern asked an AI tool for code to make ticket IDs:
    AI snippet: f"INTAKE-2026-{raw_name.upper()}"
    Messy input: "   amara okafor   " -> "INTAKE-2026-   AMARA OKAFOR   "

Stripping the spaces gives "INTAKE-2026-AMARA OKAFOR", which still has a space
inside, is not unique, and prints a person's name on a barcode.
The better design builds the ID from the visitor's queue number instead.

Your job is not to avoid AI tools. It is to own the decision.
"""

# ==============================================================================
# PART 1: A BETTER TICKET ID
# ==============================================================================

# Step 1 (done for you): the kiosk gives the queue number as text, with stray spaces.
raw_queue_number = "  7 "

# Step 2: Remove the spaces at both ends.
# Store the clean number in 'verified_number'.
# (Your code here)
verified_number = ...

# Step 3: Build the official ticket ID formatted as:
# "INTAKE-2026-<verified_number>"
# Store the ticket in 'official_ticket'.
# (Your code here)
official_ticket = ...

# Step 4: Display the official ticket using print()
# (Your code here)


# ==============================================================================
# PART 2: THE OWNERSHIP MATRIX (DE-3)
# Classify each engineering task as either "DELEGATE_OK" or "MUST_OWN".
# ==============================================================================

# Task A: Looking up a method name, or drafting boilerplate for a function you have already designed
task_a_classification = ...  # Choose: "DELEGATE_OK" or "MUST_OWN"

# Task B: Deciding system requirements, privacy guardrails, and data retention rules
task_b_classification = ...  # Choose: "DELEGATE_OK" or "MUST_OWN"

# Task C: Deciding which messy inputs the code must handle, and what the right result is for each
task_c_classification = ...  # Choose: "DELEGATE_OK" or "MUST_OWN"


# ==============================================================================
# PART 3: THE SOURCE OF TRUTH (DE-4)
# When an AI companion says a function works one way, but official docs or tests
# show another, which is the authoritative source of truth?
# ==============================================================================

# Choose: "AI_COMPANION" or "OFFICIAL_DOCS_AND_TESTS"
authoritative_source = ...
