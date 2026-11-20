import inspect
import unittest

from tests.helpers import make_supplier

from discount import (BulkDiscount, DiscountStrategy, NoDiscount,
                      PercentageDiscount, StudentDiscount)
from order import Order
from product_factory import ProductFactory


def order_totalling_250() -> Order:
    supplier = make_supplier()
    lamp = ProductFactory.create("physical", "P001", "Desk Lamp", 25.00, 10, supplier)
    order = Order("O001")
    order.add_order_line(lamp, 10)  # 10 x 25.00 = 250.00
    return order


class TestDiscountStrategies(unittest.TestCase):

    def test_no_discount_returns_total_unchanged(self):
        self.assertEqual(NoDiscount().apply(250.0), 250.0)

    def test_percentage_discount(self):
        self.assertAlmostEqual(PercentageDiscount(10).apply(250.0), 225.0)

    def test_bulk_discount_at_or_above_threshold(self):
        self.assertAlmostEqual(BulkDiscount(200, 20).apply(250.0), 230.0)
        self.assertAlmostEqual(BulkDiscount(200, 20).apply(200.0), 180.0)

    def test_bulk_discount_below_threshold(self):
        self.assertAlmostEqual(BulkDiscount(200, 20).apply(199.99), 199.99)

    def test_student_discount(self):
        self.assertAlmostEqual(StudentDiscount().apply(100.0), 95.0)

    def test_invalid_percentage_rejected(self):
        with self.assertRaises(ValueError):
            PercentageDiscount(0)
        with self.assertRaises(ValueError):
            PercentageDiscount(150)

    def test_strategy_base_class_is_abstract(self):
        with self.assertRaises(TypeError):
            DiscountStrategy()


class TestOrderUsesStrategy(unittest.TestCase):

    def test_order_defaults_to_no_discount(self):
        order = order_totalling_250()
        self.assertIsInstance(order.discount, NoDiscount)
        self.assertAlmostEqual(order.calculate_total(), 250.0)

    def test_order_with_bulk_then_percentage(self):
        # Predict first from Section 2.3: 230.00, then 225.00.
        order = order_totalling_250()
        order.set_discount(BulkDiscount(200, 20))
        self.assertAlmostEqual(order.calculate_total(), 230.0)
        order.set_discount(PercentageDiscount(10))
        self.assertAlmostEqual(order.calculate_total(), 225.0)

    def test_new_strategy_works_without_changing_order(self):
        class HalfPrice(DiscountStrategy):
            def apply(self, total: float) -> float:
                return total / 2

        order = order_totalling_250()
        order.set_discount(HalfPrice())
        self.assertAlmostEqual(order.calculate_total(), 125.0)

    def test_two_orders_can_share_one_strategy(self):
        shared = PercentageDiscount(10)
        first, second = order_totalling_250(), order_totalling_250()
        first.set_discount(shared)
        second.set_discount(shared)
        self.assertIs(first.discount, second.discount)

    def test_set_discount_rejects_non_strategy(self):
        with self.assertRaises(TypeError):
            order_totalling_250().set_discount("bulk")

    def test_order_has_no_discount_if_elif(self):
        def code_only(obj) -> str:
            # The source without comments, so a comment cannot fail the test.
            lines = inspect.getsource(obj).splitlines()
            return "\n".join(line.split("#")[0] for line in lines)

        for word in ("elif", "PercentageDiscount", "BulkDiscount", "StudentDiscount"):
            self.assertNotIn(word, code_only(Order))
        self.assertNotIn("if ", code_only(Order.calculate_total))


if __name__ == "__main__":
    unittest.main()
