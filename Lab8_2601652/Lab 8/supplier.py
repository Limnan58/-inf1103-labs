class Supplier:

    def __init__(self, supplier_id: str, name: str, contact_email: str) -> None:
        if not str(supplier_id).strip():
            raise ValueError("Supplier ID cannot be empty.")
        if not str(name).strip():
            raise ValueError("Supplier name cannot be empty.")
        if "@" not in str(contact_email):
            raise ValueError("Supplier contact email must be a valid email address.")

        self.__supplier_id: str = str(supplier_id).strip()
        self.__name: str = str(name).strip()
        self.__contact_email: str = str(contact_email).strip()

    @property
    def supplier_id(self) -> str:
        return self.__supplier_id

    @property
    def name(self) -> str:
        return self.__name

    @property
    def contact_email(self) -> str:
        return self.__contact_email

    def display_information(self) -> None:
        print(f"Supplier ID: {self.__supplier_id} | Name: {self.__name} | "
              f"Email: {self.__contact_email}")

    def to_dict(self) -> dict[str, str]:
        return {
            "id": self.__supplier_id,
            "name": self.__name,
            "contact_email": self.__contact_email,
        }
