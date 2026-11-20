import unittest

from tests.helpers import make_supplier

from order import Order
from order_line import OrderLine
from product_factory import ProductFactory


class TestValidation(unittest.TestCase):

    def setUp(self):
        self.supplier = make_supplier()
        self.lamp = ProductFactory.create("physical", "P001", "Desk Lamp", 25.00, 10,
                                          self.supplier)

    def test_price_must_be_greater_than_zero(self):
        for bad_price in (0, -5):
            with self.subTest(price=bad_price):
                with self.assertRaises(ValueError) as context:
                    ProductFactory.create("physical", "P002", "Chair", bad_price, 3,
                                          self.supplier)
                self.assertIn("greater than zero", str(context.exception))

    def test_price_must_be_a_number(self):
        with self.assertRaises(ValueError):
            ProductFactory.create("physical", "P002", "Chair", "abc", 3, self.supplier)

    def test_stock_cannot_be_negative(self):
        with self.assertRaises(ValueError):
            ProductFactory.create("physical", "P002", "Chair", 10.0, -1, self.supplier)
        with self.assertRaises(ValueError):
            self.lamp.update_stock(-1)

    def test_digital_product_keeps_the_stock_rule(self):
        # LSP: the subclass must not weaken the rule it inherits.
        with self.assertRaises(ValueError):
            ProductFactory.create("digital", "D001", "Editor", 10.0, -1, self.supplier)

    def test_order_line_quantity_must_be_greater_than_zero(self):
        for bad_quantity in (0, -2):
            with self.subTest(quantity=bad_quantity):
                with self.assertRaises(ValueError):
                    OrderLine(self.lamp, bad_quantity)
                with self.assertRaises(ValueError):
                    Order("O001").add_order_line(self.lamp, bad_quantity)


if __name__ == "__main__":
    unittest.main()
