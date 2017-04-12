import enum


class PurchaseStatus(enum.Enum):
    FINALIZED = 0
    CANCELED = 1
    PENDING = 2

    _transitions = {
        FINALIZED: (CANCELED,),
        PENDING: (FINALIZED, CANCELED)
    }

    @classmethod
    def members(cls):
        return [k for k in cls.__members__ if not k.startswith('_')]


class TrxType(enum.Enum):
    CORRECTION = 0
    DEPOSIT = 1
    WITHDRAWAL = 2
