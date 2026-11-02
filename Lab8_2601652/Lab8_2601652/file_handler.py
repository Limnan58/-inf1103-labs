import json
import os

from product import Product
from inventory import Inventory


class FileHandler:
    """Loads and saves an Inventory to a JSON file.

    Single responsibility: persistence (file I/O) only.
    """

    DEFAULT_PRODUCTS = [
        ("P001", "Laptop", 1200.00, 15),
        ("P002", "Mouse", 25.50, 40),
        ("P003", "Keyboard", 45.00, 25),
    ]

    def __init__(self, file_path):
        self.__file_path = file_path

    def load(self):
        inventory = Inventory()

        if not os.path.exists(self.__file_path):
            print("inventory.json not found. Starting with default inventory.\n")
            return self.__default_inventory()

        print("inventory.json found.")
        try:
            with open(self.__file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            for item in data:
                product = Product(item["id"], item["name"], item["price"], item["stock"])
                inventory.add_product(product)
            print("Inventory loaded successfully.\n")
            return inventory
        except (json.JSONDecodeError, OSError, KeyError, TypeError, ValueError):
            print("Warning: inventory.json is unreadable. Using defaults.\n")
            return self.__default_inventory()

    def save(self, inventory):
        data = [
            {"id": p.product_id, "name": p.name, "price": p.price, "stock": p.stock}
            for p in inventory.get_products()
        ]
        with open(self.__file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

    def __default_inventory(self):
        inventory = Inventory()
        for product_id, name, price, stock in self.DEFAULT_PRODUCTS:
            inventory.add_product(Product(product_id, name, price, stock))
        return inventory
