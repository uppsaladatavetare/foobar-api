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


class TrxStatus(enum.Enum):
    FINALIZED = 0
    CANCELED = 1
    PENDING = 2

    _transitions = {
        FINALIZED: (CANCELED,),
        PENDING: (FINALIZED, CANCELED)
    }


class Weekdays(enum.Enum):
    MONDAY = 0
    TUESDAY = 1
    WEDNESDAY = 2
    THURSDAY = 3
    FRIDAY = 4
    SATURDAY = 5
    SUNDAY = 6

    @classmethod
    def choices(cls):
        return [(x.value, x.name) for x in cls]
