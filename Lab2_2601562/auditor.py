# auditor.py
# Real-time stock delivery auditor

def main():
    # 1. Initialize inventory to zero
    inventory = 0
    MAX_CAPACITY = 500        # Total storage cap

    print("=== Stock Delivery Auditor ===")
    print(f"Storage capacity: {MAX_CAPACITY}")
    print("Type 'quit' to exit.\n")

    # 2. Continuous loop until user types 'quit'
    while True:
        user_input = input("Enter stock quantity: ").strip()

        # Exit condition
        if user_input.lower() == "quit":
            print(f"\nFinal inventory: {inventory}")
            print("Auditor shutting down. Goodbye!")
            break

        # 3, 4 & 5. Validate the entry with an if / elif / else chain
        if not user_input.lstrip("-").isdigit():
            # Not a number at all (e.g., "ten", "abc")
            print("Error: Invalid input. Please enter a whole number.\n")
        elif int(user_input) < 0:
            # Negative value
            print("Error: Quantity cannot be negative.\n")
        elif inventory + int(user_input) > MAX_CAPACITY:
            # Would exceed the 500 cap
            print(f"Error: Over-stock! Storage is capped at {MAX_CAPACITY}. "
                  f"Current: {inventory}, Attempted: {int(user_input)}, "
                  f"Remaining space: {MAX_CAPACITY - inventory}.\n")
        else:
            # Everything is valid — accept the delivery
            inventory += int(user_input)
            print(f"Accepted. Current inventory: {inventory}\n")


if __name__ == "__main__":
    main()