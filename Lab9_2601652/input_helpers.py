def get_positive_float(prompt: str) -> float:
    """Keep asking until the user types a number greater than zero.

    Exception handling: float() raises ValueError for text like "abc".
    Validation: an if statement rejects zero and negative numbers.
    """
    while True:
        try:
            value = float(input(prompt))
            if value <= 0:
                print("Please enter a number greater than zero.")
                continue
            return value
        except ValueError:
            print("Please enter a valid number, e.g. 12.50")


def get_non_negative_int(prompt: str) -> int:
    """Keep asking until the user types a whole number of zero or more."""
    while True:
        try:
            value = int(input(prompt))
            if value < 0:
                print("Please enter zero or a positive whole number.")
                continue
            return value
        except ValueError:
            print("Please enter a whole number, e.g. 10")


def get_positive_int(prompt: str) -> int:
    """Keep asking until the user types a whole number greater than zero."""
    while True:
        try:
            value = int(input(prompt))
            if value <= 0:
                print("Please enter a whole number greater than zero.")
                continue
            return value
        except ValueError:
            print("Please enter a whole number, e.g. 2")
