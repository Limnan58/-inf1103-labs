from product import Product
from can_be_shipped import CanBeShipped


class PhysicalProduct(Product, CanBeShipped):
    """A product that has a weight and must be shipped.

    Inherits from Product (is-a) and implements the CanBeShipped
    interface (must-be-able-to).
    """

    PRODUCT_TYPE = "physical"

    BASE_SHIPPING_FEE = 5.00   # flat fee per item ($)
    RATE_PER_KG = 2.00         # extra cost per kg ($)

    def __init__(self, product_id, name, price, stock, weight):
        super().__init__(product_id, name, price, stock)   # reuse Product's constructor
        if float(weight) <= 0:
            raise ValueError("Weight must be greater than 0.")
        self.__weight = float(weight)

    @property
    def weight(self):
        return self.__weight

    # ---------- Overridden methods ----------

    def display_information(self):
        super().display_information()          # common info from Product
        print(f" | Weight: {self.__weight:.2f} kg")

    def to_dict(self):
        data = super().to_dict()
        data["weight"] = self.__weight
        return data

    # ---------- Abstract method from Product ----------

    def get_fulfilment_info(self):
        return f"{self.name} is a physical product and requires physical shipping."

    # ---------- Interface method from CanBeShipped ----------

    def calculate_shipping_cost(self):
        """Shipping = $5 base fee + $2 per kg."""
        return self.BASE_SHIPPING_FEE + self.RATE_PER_KG * self.__weight
