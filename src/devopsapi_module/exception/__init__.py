import logging

log: logging.Logger = logging.getLogger(__name__)

from .mail import MailBaseException
from .mail import MailPropAlreadySetException
from .mail import MailSMTPException
