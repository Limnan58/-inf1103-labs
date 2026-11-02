"""Main program: shows the menu, gets user input, and calls Inventory methods."""
import os

from product import Product
from file_handler import FileHandler


if os.path.isdir("/app/data"):
    INVENTORY_FILE = "/app/data/inventory.json"
else:
    INVENTORY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "inventory.json")


# ---------- Menu actions ----------

def add_product(inventory):
    print("\nAdd New Product")
    product_id = input("Product ID: ").strip()
    if not product_id:
        print("Error: Product ID cannot be empty.\n"); return
    if inventory.search_product(product_id) is not None:
        print(f"Error: Product ID {product_id} already exists.\n"); return

    name = input("Product Name: ").strip()
    try:
        price = float(input("Price: ").strip())
        stock = int(input("Stock Quantity: ").strip())
        product = Product(product_id, name, price, stock)   # Product validates itself
    except ValueError as e:
        print(f"Error: {e}\n"); return

    inventory.add_product(product)
    print("Product added successfully!\n")


def update_stock(inventory):
    print("\nUpdate Stock")
    product_id = input("Enter Product ID: ").strip()
    product = inventory.search_product(product_id)
    if product is None:
        print("Product not found.\n"); return

    print("\nProduct Found:")
    print(f"Name: {product.name}")
    print(f"Current Stock: {product.stock}\n")

    try:
        new_stock = int(input("New Stock Quantity: ").strip())
        inventory.update_stock(product_id, new_stock)
    except ValueError as e:
        print(f"Error: {e}\n"); return

    print("Stock updated successfully!\n")


def search_product(inventory):
    print("\nSearch Product")
    product_id = input("Enter Product ID: ").strip()
    product = inventory.search_product(product_id)
    if product is None:
        print("Product not found.\n"); return

    print("\nProduct Found")
    print("-" * 40)
    product.display_information()
    print("-" * 40 + "\n")


def save_inventory(file_handler, inventory):
    print("\nSaving inventory...")
    file_handler.save(inventory)
    print("Inventory saved successfully to inventory.json.\n")


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


# ---------- Main ----------

def main():
    file_handler = FileHandler(INVENTORY_FILE)
    inventory = file_handler.load()

    while True:
        print_menu()
        option = input("Enter option: ").strip()

        if option == "1":
            inventory.display_all()
        elif option == "2":
            add_product(inventory)
        elif option == "3":
            update_stock(inventory)
        elif option == "4":
            search_product(inventory)
        elif option == "5":
            save_inventory(file_handler, inventory)
        elif option == "6":
            save_inventory(file_handler, inventory)
            print("Thank you for using Inventory Management System.")
            print("Program terminated.")
            break
        else:
            print("Invalid option. Please choose 1-6.\n")


if __name__ == "__main__":
    main()
