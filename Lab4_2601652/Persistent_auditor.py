# modular_auditor.py
# Simplified order tracker matching the target output format

ORDERS_FILE = "orders.txt"


def parse_tx_id(tx_id_str):
    """Extract the numeric part from a transaction ID (handles 'TX-001' and '1001')."""
    # Remove any non-numeric prefix like "TX-"
    numeric_part = tx_id_str.split("-")[-1]
    return int(numeric_part)


def next_transaction_id():
    """Generate a new transaction ID based on the existing file."""
    existing = load_inventory()
    if not existing:
        return 1001

    ids = [item["transaction_id"] for item in existing]
    # If all existing IDs are small (like 1, 2, 3 from old format), start at 1001
    max_id = max(ids)
    if max_id < 1000:
        return 1001
    return max_id + 1


def load_inventory(transaction_id=None):
    """Load saved products and quantities from orders.txt."""
    orders = []

    try:
        with open(ORDERS_FILE, "r", encoding="utf-8") as file:
            for line in file:
                line = line.strip()
                if not line:
                    continue

                parts = [part.strip() for part in line.split(",")]
                if len(parts) < 3:
                    continue

                # Take only the first 3 parts (ignore old UID if present)
                tx_id_str, product, quantity = parts[:3]

                # Convert 'TX-001' or '1001' into an integer
                try:
                    tx_id = parse_tx_id(tx_id_str)
                except (ValueError, IndexError):
                    continue

                if transaction_id is not None and str(tx_id) != str(transaction_id):
                    continue

                orders.append({
                    "transaction_id": tx_id,
                    "product": product,
                    "quantity": int(quantity)
                })

    except FileNotFoundError:
        return []

    return orders


def save_inventory(order_list, transaction_id=None):
    """Append only new items to orders.txt without duplicating past inventory."""
    existing = load_inventory(transaction_id) if transaction_id is not None else load_inventory()
    existing_keys = {(item["transaction_id"], item["product"]) for item in existing}

    new_items = []
    for item in order_list:
        key = (item.get("transaction_id"), item.get("product"))
        if key not in existing_keys:
            new_items.append(item)
            existing_keys.add(key)

    if not new_items:
        return

    with open(ORDERS_FILE, "a", encoding="utf-8") as file:
        for item in new_items:
            file.write(f"{item['transaction_id']},{item['product']},{item['quantity']}\n")


def display_history(order_list):
    """Display all products with quantities in the order history."""
    if not order_list:
        print("No products have been ordered yet.")
        return

    for item in order_list:
        print(f"{item['transaction_id']}, {item['product']}, {item['quantity']}")


def get_product_name():
    """Ask the user for a product name."""
    product = input("Enter Product Name: ").strip()

    if product == "":
        print("Error: Product name cannot be empty.\n")
        return None

    return product


def get_quantity():
    """Ask the user for a quantity."""
    quantity = input("Enter Quantity: ").strip()

    if not quantity.isdigit() or int(quantity) <= 0:
        print("Error: Quantity must be a positive whole number.\n")
        return None

    return int(quantity)


def main():
    # 1. Load and display current orders
    orders = load_inventory()
    
    print("Current Orders:\n")
    display_history(orders)
    print()  # Blank line

    # 2. Get user input
    product_name = get_product_name()
    if product_name is None:
        return

    quantity = get_quantity()
    if quantity is None:
        return

    # 3. Generate new ID and create the order record
    new_id = next_transaction_id()
    new_order = {
        "transaction_id": new_id,
        "product": product_name,
        "quantity": quantity
    }

    # 4. Display the newly added order
    print("\nNew Order Added:")
    print(f"{new_id},{product_name},{quantity}")

    # 5. Save to file
    save_inventory([new_order])
    print("\nOrder successfully saved to orders.txt")


if __name__ == "__main__":
    main()