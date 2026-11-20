from product import Product


class Inventory:

    def __init__(self) -> None:
        # Aggregation: the Inventory groups Product objects that were created
        # elsewhere. It holds references to them but does not own their lifecycle.
        self.__products: list[Product] = []

    @property
    def products(self) -> list[Product]:
        return list(self.__products)

    def add_product(self, product: Product) -> bool:
        if not isinstance(product, Product):
            raise TypeError("Only Product objects can be added.")
        if self.find_product(product.product_id) is not None:
            return False
        self.__products.append(product)
        return True

    def remove_product(self, product_id: str) -> Product | None:
        product = self.find_product(product_id)
        if product is None:
            return None
        # Only the reference is removed. The Product object itself still exists
        # and is handed back so it can be used or added to another Inventory.
        self.__products.remove(product)
        return product

    def find_product(self, product_id: str) -> Product | None:
        for product in self.__products:
            if product.product_id.lower() == product_id.strip().lower():
                return product
        return None

    def update_stock(self, product_id: str, quantity: int) -> bool:
        product = self.find_product(product_id)
        if product is None:
            return False
        product.update_stock(quantity)
        return True

    def display_all_products(self) -> None:
        print("\nCurrent Inventory")
        print("-" * 60)
        if not self.__products:
            print("No products in inventory.")
        for product in self.__products:
            product.display_information()
        print("-" * 60 + "\n")
