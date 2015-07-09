import enum


class TrxType(enum.Enum):
    INCOMING = 0
    OUTGOING = 1


class TrxStatus(enum.Enum):
    PENDING = 0
    FINALIZED = 1
    REJECTED = 2
    CANCELED = 3
