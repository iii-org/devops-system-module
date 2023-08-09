import logging

log: logging.Logger = logging.getLogger(__name__)


class BaseException(Exception):
    """
    BaseException class that represents an error occurring in a specific module.

    Attributes:
        module (str): The name of the module where the error occurred.
        message (str): The error message.
    """

    def __init__(self, error_code: int, detail: str) -> None:
        """
        Initialize the exception.

        Args:
            error_code:
            detail:
        """
        self.error_code = error_code
        self.detail = detail

    def __repr__(self):
        class_name = self.__class__.__name__
        return f"{class_name}(error_code={self.error_code!r}, detail={self.detail!r})"
