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

        # 3 & 4. Accept integers, reject non-numeric strings
        if user_input.lstrip("-").isdigit():
            quantity = int(user_input)
        else:
            print("Error: Invalid input. Please enter a whole number.\n")
            continue

        # Reject negative values
        if quantity < 0:
            print("Error: Quantity cannot be negative.\n")
            continue

        # 5. Enforce total storage cap (500)
        if inventory + quantity > MAX_CAPACITY:
            print(f"Error: Over-stock! Storage is capped at {MAX_CAPACITY}. "
                  f"Current: {inventory}, Attempted: {quantity}, "
                  f"Remaining space: {MAX_CAPACITY - inventory}.\n")
            continue

        # Valid entry — update inventory
        inventory += quantity
        print(f"Accepted. Current inventory: {inventory}\n")


if __name__ == "__main__":
    main()