# inventory_manager.py
# Phase 1: Data representation — a list of product dictionaries.

DEFAULT_INVENTORY = [
    {"id": "P001", "name": "Laptop",   "price": 1200.00, "stock": 15},
    {"id": "P002", "name": "Mouse",    "price": 25.50,   "stock": 40},
    {"id": "P003", "name": "Keyboard", "price": 45.00,   "stock": 25},
]


def main():
    print("Inventory contains:")
    for p in DEFAULT_INVENTORY:
        print(f"ID: {p['id']} | Name: {p['name']} | Price: ${p['price']:.2f} | Stock: {p['stock']}")


if __name__ == "__main__":
    main()