# inventory_manager.py
# Phase 2: Persistence — load inventory from JSON if it exists.

import json
import os

INVENTORY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "inventory.json")

DEFAULT_INVENTORY = [
    {"id": "P001", "name": "Laptop",   "price": 1200.00, "stock": 15},
    {"id": "P002", "name": "Mouse",    "price": 25.50,   "stock": 40},
    {"id": "P003", "name": "Keyboard", "price": 45.00,   "stock": 25},
]


def load_inventory():
    """Return the inventory as a list of dicts. Fall back to defaults if missing."""
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


def display_all(inventory):
    print("\nCurrent Inventory")
    print("-" * 60)
    for p in inventory:
        print(f"ID: {p['id']} | Name: {p['name']} | Price: ${p['price']:.2f} | Stock: {p['stock']}")
    print("-" * 60 + "\n")


def main():
    inventory = load_inventory()
    display_all(inventory)


if __name__ == "__main__":
    main()