import enum


class TrxType(enum.Enum):
    """Transaction types."""

    # To be used when a product gets sold.
    PURCHASE = 0

    # Transaction has been created during inventory management, i.e.
    # receiving a new product batch from a vendor.
    INVENTORY = 1

    # Sometimes, when doing a total inventory inspection, one notices
    # discrepancies between product quantity in the system and in the actual
    # inventory. This special type is used to mark a correction of the product
    # quantity.
    CORRECTION = 2
