# modular_auditor.py
# Refactored stock delivery auditor (Week 3)

MAX_CAPACITY = 500  # Total storage is 500


def get_valid_input():
    """Prompt the user for a stock quantity.
    Returns an int if valid, or the string 'quit' to signal exit."""
    user_input = input("Enter stock quantity: ").strip()

    if user_input.lower() == "quit":
        return "quit"

    # Validation: must be a whole number (allows leading minus for error msg)
    if not user_input.lstrip("-").isdigit():
        print("Error: Invalid input. Please enter a whole number.\n")
        return None

    value = int(user_input)

    if value < 0:
        print("Error: Quantity cannot be negative.\n")
        return None

    return value


def process_delivery(current_total, new_value):
    """Add the new delivery amount to the running total.
    Returns the updated total."""
    return current_total + new_value


def calculate_tax(amount):
    """Return 10% tax on the given delivery amount."""
    return amount * 0.10


def generate_report(total_units, failed_attempts):
    """Print the final summary of the audit session."""
    print("\n=== Audit Report ===")
    print(f"Total Deliveries Processed: {total_units}")
    print(f"Number of Failed/Rejected Entries: {failed_attempts}")
    print(f"Final inventory: {total_units}")
    print("Auditor shutting down. Goodbye!")


def main():
    # 1. Initialize inventory and counters to zero
    inventory = 0
    deliveries_processed = 0
    failed_attempts = 0

    print("=== Stock Delivery Auditor ===")
    print(f"Storage capacity: {MAX_CAPACITY}")
    print("Type 'quit' to exit.\n")

    # 2. Continuous loop
    while True:
        value = get_valid_input()

        # Exit condition
        if value == "quit":
            break

        # Failed validation (None) or capacity overflow
        if value is None:
            failed_attempts += 1
            continue

        if inventory + value > MAX_CAPACITY:
            print(f"Error: Stock! Storage is capped at {MAX_CAPACITY}. "
                  f"Current: {inventory}, Attempted: {value}, "
                  f"Remaining space: {MAX_CAPACITY - inventory}.\n")
            failed_attempts += 1
            continue

        # 3. Valid delivery
        inventory = process_delivery(inventory, value)
        tax = calculate_tax(value)
        deliveries_processed += 1

        print(f"Accepted. Current inventory: {inventory} "
              f"(Tax on this delivery: ${tax:.2f})\n")

    # 4. Reporting
    generate_report(inventory, failed_attempts)


if __name__ == "__main__":
    main()