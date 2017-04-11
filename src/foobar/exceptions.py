class APIException(Exception):
    """General exception that may be raised by the module API."""


class NotCancelableException(APIException):
    """Raised when a purchase cannot be canceled."""
