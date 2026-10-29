"""Unit PY-0.4: Run a first program

Operational Context:
You are building the intake desk for an operations center.
When an applicant arrives, the desk collects their name and ward code,
cleans up leading/trailing whitespace, and emits a standard confirmation slip.

Requirements:
1. Implement run_intake(name: str, ward_code: str) -> str:
   - Strip whitespace from name.
   - Strip whitespace and uppercase ward_code.
   - Return formatted string: "REGISTRATION CONFIRMED: <name> [WARD-<ward_code>]"
2. Interactive Execution:
   - If executed directly as a script (__name__ == "__main__"):
     Prompt for name via input("Applicant Name: ")
     Prompt for ward code via input("Ward Code: ")
     Print the output returned by run_intake().
"""

def run_intake(name: str, ward_code: str) -> str:
    # TODO: Implement the operational intake formatting
    pass


if __name__ == "__main__":
    # TODO: Connect input() ingress to run_intake() and print() egress
    pass
