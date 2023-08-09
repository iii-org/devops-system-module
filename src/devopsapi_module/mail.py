import logging
import smtplib
from email.message import EmailMessage
from typing import Optional, Union

from devopsapi_module.exception import MailPropAlreadySetException, MailSMTPException
from exception import MailBaseException

log: logging.Logger = logging.getLogger(__name__)


class MailSender:
    def __init__(self, account: str, password: str):
        """
        Initialize sender account and password.

        Args:
            account: The email account of the sender.
            password: The password of the sender account.
        """
        self.account: Optional[str] = account
        self.password: Optional[str] = password


class MailServer(smtplib.SMTP):
    def __init__(self, domain: str, port: int = 587, timeout: int = 3):
        """
        Initialize SMTP server connection.

        Args:
            domain: The domain name of the SMTP server.
            port: The port number of the SMTP server, default is 587.
            timeout: The timeout value of the SMTP server connection, default is 3 seconds.
        """
        self.domain: Optional[str] = domain
        self.port: Optional[int] = port
        self.timeout: Optional[int] = timeout

        try:
            super().__init__(domain, port, timeout=timeout)
            self.starttls()  # For most SMTP servers are TLS enabled

        except Exception as e:
            raise MailSMTPException(f"Connection failed. Reason: {e}")


class MailContent(EmailMessage):
    def __init__(self):
        """
        Initialize email content, inherited from EmailMessage.
        """
        super().__init__()

    def set_subject(self, subject: str) -> None:
        """
        Set the subject of the email.

        Args:
            subject: The subject of the email.

        Returns:
            None
        """
        if self["Subject"] is not None:
            raise MailPropAlreadySetException("Subject")

        self["Subject"] = subject

    def set_from(self, sender: str) -> None:
        """
        Set the sender of the email.

        Args:
            sender: The sender of the email, only accept one sender.

        Returns:
            None
        """
        if self["From"] is not None:
            raise MailPropAlreadySetException("From")

        self["From"] = sender

    def set_disposition_notification_to(self, recipients: Union[str, list[str]]) -> None:
        """
        Set the Disposition-Notification-To header field.

        Args:
            recipients: Recipient(s) of the disposition notification.

        Returns:
            None
        """
        if self["Disposition-Notification-To"] is not None:
            raise MailPropAlreadySetException("Disposition-Notification-To")

        if isinstance(recipients, str):
            self["Disposition-Notification-To"] = recipients

        if isinstance(recipients, list):
            self["Disposition-Notification-To"] = ", ".join(recipients)

    def set_recipient(self, recipients: Union[str, list[str]]) -> None:
        """
        Set the recipient(s) of the email.

        Args:
            recipients: Recipient(s) of the email.

        Returns:
            None
        """
        if self["To"] is not None:
            raise MailPropAlreadySetException("To")

        if isinstance(recipients, str):
            self["To"] = recipients

        if isinstance(recipients, list):
            self["To"] = ", ".join(recipients)

    def set_cc(self, recipients: Union[str, list[str]]) -> None:
        """
        Set the CC of the email.

        Args:
            recipients: Recipient(s) of the CC.

        Returns:
            None
        """
        if self["Cc"] is not None:
            raise MailPropAlreadySetException("Cc")

        if isinstance(recipients, str):
            self["Cc"] = recipients

        if isinstance(recipients, list):
            self["Cc"] = ", ".join(recipients)

    def set_bcc(self, recipients: Union[str, list[str]]) -> None:
        """
        Set the BCC of the email.

        Args:
            recipients: Recipient(s) of the BCC.

        Returns:
            None
        """
        if self["Bcc"] is not None:
            raise MailPropAlreadySetException("Bcc")

        if isinstance(recipients, str):
            self["Bcc"] = recipients

        if isinstance(recipients, list):
            self["Bcc"] = ", ".join(recipients)


