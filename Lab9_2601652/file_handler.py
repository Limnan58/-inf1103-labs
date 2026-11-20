import json
import os

from inventory import Inventory
from product import Product
from product_factory import ProductFactory
from supplier import Supplier


class FileHandler:

    # Used for records saved before Lab 8, which have no supplier.
    UNKNOWN_SUPPLIER: Supplier = Supplier("S000", "Unknown Supplier", "unknown@example.com")

    DEFAULT_SUPPLIERS: list[Supplier] = [
        Supplier("S001", "TechSource Pte Ltd", "sales@techsource.example"),
        Supplier("S002", "SoftWorks Digital", "orders@softworks.example"),
    ]

    DEFAULT_PRODUCTS: list[Product] = [
        ProductFactory.create("physical", "P001", "Laptop", 1200.00, 15,
                              DEFAULT_SUPPLIERS[0], weight=2.0),
        ProductFactory.create("physical", "P002", "Mouse", 25.50, 40,
                              DEFAULT_SUPPLIERS[0], weight=0.1),
        ProductFactory.create("digital", "P003", "Antivirus Software", 49.90, 100,
                              DEFAULT_SUPPLIERS[1], download_size=350.0),
    ]

    def __init__(self, file_path: str) -> None:
        self.__file_path: str = file_path

    def load(self) -> Inventory:
        if not os.path.exists(self.__file_path):
            print("inventory.json not found. Starting with default inventory.\n")
            return self.__default_inventory()

        print("inventory.json found.")
        try:
            with open(self.__file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            inventory = Inventory()
            # One Supplier object per supplier ID, shared by all its products.
            suppliers: dict[str, Supplier] = {}
            for item in data:
                inventory.add_product(self.__create_product(item, suppliers))
            print("Inventory loaded successfully.\n")
            return inventory
        except (json.JSONDecodeError, OSError, KeyError, TypeError, ValueError,
                AttributeError):
            print("Warning: inventory.json is unreadable. Using defaults.\n")
            return self.__default_inventory()

    def save(self, inventory: Inventory) -> None:
        data = [product.to_dict() for product in inventory.products]
        with open(self.__file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

    def __create_supplier(self, item: dict, suppliers: dict[str, Supplier]) -> Supplier:
        supplier_data = item.get("supplier")
        if supplier_data is None:
            return self.UNKNOWN_SUPPLIER

        key = str(supplier_data["id"]).strip().lower()
        if key not in suppliers:
            suppliers[key] = Supplier(supplier_data["id"], supplier_data["name"],
                                      supplier_data["contact_email"])
        return suppliers[key]

    def __create_product(self, item: dict, suppliers: dict[str, Supplier]) -> Product:
        product_type = item.get("type", "physical")
        supplier = self.__create_supplier(item, suppliers)

        # The factory decides which class to build and raises ValueError
        # for an unknown type.
        return ProductFactory.create(product_type, item["id"], item["name"],
                                     item["price"], item["stock"], supplier,
                                     weight=item.get("weight"),
                                     download_size=item.get("download_size"))

    def __default_inventory(self) -> Inventory:
        inventory = Inventory()
        for product in self.DEFAULT_PRODUCTS:
            inventory.add_product(product)
        return inventory
