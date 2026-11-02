from product import Product


class Inventory:
    """Manages a collection of Product objects.

    Single responsibility: store, add, search and display products.
    It does NOT read/write files or talk to the user.
    """

    def __init__(self):
        self.__products = []

    def add_product(self, product):
        """Add a Product. Returns False if the ID already exists."""
        if not isinstance(product, Product):
            raise TypeError("Only Product objects can be added.")
        if self.search_product(product.product_id) is not None:
            return False
        self.__products.append(product)
        return True

    def search_product(self, product_id):
        """Return the Product with this ID (case-insensitive), or None."""
        for product in self.__products:
            if product.product_id.lower() == product_id.strip().lower():
                return product
        return None

    def update_stock(self, product_id, quantity):
        """Ask the matching Product to update its own stock."""
        product = self.search_product(product_id)
        if product is None:
            return False
        product.update_stock(quantity)
        return True

    def display_all(self):
        print("\nCurrent Inventory")
        print("-" * 60)
        if not self.__products:
            print("No products in inventory.")
        for product in self.__products:
            product.display_information()
        print("-" * 60 + "\n")

    def get_products(self):
        """Return a copy of the list so outside code can't replace it."""
        return list(self.__products)