class MailClient:
    def __init__(self):
        """
        Initialize SMTP server and sender, use to send email.
        """
        self._is_logged_in: bool = False
        self._smtp_server: Optional[MailServer] = None
        self._sender: Optional[MailSender] = None

    @property
    def smtp_server(self) -> MailServer:
        return self._smtp_server

    @smtp_server.setter
    def smtp_server(self, value: MailServer) -> None:
        if not isinstance(value, smtplib.SMTP):
            raise TypeError("SMTP server must be a MailSMTP object.")
        self._smtp_server = value

    @property
    def sender(self) -> MailSender:
        return self._sender

    @sender.setter
    def sender(self, value: MailSender) -> None:
        if not isinstance(value, MailSender):
            raise TypeError("Sender must be a MailSender object.")
        self._sender = value

    def login(self) -> None:
        """
        Login to the SMTP server. If the SMTP server is already logged in, raise an exception.

        Returns:
            None
        """
        if self._is_logged_in:
            raise MailSMTPException("Already logged in.")

        # Check if SMTP server and sender are set
        if any(_ is None for _ in [self.smtp_server, self.sender]):
            raise MailSMTPException("SMTP server and sender must be set.")

        if hasattr(self.smtp_server, "user"):
            # Skip login if SMTP server already logged in
            self._is_logged_in = True
            return

        try:
            self.smtp_server.login(self.sender.account, self.sender.password)
            self._is_logged_in = True

        except smtplib.SMTPAuthenticationError as e:
            if self.sender.account.endswith("gmail.com"):
                raise MailBaseException(
                    error_code=500,
                    detail="Gmail server authentication failed. App password required.",
                )

            raise MailSMTPException(f"SMTP server authentication failed. Reason: {e}")

        except Exception as e:
            raise MailSMTPException(f"SMTP server login failed. Reason: {e}")

    def send(
        self,
        subject: str,
        content: MailContent,
        receiver: Union[str, list[str]] = None,
        cc: Union[str, list[str]] = None,
        bcc: Optional[Union[str, list[str]]] = None,
        disposition_notification_to: Optional[Union[str, list[str]]] = None,
    ) -> None:
        """
        Send the email.

        Args:
            subject: The email subject.
            content: The email content.
            receiver: The email receiver(s).
            cc: The email CC.
            bcc: The email BCC.
            disposition_notification_to: Which email address to send the disposition notification to.

        Returns:
            None
        """
        if self.smtp_server is None:
            raise MailSMTPException("SMTP server not initialized.")

        if not self._is_logged_in:
            self.login()

        if not receiver and not cc and not bcc:
            raise MailBaseException(error_code=500, detail="Receiver not specified.")

        content.set_from(self.sender.account)
        content.set_disposition_notification_to(disposition_notification_to)
        content.set_subject(subject)
        content.set_recipient(receiver)
        content.set_cc(cc)
        content.set_bcc(bcc)

        all_receivers: list[str] = []

        if receiver:
            if isinstance(receiver, str):
                receiver = [receiver]
            all_receivers.extend(receiver)

        if cc:
            if isinstance(cc, str):
                cc = [cc]
            all_receivers.extend(cc)

        if bcc:
            if isinstance(bcc, str):
                bcc = [bcc]
            all_receivers.extend(bcc)

        log.info(f"Sending mail to {all_receivers}, title: {subject}")

        try:
            self.smtp_server.send_message(content, to_addrs=all_receivers)

        except Exception as e:
            log.exception(str(e))
            raise MailBaseException(error_code=500, detail=f"Sending mail failed, reason: {str(e)}")

        self.smtp_server.quit()
        log.info("Sending mail done.")


def send_mail(subject: str, message: str, email: str):
    mail_client: MailClient = MailClient()
    mail_client.smtp_server = MailServer("smtp.gmail.com", 587)
    mail_client.sender = MailSender("example@example.com", "password")

    mail_body: MailContent = MailContent()
    mail_body.set_content(message)

    mail_client.send(
        subject,
        mail_body,
        receiver=email,
        cc="some-cc@example.com",
        bcc="noshow@example.com",
    )
