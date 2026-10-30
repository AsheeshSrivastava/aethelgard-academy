"""Unit PY-0.3: Tool help versus your own reasoning

Operational Context:
At the intake desk, an intern used an AI coding assistant to generate a quick snippet
for formatting ticket IDs. The AI output looked clean and ran without errors, but
on the first morning of live intake, the desk's barcode scanner rejected every ticket!

Why? The AI code assumed user input is always clean and forgot to strip whitespace:
    AI snippet: f"INTAKE-2026-{raw_name.upper()}"
    Failing input: "   amara okafor   " -> produced "INTAKE-2026-   AMARA OKAFOR   "

As the systems engineer, your job is not to avoid AI tools, but to OWN THE DECISION.
Complete the steps below to fix the code and establish the developer ownership boundary.
"""

# ==============================================================================
# PART 1: FIXING THE AI ASSUMPTION (BU-1 / VE-4)
# ==============================================================================

# Step 1: Simulate the applicant typing their name with messy spaces
raw_applicant_name = "   amara okafor   "

# Step 2: Fix the AI flaw. Strip the whitespace and make it uppercase.
# Store the clean name in 'verified_name'.
# (Your code here)
verified_name = ...

# Step 3: Generate the official ticket ID formatted as:
# "INTAKE-2026-<verified_name>"
# Store the ticket in 'official_ticket'.
# (Your code here)
official_ticket = ...

# Step 4: Display the official ticket using print()
# (Your code here)


# ==============================================================================
# PART 2: THE OWNERSHIP MATRIX (DE-3)
# Classify each engineering task as either "DELEGATE_OK" or "MUST_OWN".
# ==============================================================================

# Task A: Writing initial syntax boilerplate or looking up standard library method names
task_a_classification = ...  # Choose: "DELEGATE_OK" or "MUST_OWN"

# Task B: Deciding system requirements, privacy guardrails, and data retention rules
task_b_classification = ...  # Choose: "DELEGATE_OK" or "MUST_OWN"

# Task C: Verifying that code actually passes tests on messy edge cases before deployment
task_c_classification = ...  # Choose: "DELEGATE_OK" or "MUST_OWN"


# ==============================================================================
# PART 3: THE SOURCE OF TRUTH (DE-4)
# When an AI companion says a function works one way, but official docs or tests
# show another, which is the authoritative source of truth?
# ==============================================================================

# Choose: "AI_COMPANION" or "OFFICIAL_DOCS_AND_TESTS"
authoritative_source = ...
