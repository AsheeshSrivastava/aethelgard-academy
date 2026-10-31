# Stage 0 build: reference solution. Never served to a learner.

# Ask for the applicant's name and the service they need.
raw_name = input("Name: ")
raw_service = input("Service needed: ")

# Clean both answers, because people type in messy ways.
name = raw_name.strip().title()
service = raw_service.strip().title()

# Print the slip the desk officer reads aloud.
print()
print("--- CHECK-IN SLIP ---")
print(f"Name: {name}")
print(f"Service: {service}")
print(f"Please wait for the {service} desk.")
