from discount import DiscountStrategy, NoDiscount
from order_line import OrderLine
from product import Product


class Order:

    def __init__(self, order_id: str, discount: DiscountStrategy | None = None) -> None:
        if not str(order_id).strip():
            raise ValueError("Order ID cannot be empty.")
        self.__order_id: str = str(order_id).strip()
        # Composition: the Order creates and manages its own OrderLine objects.
        # They are never passed in from outside or moved to another Order.
        self.__order_lines: list[OrderLine] = []
        # Association (Strategy pattern): the Order uses a DiscountStrategy
        # but does not own it. The same strategy object can be shared by many
        # Orders and swapped at any time with set_discount().
        self.__discount: DiscountStrategy = NoDiscount()
        if discount is not None:
            self.set_discount(discount)

    @property
    def order_id(self) -> str:
        return self.__order_id

    @property
    def order_lines(self) -> list[OrderLine]:
        return list(self.__order_lines)

    @property
    def discount(self) -> DiscountStrategy:
        return self.__discount

    def set_discount(self, discount: DiscountStrategy) -> None:
        if not isinstance(discount, DiscountStrategy):
            raise TypeError("discount must be a DiscountStrategy object.")
        self.__discount = discount

    def add_order_line(self, product: Product, quantity: int) -> None:
        order_line = OrderLine(product, quantity)
        self.__order_lines.append(order_line)

    def remove_order_line(self, product_id: str) -> bool:
        for order_line in self.__order_lines:
            if order_line.product.product_id.lower() == product_id.strip().lower():
                self.__order_lines.remove(order_line)
                return True
        return False

    def calculate_subtotal(self) -> float:
        return sum(order_line.calculate_subtotal() for order_line in self.__order_lines)

    def calculate_total(self) -> float:
        # No if/elif about discount types: the strategy decides.
        total = self.calculate_subtotal()
        return self.__discount.apply(total)

    def display_information(self) -> None:
        print(f"Order {self.__order_id}")
        print("-" * 40)
        if not self.__order_lines:
            print("No order lines.")
        for order_line in self.__order_lines:
            order_line.display_information()
        print("-" * 40)
        print(f"Subtotal: ${self.calculate_subtotal():.2f}")
        print(f"Discount: {self.__discount}")
        print(f"Total: ${self.calculate_total():.2f}")
