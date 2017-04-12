import enum
from utils.exceptions import InvalidTransition


class TrxDirection(enum.Enum):
    INCOMING = 0
    OUTGOING = 1


class TrxStatus(enum.Enum):
    FINALIZED = 0
    PENDING = 1
    CANCELLATION = 2

    _transitions = {
        None: (PENDING,),
        PENDING: (FINALIZED, CANCELLATION),
        FINALIZED: (CANCELLATION,)
    }

    _money_transitions = {
        TrxDirection.OUTGOING: {
            (None, PENDING): 1,
            (PENDING, FINALIZED): 0,
            (PENDING, CANCELLATION): -1,
            (FINALIZED, CANCELLATION): -1
        },
        TrxDirection.INCOMING: {
            (None, PENDING): 0,
            (PENDING, FINALIZED): 1,
            (PENDING, CANCELLATION): 0,
            (FINALIZED, CANCELLATION): -1
        }
    }


def get_direction_multiplier(enum, from_state, to_state, direction):
    if not hasattr(enum, '_money_transitions'):
        raise InvalidTransition('No money transitions found')

    transitions = enum._money_transitions.value.get(direction)
    if transitions is None:
        msg = 'No transitions found for direction: {0}'.format(direction)
        raise InvalidTransition(msg)

    from_key = from_state.value if from_state is not None else None
    to_key = to_state.value if to_state is not None else None
    return transitions.get((from_key, to_key))
