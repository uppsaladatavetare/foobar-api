import enum


class TrxType(enum.Enum):
    FINALIZED = 0
    PENDING = 1
    CANCELLATION = 2


class TrxDirection(enum.Enum):
    INCOMING = 0
    OUTGOING = 1
