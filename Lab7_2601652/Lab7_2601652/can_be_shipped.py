from abc import ABC, abstractmethod


class CanBeShipped(ABC):
    """Interface-style abstract base class.

    A contract for anything that 'must be able to' be shipped.
    It holds no attributes and no implementation - any class that
    implements it must provide calculate_shipping_cost().
    """

    @abstractmethod
    def calculate_shipping_cost(self):
        """Return the shipping cost for this item."""
        pass
