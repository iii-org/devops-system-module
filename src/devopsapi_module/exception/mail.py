import logging

from .base import BaseException

log: logging.Logger = logging.getLogger(__name__)


class MailBaseException(BaseException):
    pass


class MailPropAlreadySetException(MailBaseException):
    def __init__(self, property_name: str) -> None:
        super().__init__(500, f"Property {property_name} already set.")


class MailSMTPException(MailBaseException):
    def __init__(self, detail: str) -> None:
        super().__init__(500, detail)
