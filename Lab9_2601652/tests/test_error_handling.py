import io
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from tests.helpers import PROJECT_DIR, make_supplier

from input_helpers import get_positive_float
from inventory import Inventory
from product_loader import load_products

PRODUCTS_CSV = os.path.join(PROJECT_DIR, "products.csv")


class TestGetPositiveFloat(unittest.TestCase):

    def test_keeps_asking_until_valid(self):
        # Predict first from Section 5.1: abc, then -5, then 12.50.
        output = io.StringIO()
        with patch("builtins.input", side_effect=["abc", "-5", "12.50"]):
            with redirect_stdout(output):
                value = get_positive_float("Price: ")
        self.assertEqual(value, 12.5)
        self.assertEqual(output.getvalue().splitlines(), [
            "Please enter a valid number, e.g. 12.50",
            "Please enter a number greater than zero.",
        ])


class TestLoadProducts(unittest.TestCase):

    def run_loader(self, path):
        inventory = Inventory()
        output = io.StringIO()
        with redirect_stdout(output):
            loaded = load_products(path, inventory, make_supplier())
        return loaded, inventory, output.getvalue()

    def test_valid_rows_load_and_bad_rows_are_skipped(self):
        loaded, inventory, output = self.run_loader(PRODUCTS_CSV)
        self.assertEqual(loaded, 3)
        self.assertEqual([p.product_id for p in inventory.products],
                         ["P001", "D001", "P003"])
        self.assertIn("Unknown product type: service", output)
        self.assertIn("Office Chair", output)
        self.assertIn("3 products loaded.", output)
        self.assertTrue(output.rstrip().endswith("Load attempt finished."))

    def test_missing_file_is_handled_gracefully(self):
        missing = os.path.join(tempfile.gettempdir(), "no_such_products_file.csv")
        loaded, inventory, output = self.run_loader(missing)
        self.assertEqual(loaded, 0)
        self.assertEqual(inventory.products, [])
        self.assertIn("Products file not found", output)
        self.assertNotIn("products loaded", output)   # else block skipped
        self.assertIn("Load attempt finished.", output)  # finally still runs


if __name__ == "__main__":
    unittest.main()
