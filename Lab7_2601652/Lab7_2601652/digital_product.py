from product import Product


class DigitalProduct(Product):
    """A product delivered by download. It has a download size, not a weight.

    It does NOT implement CanBeShipped because it is never shipped.
    """

    PRODUCT_TYPE = "digital"

    def __init__(self, product_id, name, price, stock, download_size):
        super().__init__(product_id, name, price, stock)   # reuse Product's constructor
        if float(download_size) <= 0:
            raise ValueError("Download size must be greater than 0.")
        self.__download_size = float(download_size)

    @property
    def download_size(self):
        return self.__download_size

    # ---------- Overridden methods ----------

    def display_information(self):
        super().display_information()          # common info from Product
        print(f" | Download Size: {self.__download_size:.2f} MB")

    def to_dict(self):
        data = super().to_dict()
        data["download_size"] = self.__download_size
        return data

    # ---------- Abstract method from Product ----------

    def get_fulfilment_info(self):
        return f"{self.name} is a digital product and is delivered digitally via download link."
