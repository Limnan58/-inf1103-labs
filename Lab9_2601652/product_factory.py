from digital_product import DigitalProduct
from physical_product import PhysicalProduct
from product import Product
from supplier import Supplier


class ProductFactory:
    """Factory pattern: the one place that decides which Product class to build.

    The rest of the program asks the factory for a Product and only needs to
    know about Product, not PhysicalProduct or DigitalProduct.

    Adding a new product type still means editing create(), so the factory
    itself breaks OCP. That is an accepted trade-off for a small system: the
    change is kept in one place instead of spread across the program.
    """

    DEFAULT_WEIGHT: float = 1.0          # kg, used when no weight is given
    DEFAULT_DOWNLOAD_SIZE: float = 1.0   # MB, used when no size is given

    @staticmethod
    def create(product_type: str, product_id: str, name: str, price: float,
               stock_quantity: int, supplier: Supplier,
               weight: float | None = None,
               download_size: float | None = None) -> Product:
        kind = str(product_type).strip().lower()

        if kind == "physical":
            if weight is None:
                weight = ProductFactory.DEFAULT_WEIGHT
            return PhysicalProduct(product_id, name, price, stock_quantity,
                                   weight, supplier)
        elif kind == "digital":
            if download_size is None:
                download_size = ProductFactory.DEFAULT_DOWNLOAD_SIZE
            return DigitalProduct(product_id, name, price, stock_quantity,
                                  download_size, supplier)
        else:
            raise ValueError(f"Unknown product type: {product_type}")
