from utils.exceptions import InvalidTransition


def validate_transition(enum, from_state, to_state):
    if not hasattr(enum, '_transitions'):
        raise InvalidTransition('No transitions found')

    transitions = enum._transitions.value
    from_value = from_state.value if from_state is not None else None
    if to_state.value not in transitions.get(from_value, []):
        msg = 'Transition {0} -> {1} not allowed'.format(from_state, to_state)
        raise InvalidTransition(msg)
