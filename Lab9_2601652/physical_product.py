from product import Product
from can_be_shipped import CanBeShipped
from supplier import Supplier


class PhysicalProduct(Product, CanBeShipped):
    PRODUCT_TYPE: str = "physical"

    BASE_SHIPPING_FEE: float = 5.00
    RATE_PER_KG: float = 2.00

    def __init__(self, product_id: str, name: str, price: float, stock: int,
                 weight: float, supplier: Supplier) -> None:
        super().__init__(product_id, name, price, stock, supplier)
        if float(weight) <= 0:
            raise ValueError("Weight must be greater than 0.")
        self.__weight: float = float(weight)

    @property
    def weight(self) -> float:
        return self.__weight

    def display_information(self) -> None:
        super().display_information()
        print(f" | Weight: {self.__weight:.2f} kg")

    def to_dict(self) -> dict[str, object]:
        data = super().to_dict()
        data["weight"] = self.__weight
        return data

    def get_fulfilment_info(self) -> str:
        return f"{self.name} is a physical product and requires physical shipping."

    def calculate_shipping_cost(self) -> float:
        return self.BASE_SHIPPING_FEE + self.RATE_PER_KG * self.__weight
