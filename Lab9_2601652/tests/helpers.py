import os
import sys

# Let the tests import the project modules (product.py, order.py, ...) from
# the folder above, whichever folder the tests are started from.
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

from supplier import Supplier  # noqa: E402


def make_supplier() -> Supplier:
    return Supplier("S001", "TechSource Pte Ltd", "sales@techsource.example")
