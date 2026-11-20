import os

from can_be_shipped import CanBeShipped
from discount import (BulkDiscount, DiscountStrategy, NoDiscount,
                      PercentageDiscount, StudentDiscount)
from file_handler import FileHandler
from input_helpers import get_non_negative_int, get_positive_float, get_positive_int
from inventory import Inventory
from order import Order
from product import Product
from product_factory import ProductFactory
from product_loader import load_products
from supplier import Supplier


if os.path.isdir("/app/data"):
    INVENTORY_FILE: str = "/app/data/inventory.json"
else:
    INVENTORY_FILE: str = os.path.join(os.path.dirname(os.path.abspath(__file__)), "inventory.json")

if os.path.exists("/app/data/products.csv"):
    PRODUCTS_FILE: str = "/app/data/products.csv"
else:
    PRODUCTS_FILE: str = os.path.join(os.path.dirname(os.path.abspath(__file__)), "products.csv")


def show_product_details(product: Product) -> None:
    # Works with any Product. Each object supplies its own implementation.
    product.display_information()
    print(f"Fulfilment: {product.get_fulfilment_info()}")


def find_supplier(inventory: Inventory, supplier_id: str) -> Supplier | None:
    for product in inventory.products:
        if product.supplier.supplier_id.lower() == supplier_id.strip().lower():
            return product.supplier
    return None


def get_supplier(inventory: Inventory) -> Supplier:
    supplier_id = input("Supplier ID: ").strip()
    supplier = find_supplier(inventory, supplier_id)
    if supplier is not None:
        print(f"Using existing supplier: {supplier.name}")
        return supplier

    supplier_name = input("Supplier Name: ").strip()
    contact_email = input("Supplier Contact Email: ").strip()
    return Supplier(supplier_id, supplier_name, contact_email)


def add_product(inventory: Inventory) -> None:
    print("\nAdd New Product")
    print("Product type:")
    print("  1. Physical Product")
    print("  2. Digital Product")
    product_type = input("Choose type (1/2): ").strip()
    if product_type not in ("1", "2"):
        print("Error: Please choose 1 or 2.\n"); return

    product_id = input("Product ID: ").strip()
    if not product_id:
        print("Error: Product ID cannot be empty.\n"); return
    if inventory.find_product(product_id) is not None:
        print(f"Error: Product ID {product_id} already exists.\n"); return

    name = input("Product Name: ").strip()
    # The helpers keep asking until the value is valid, so we never carry on
    # with incomplete data.
    price = get_positive_float("Price: ")
    stock = get_non_negative_int("Stock Quantity: ")
    try:
        if product_type == "1":
            weight = get_positive_float("Weight (kg): ")
            supplier = get_supplier(inventory)
            product: Product = ProductFactory.create("physical", product_id, name, price,
                                                     stock, supplier, weight=weight)
        else:
            download_size = get_positive_float("Download Size (MB): ")
            supplier = get_supplier(inventory)
            product = ProductFactory.create("digital", product_id, name, price,
                                            stock, supplier, download_size=download_size)
    except ValueError as e:
        print(f"Error: {e}\n"); return

    inventory.add_product(product)
    print("Product added successfully!\n")


def update_stock(inventory: Inventory) -> None:
    print("\nUpdate Stock")
    product_id = input("Enter Product ID: ").strip()
    product = inventory.find_product(product_id)
    if product is None:
        print("Product not found.\n"); return

    print("\nProduct Found:")
    print(f"Name: {product.name}")
    print(f"Current Stock: {product.stock}\n")

    new_stock = get_non_negative_int("New Stock Quantity: ")
    inventory.update_stock(product_id, new_stock)

    print("Stock updated successfully!\n")


def search_product(inventory: Inventory) -> None:
    print("\nSearch Product")
    product_id = input("Enter Product ID: ").strip()
    product = inventory.find_product(product_id)
    if product is None:
        print("Product not found.\n"); return

    print("\nProduct Found")
    print("-" * 40)
    show_product_details(product)
    product.supplier.display_information()
    if isinstance(product, CanBeShipped):
        print(f"Shipping Cost: ${product.calculate_shipping_cost():.2f}")
    print("-" * 40 + "\n")


