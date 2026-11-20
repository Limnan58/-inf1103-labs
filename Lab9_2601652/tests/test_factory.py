import unittest

from tests.helpers import make_supplier

from digital_product import DigitalProduct
from physical_product import PhysicalProduct
from product import Product
from product_factory import ProductFactory


class TestProductFactory(unittest.TestCase):

    def setUp(self):
        self.supplier = make_supplier()

    def test_creates_physical_product(self):
        product = ProductFactory.create("physical", "P001", "Desk Lamp", 25.00, 10,
                                        self.supplier, weight=1.5)
        self.assertIsInstance(product, PhysicalProduct)
        self.assertIsInstance(product, Product)
        self.assertEqual(product.weight, 1.5)

    def test_creates_digital_product(self):
        product = ProductFactory.create("digital", "D001", "Photo Editor", 49.90, 100,
                                        self.supplier, download_size=500.0)
        self.assertIsInstance(product, DigitalProduct)
        self.assertEqual(product.download_size, 500.0)

    def test_type_is_case_insensitive(self):
        product = ProductFactory.create(" Physical ", "P001", "Desk Lamp", 25.00, 10,
                                        self.supplier)
        self.assertIsInstance(product, PhysicalProduct)

    def test_unknown_type_raises_clear_value_error(self):
        with self.assertRaises(ValueError) as context:
            ProductFactory.create("service", "S001", "Installation", 30.00, 5,
                                  self.supplier)
        self.assertEqual(str(context.exception), "Unknown product type: service")


if __name__ == "__main__":
    unittest.main()
