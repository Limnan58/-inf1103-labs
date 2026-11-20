import csv

from inventory import Inventory
from product_factory import ProductFactory
from supplier import Supplier


def load_products(path: str, inventory: Inventory, supplier: Supplier) -> int:
    """Load products from a CSV file into the inventory.

    Returns how many products were loaded. A missing file is reported, not
    raised, and a bad row is reported and skipped so the other rows still load.
    """
    loaded = 0
    try:
        file = open(path, newline="", encoding="utf-8")
    except FileNotFoundError:
        print(f"Products file not found: {path}")
    else:
        with file:
            reader = csv.reader(file)
            next(reader, None)  # skip the header row
            for line_number, row in enumerate(reader, start=2):
                if not row:
                    continue  # ignore blank lines
                try:
                    product_type, product_id, name, price, stock_quantity = row
                    product = ProductFactory.create(product_type, product_id, name,
                                                    float(price), int(stock_quantity),
                                                    supplier)
                except ValueError as e:
                    print(f"Skipped row {line_number} {row}: {e}")
                    continue

                if inventory.add_product(product):
                    loaded += 1
                else:
                    print(f"Skipped row {line_number}: product {product_id} "
                          f"is already in the inventory.")
        print(f"{loaded} products loaded.")
    finally:
        print("Load attempt finished.")
    return loaded