def remove_product(inventory: Inventory) -> None:
    print("\nRemove Product")
    product_id = input("Enter Product ID: ").strip()
    product = inventory.remove_product(product_id)
    if product is None:
        print("Product not found.\n"); return

    print(f"{product.name} removed from inventory.\n")


def choose_discount() -> DiscountStrategy:
    # The client chooses which strategy object to create. Order itself
    # never sees this choice; it only calls discount.apply().
    print("Discount:")
    print("  1. No discount")
    print("  2. Percentage discount")
    print("  3. Bulk discount")
    print("  4. Student discount (5%)")
    while True:
        choice = input("Choose discount (1-4): ").strip()
        if choice == "1":
            return NoDiscount()
        if choice == "2":
            while True:
                try:
                    return PercentageDiscount(get_positive_float("Percentage off: "))
                except ValueError as e:
                    print(f"Error: {e}")
        if choice == "3":
            threshold = get_positive_float("Minimum order total: ")
            amount = get_positive_float("Amount off: ")
            return BulkDiscount(threshold, amount)
        if choice == "4":
            return StudentDiscount()
        print("Please choose 1, 2, 3 or 4.")


def create_order(inventory: Inventory) -> None:
    print("\nCreate Order")
    try:
        order = Order(input("Order ID: ").strip())
    except ValueError as e:
        print(f"Error: {e}\n"); return

    while True:
        product_id = input("Product ID (leave blank to finish): ").strip()
        if not product_id:
            break
        product = inventory.find_product(product_id)
        if product is None:
            print("Product not found."); continue
        quantity = get_positive_int("Quantity: ")
        order.add_order_line(product, quantity)
        print(f"Added {product.name} x {quantity}.")

    print()
    order.set_discount(choose_discount())
    print()
    order.display_information()
    print()


def load_products_from_csv(inventory: Inventory) -> None:
    print(f"\nLoad Products from {os.path.basename(PRODUCTS_FILE)}")
    print("Which supplier provides these products?")
    try:
        supplier = get_supplier(inventory)
    except ValueError as e:
        print(f"Error: {e}\n"); return
    load_products(PRODUCTS_FILE, inventory, supplier)
    print()


def save_inventory(file_handler: FileHandler, inventory: Inventory) -> None:
    print("\nSaving inventory...")
    file_handler.save(inventory)
    print("Inventory saved successfully to inventory.json.\n")


def print_menu() -> None:
    print("=" * 44)
    print("INVENTORY MANAGEMENT SYSTEM")
    print("=" * 44)
    print("\n--------- MENU ---------")
    print("1. Display All Products")
    print("2. Add Product")
    print("3. Update Stock")
    print("4. Search Product")
    print("5. Remove Product")
    print("6. Create Order")
    print("7. Load Products from CSV")
    print("8. Save Inventory")
    print("9. Exit")
    print("------------------------\n")


def main() -> None:
    file_handler = FileHandler(INVENTORY_FILE)
    inventory = file_handler.load()

    while True:
        print_menu()
        option = input("Enter option: ").strip()

        if option == "1":
            inventory.display_all_products()
        elif option == "2":
            add_product(inventory)
        elif option == "3":
            update_stock(inventory)
        elif option == "4":
            search_product(inventory)
        elif option == "5":
            remove_product(inventory)
        elif option == "6":
            create_order(inventory)
        elif option == "7":
            load_products_from_csv(inventory)
        elif option == "8":
            save_inventory(file_handler, inventory)
        elif option == "9":
            save_inventory(file_handler, inventory)
            print("Thank you for using Inventory Management System.")
            print("Program terminated.")
            break
        else:
            print("Invalid option. Please choose 1-9.\n")


if __name__ == "__main__":
    main()
