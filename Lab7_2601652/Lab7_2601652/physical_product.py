from product import Product
from can_be_shipped import CanBeShipped


class PhysicalProduct(Product, CanBeShipped):
    PRODUCT_TYPE = "physical"

    BASE_SHIPPING_FEE = 5.00
    RATE_PER_KG = 2.00

    def __init__(self, product_id, name, price, stock, weight):
        super().__init__(product_id, name, price, stock)
        if float(weight) <= 0:
            raise ValueError("Weight must be greater than 0.")
        self.__weight = float(weight)

    @property
    def weight(self):
        return self.__weight

    def display_information(self):
        super().display_information()
        print(f" | Weight: {self.__weight:.2f} kg")

    def to_dict(self):
        data = super().to_dict()
        data["weight"] = self.__weight
        return data

    def get_fulfilment_info(self):
        return f"{self.name} is a physical product and requires physical shipping."

    def calculate_shipping_cost(self):
        return self.BASE_SHIPPING_FEE + self.RATE_PER_KG * self.__weight
