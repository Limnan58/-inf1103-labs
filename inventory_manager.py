# inventory_manager.py
# Phase 3: Full CRUD + persistence + menu system.

import json
import os

INVENTORY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "inventory.json")

DEFAULT_INVENTORY = [
    {"id": "P001", "name": "Laptop",   "price": 1200.00, "stock": 15},
    {"id": "P002", "name": "Mouse",    "price": 25.50,   "stock": 40},
    {"id": "P003", "name": "Keyboard", "price": 45.00,   "stock": 25},
]


# ---------- Persistence ----------

def load_inventory():
    if os.path.exists(INVENTORY_FILE):
        print("inventory.json found.")
        try:
            with open(INVENTORY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            print("Inventory loaded successfully.\n")
            return data
        except (json.JSONDecodeError, OSError):
            print("Warning: inventory.json is unreadable. Using defaults.\n")
            return list(DEFAULT_INVENTORY)

    print("inventory.json not found. Starting with default inventory.\n")
    return list(DEFAULT_INVENTORY)


def save_inventory(inventory):
    print("\nSaving inventory...")
    with open(INVENTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(inventory, f, indent=4)
    print("Inventory saved successfully to inventory.json.\n")


# ---------- CRUD ----------

def _find_product(inventory, product_id):
    for product in inventory:
        if product["id"].lower() == product_id.lower():
            return product
    return None


def display_all(inventory):
    print("\nCurrent Inventory")
    print("-" * 60)
    for p in inventory:
        print(f"ID: {p['id']} | Name: {p['name']} | Price: ${p['price']:.2f} | Stock: {p['stock']}")
    print("-" * 60 + "\n")


def add_product(inventory):
    print("\nAdd New Product")
    product_id = input("Product ID: ").strip()
    if not product_id:
        print("Error: Product ID cannot be empty.\n"); return
    if _find_product(inventory, product_id) is not None:
        print(f"Error: Product ID {product_id} already exists.\n"); return

    name = input("Product Name: ").strip()
    if not name:
        print("Error: Product name cannot be empty.\n"); return

    try:
        price = float(input("Price: ").strip())
        stock = int(input("Stock Quantity: ").strip())
    except ValueError:
        print("Error: Price must be a number and Stock must be a whole number.\n"); return

    if price < 0 or stock < 0:
        print("Error: Price and Stock must be non-negative.\n"); return

    inventory.append({"id": product_id, "name": name, "price": price, "stock": stock})
    print("Product added successfully!\n")


def update_stock(inventory):
    print("\nUpdate Stock")
    product_id = input("Enter Product ID: ").strip()
    product = _find_product(inventory, product_id)
    if product is None:
        print("Product not found.\n"); return

    print("\nProduct Found:")
    print(f"Name: {product['name']}")
    print(f"Current Stock: {product['stock']}\n")

    try:
        new_stock = int(input("New Stock Quantity: ").strip())
    except ValueError:
        print("Error: Stock must be a whole number.\n"); return

    if new_stock < 0:
        print("Error: Stock cannot be negative.\n"); return

    product["stock"] = new_stock
    print("Stock updated successfully!\n")


def search_product(inventory):
    print("\nSearch Product")
    product_id = input("Enter Product ID: ").strip()
    product = _find_product(inventory, product_id)
    if product is None:
        print("Product not found.\n"); return

    print("\nProduct Found")
    print("-" * 40)
    print(f"ID: {product['id']}")
    print(f"Name: {product['name']}")
    print(f"Price: ${product['price']:.2f}")
    print(f"Stock: {product['stock']}")
    print("-" * 40 + "\n")


# ---------- Menu ----------

def print_menu():
    print("=" * 44)
    print("INVENTORY MANAGEMENT SYSTEM")
    print("=" * 44)
    print("\n--------- MENU ---------")
    print("1. Display All Products")
    print("2. Add Product")
    print("3. Update Stock")
    print("4. Search Product")
    print("5. Save Inventory")
    print("6. Exit")
    print("------------------------\n")


def main():
    inventory = load_inventory()

    while True:
        print_menu()
        option = input("Enter option: ").strip()

        if option == "1":
            display_all(inventory)
        elif option == "2":
            add_product(inventory)
        elif option == "3":
            update_stock(inventory)
        elif option == "4":
            search_product(inventory)
        elif option == "5":
            save_inventory(inventory)
        elif option == "6":
            print("\nSaving inventory before exit...")
            with open(INVENTORY_FILE, "w", encoding="utf-8") as f:
                json.dump(inventory, f, indent=4)
            print("Inventory saved successfully.\n")
            print("Thank you for using Inventory Management System.")
            print("Program terminated.")
            break
        else:
            print("Invalid option. Please choose 1-6.\n")


if __name__ == "__main__":
    main()