import enum
from django.test import TestCase

from utils.exceptions import InvalidTransition
from utils.enums import validate_transition


class NoTransition(enum.Enum):
    FIRST = 0
    SECOND = 1
    THIRD = 2


class WithTransition(enum.Enum):
    FIRST = 0
    SECOND = 1
    THIRD = 2

    _transitions = {
        FIRST: (SECOND,),
        THIRD: (SECOND, FIRST)
    }


class UtilsTests(TestCase):
    def test_validate_transition_nonexisting_path(self):
        with self.assertRaises(InvalidTransition):
            validate_transition(
                enum=NoTransition,
                from_state=NoTransition.FIRST,
                to_state=NoTransition.SECOND
            )

    def test_validate_transition_invalid_path(self):
        with self.assertRaises(InvalidTransition):
            validate_transition(
                enum=WithTransition,
                from_state=WithTransition.SECOND,
                to_state=WithTransition.THIRD
            )

        with self.assertRaises(InvalidTransition):
            validate_transition(
                enum=WithTransition,
                from_state=WithTransition.FIRST,
                to_state=WithTransition.THIRD
            )

    def test_validate_transition_correct_path(self):
        ret = validate_transition(
            enum=WithTransition,
            from_state=WithTransition.FIRST,
            to_state=WithTransition.SECOND
        )
        self.assertIsNone(ret)
