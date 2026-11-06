import json
import os

from physical_product import PhysicalProduct
from digital_product import DigitalProduct
from inventory import Inventory


class FileHandler:

    DEFAULT_PRODUCTS = [
        PhysicalProduct("P001", "Laptop", 1200.00, 15, 2.0),
        PhysicalProduct("P002", "Mouse", 25.50, 40, 0.1),
        DigitalProduct("P003", "Antivirus Software", 49.90, 100, 350.0),
    ]

    def __init__(self, file_path):
        self.__file_path = file_path

    def load(self):
        if not os.path.exists(self.__file_path):
            print("inventory.json not found. Starting with default inventory.\n")
            return self.__default_inventory()

        print("inventory.json found.")
        try:
            with open(self.__file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            inventory = Inventory()
            for item in data:
                inventory.add_product(self.__create_product(item))
            print("Inventory loaded successfully.\n")
            return inventory
        except (json.JSONDecodeError, OSError, KeyError, TypeError, ValueError):
            print("Warning: inventory.json is unreadable. Using defaults.\n")
            return self.__default_inventory()

    def save(self, inventory):
        data = [product.to_dict() for product in inventory.get_products()]
        with open(self.__file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

    def __create_product(self, item):
        product_type = item.get("type", "physical")

        if product_type == "physical":
            return PhysicalProduct(item["id"], item["name"], item["price"],
                                   item["stock"], item.get("weight", 1.0))
        if product_type == "digital":
            return DigitalProduct(item["id"], item["name"], item["price"],
                                  item["stock"], item["download_size"])
        raise ValueError(f"Unknown product type: {product_type}")

    def __default_inventory(self):
        inventory = Inventory()
        for product in self.DEFAULT_PRODUCTS:
            inventory.add_product(product)
        return inventory
