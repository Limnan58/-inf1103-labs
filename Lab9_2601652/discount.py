from abc import ABC, abstractmethod


class DiscountStrategy(ABC):
    """Strategy pattern: each way of discounting an order is its own class.

    Order only calls apply(). It never needs to know which discount it has,
    so a new discount means a new class here, not a change to Order (OCP).
    """

    @abstractmethod
    def apply(self, total: float) -> float:
        pass


class NoDiscount(DiscountStrategy):

    def apply(self, total: float) -> float:
        return total

    def __str__(self) -> str:
        return "No discount"


class PercentageDiscount(DiscountStrategy):

    def __init__(self, percentage: float) -> None:
        if not 0 < percentage <= 100:
            raise ValueError("Percentage must be greater than 0 and at most 100.")
        self.__percentage: float = float(percentage)

    @property
    def percentage(self) -> float:
        return self.__percentage

    def apply(self, total: float) -> float:
        return total * (1 - self.__percentage / 100)

    def __str__(self) -> str:
        return f"{self.__percentage:g}% off"


class BulkDiscount(DiscountStrategy):

    def __init__(self, threshold: float, amount: float) -> None:
        if threshold <= 0:
            raise ValueError("Threshold must be greater than zero.")
        if amount <= 0:
            raise ValueError("Discount amount must be greater than zero.")
        self.__threshold: float = float(threshold)
        self.__amount: float = float(amount)

    @property
    def threshold(self) -> float:
        return self.__threshold

    @property
    def amount(self) -> float:
        return self.__amount

    def apply(self, total: float) -> float:
        if total >= self.__threshold:
            # Never let the discount push the total below zero.
            return max(total - self.__amount, 0.0)
        return total

    def __str__(self) -> str:
        return f"${self.__amount:.2f} off orders of ${self.__threshold:.2f} or more"
