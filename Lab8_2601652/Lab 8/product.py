from abc import ABC, abstractmethod

from supplier import Supplier


class Product(ABC):
    PRODUCT_TYPE: str | None = None

    def __init__(self, product_id: str, name: str, price: float, stock: int,
                 supplier: Supplier) -> None:
        if not str(product_id).strip():
            raise ValueError("Product ID cannot be empty.")
        if not str(name).strip():
            raise ValueError("Product name cannot be empty.")
        if float(price) < 0:
            raise ValueError("Price must be non-negative.")
        if not isinstance(supplier, Supplier):
            raise TypeError("supplier must be a Supplier object.")

        self.__product_id: str = str(product_id).strip()
        self.__name: str = str(name).strip()
        self.__price: float = float(price)
        self.__stock: int = 0
        # Association: the Product keeps a reference to a Supplier that was
        # created elsewhere. It does not create or own the Supplier.
        self.__supplier: Supplier = supplier
        self.update_stock(stock)

    @property
    def product_id(self) -> str:
        return self.__product_id

    @property
    def name(self) -> str:
        return self.__name

    @property
    def price(self) -> float:
        return self.__price

    @property
    def stock(self) -> int:
        return self.__stock

    @property
    def supplier(self) -> Supplier:
        return self.__supplier

    def update_stock(self, quantity: int) -> None:
        if isinstance(quantity, bool) or not isinstance(quantity, int):
            raise ValueError("Stock must be a whole number.")
        if quantity < 0:
            raise ValueError("Stock cannot be negative.")
        self.__stock = quantity

    def display_information(self) -> None:
        print(f"ID: {self.__product_id} | Name: {self.__name} | "
              f"Price: ${self.__price:.2f} | Stock: {self.__stock} | "
              f"Supplier: {self.__supplier.name}", end="")

    def to_dict(self) -> dict[str, object]:
        return {
            "type": self.PRODUCT_TYPE,
            "id": self.__product_id,
            "name": self.__name,
            "price": self.__price,
            "stock": self.__stock,
            "supplier": self.__supplier.to_dict(),
        }

    @abstractmethod
    def get_fulfilment_info(self) -> str:
        pass
