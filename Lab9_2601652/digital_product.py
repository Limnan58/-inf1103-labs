from product import Product
from supplier import Supplier


class DigitalProduct(Product):
    PRODUCT_TYPE: str = "digital"

    def __init__(self, product_id: str, name: str, price: float, stock: int,
                 download_size: float, supplier: Supplier) -> None:
        super().__init__(product_id, name, price, stock, supplier)
        if float(download_size) <= 0:
            raise ValueError("Download size must be greater than 0.")
        self.__download_size: float = float(download_size)

    @property
    def download_size(self) -> float:
        return self.__download_size

    def display_information(self) -> None:
        super().display_information()
        print(f" | Download Size: {self.__download_size:.2f} MB")

    def to_dict(self) -> dict[str, object]:
        data = super().to_dict()
        data["download_size"] = self.__download_size
        return data

    def get_fulfilment_info(self) -> str:
        return f"{self.name} is a digital product and is delivered digitally via download link."
