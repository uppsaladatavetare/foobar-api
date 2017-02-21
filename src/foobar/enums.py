import enum


class PurchaseStatus(enum.Enum):
    FINALIZED = 0
    CANCELED = 1


class TrxType(enum.Enum):
    CORRECTION = 0
    DEPOSIT = 1
    WITHDRAWAL = 2
