class Product:
    """Represents a single product and manages its own state.

    Single responsibility: store one product's information and control
    how that information (e.g. stock) is changed.
    """

    def __init__(self, product_id, name, price, stock):
        if not str(product_id).strip():
            raise ValueError("Product ID cannot be empty.")
        if not str(name).strip():
            raise ValueError("Product name cannot be empty.")
        if float(price) < 0:
            raise ValueError("Price must be non-negative.")

        # Private attributes (name-mangled) - change them only through methods
        self.__product_id = str(product_id).strip()
        self.__name = str(name).strip()
        self.__price = float(price)
        self.__stock = 0
        self.update_stock(stock)   # reuse the same validation rules

    # ---------- Read-only access (getters) ----------

    @property
    def product_id(self):
        return self.__product_id

    @property
    def name(self):
        return self.__name

    @property
    def price(self):
        return self.__price

    @property
    def stock(self):
        return self.__stock

    # ---------- Behaviour ----------

    def update_stock(self, quantity):
        """Set the stock to a new quantity. The Product decides what is valid."""
        if isinstance(quantity, bool) or not isinstance(quantity, int):
            raise ValueError("Stock must be a whole number.")
        if quantity < 0:
            raise ValueError("Stock cannot be negative.")
        self.__stock = quantity

    def display_information(self):
        print(f"ID: {self.__product_id} | Name: {self.__name} | "
              f"Price: ${self.__price:.2f} | Stock: {self.__stock}")
