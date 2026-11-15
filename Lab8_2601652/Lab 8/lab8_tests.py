"""Lab 8 tests: association, aggregation, composition, LSP and polymorphism.

Run with:  python lab8_tests.py
"""

from digital_product import DigitalProduct
from inventory import Inventory
from order import Order
from physical_product import PhysicalProduct
from product import Product
from supplier import Supplier


def heading(title: str) -> None:
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)


def show_product_details(product: Product) -> None:
    product.display_information()
    print(product.get_fulfilment_info())


def test_association() -> None:
    heading("Section 2 - Association: Supplier and Product")

    supplier = Supplier("S001", "TechSource Pte Ltd", "sales@techsource.example")
    laptop = PhysicalProduct("P001", "Laptop", 1200.00, 15, 2.0, supplier)
    antivirus = DigitalProduct("D001", "Antivirus Software", 49.90, 100, 350.0, supplier)

    print("Supplier on its own:")
    supplier.display_information()

    print("\nSupplier information through each Product:")
    laptop.supplier.display_information()
    antivirus.supplier.display_information()

    print("\nBoth products refer to the same Supplier object:",
          laptop.supplier is antivirus.supplier)
    print("Supplier and Product are separate objects:", supplier is not laptop)
    assert laptop.supplier is supplier and antivirus.supplier is supplier

    # Predict first: what happens after 'del supplier'?
    del supplier
    print("\nAfter 'del supplier', through each Product:")
    laptop.supplier.display_information()
    antivirus.supplier.display_information()


def test_aggregation() -> None:
    heading("Section 3 - Aggregation: Inventory and Product")

    supplier = Supplier("S001", "TechSource Pte Ltd", "sales@techsource.example")

    # The Product exists before any Inventory does.
    mouse = PhysicalProduct("P002", "Mouse", 25.50, 40, 0.1, supplier)
    inventory_a = Inventory()
    inventory_b = Inventory()

    inventory_a.add_product(mouse)
    print("Added to Inventory A. Products in A:", len(inventory_a.products))

    removed = inventory_a.remove_product("P002")
    print("Removed from Inventory A. Products in A:", len(inventory_a.products))
    print("find_product in A now returns:", inventory_a.find_product("P002"))

    # Predict first: does the Product still work after removal?
    print("\nThe Product after removal:")
    mouse.display_information()
    mouse.update_stock(35)
    print("Stock after update_stock(35):", mouse.stock)
    print("Removed object is the same Product:", removed is mouse)
    assert removed is mouse

    inventory_b.add_product(mouse)
    print("\nAdded the same Product to Inventory B. Products in B:",
          len(inventory_b.products))
    print("Product in B is the same object:", inventory_b.find_product("P002") is mouse)
    assert inventory_b.find_product("P002") is mouse


def test_composition() -> None:
    heading("Section 4 - Composition: Order and OrderLine")

    supplier = Supplier("S001", "TechSource Pte Ltd", "sales@techsource.example")
    laptop = PhysicalProduct("P001", "Laptop", 1200.00, 15, 2.0, supplier)
    antivirus = DigitalProduct("D001", "Antivirus Software", 49.90, 100, 350.0, supplier)

    order_1 = Order("O001")
    order_1.add_order_line(laptop, 2)
    order_1.add_order_line(antivirus, 3)
    order_1.display_information()
    assert abs(order_1.calculate_total() - (1200.00 * 2 + 49.90 * 3)) < 0.001

    # Predict first: same Product in two Orders.
    order_2 = Order("O002")
    order_2.add_order_line(laptop, 1)
    print()
    order_2.display_information()

    line_1 = order_1.order_lines[0]
    line_2 = order_2.order_lines[0]
    print("\nSame Product added to two Orders:")
    print("OrderLine in O001 id:", id(line_1))
    print("OrderLine in O002 id:", id(line_2))
    print("Same OrderLine object:", line_1 is line_2)
    print("Same Product object:", line_1.product is line_2.product)
    assert line_1 is not line_2 and line_1.product is line_2.product

    # The line is removed through its Order. The Product is unaffected.
    order_1.remove_order_line("P001")
    print("\nAfter removing the Laptop line from O001:")
    order_1.display_information()
    print("\nThe Product still exists:")
    laptop.display_information()


def test_lsp() -> None:
    heading("Section 6 - LSP: substitutability")

    supplier = Supplier("S001", "TechSource Pte Ltd", "sales@techsource.example")
    laptop = PhysicalProduct("P001", "Laptop", 1200.00, 15, 2.0, supplier)
    antivirus = DigitalProduct("D001", "Antivirus Software", 49.90, 100, 350.0, supplier)

    print("show_product_details() with a PhysicalProduct:")
    show_product_details(laptop)
    print("\nshow_product_details() with a DigitalProduct:")
    show_product_details(antivirus)

    inventory = Inventory()
    inventory.add_product(laptop)
    inventory.add_product(antivirus)

    # Normal Inventory operations work the same for both subclasses.
    inventory.update_stock("P001", 10)
    inventory.update_stock("D001", 90)
    print("\nStock after Inventory.update_stock():",
          inventory.find_product("P001").stock, "and",
          inventory.find_product("D001").stock)
    assert laptop.stock == 10 and antivirus.stock == 90
    inventory.display_all_products()


def test_polymorphism() -> None:
    heading("Section 7 - Polymorphism through Product")

    supplier = Supplier("S001", "TechSource Pte Ltd", "sales@techsource.example")
    inventory = Inventory()
    inventory.add_product(PhysicalProduct("P003", "Keyboard", 45.00, 25, 0.8, supplier))
    inventory.add_product(DigitalProduct("D001", "Antivirus Software", 49.90, 100, 350.0, supplier))

    # One loop, no isinstance(): each object supplies its own behaviour.
    for product in inventory.products:
        product.display_information()
        print(product.get_fulfilment_info())


if __name__ == "__main__":
    test_association()
    test_aggregation()
    test_composition()
    test_lsp()
    test_polymorphism()
    print("\nAll Lab 8 tests completed.")
