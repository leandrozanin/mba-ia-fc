import logging
import smtplib
from email.message import EmailMessage

logger = logging.getLogger(__name__)


class NotificationService:
    """Envio de e-mails; credenciais vêm da configuração, nunca do código."""

    def __init__(self, host=None, port=587, user=None, password=None):
        self.host = host
        self.port = port
        self.user = user
        self.password = password

    @classmethod
    def from_config(cls, config):
        return cls(config['SMTP_HOST'], config['SMTP_PORT'], config['SMTP_USER'], config['SMTP_PASSWORD'])

    @property
    def enabled(self):
        return bool(self.host and self.user and self.password)

    def send_email(self, to, subject, body):
        if not self.enabled:
            logger.debug('SMTP não configurado; e-mail "%s" não enviado.', subject)
            return False
        message = EmailMessage()
        message['From'], message['To'], message['Subject'] = self.user, to, subject
        message.set_content(body)
        try:
            with smtplib.SMTP(self.host, self.port, timeout=10) as server:
                server.starttls()
                server.login(self.user, self.password)
                server.send_message(message)
            return True
        except (smtplib.SMTPException, OSError):
            logger.exception('Falha ao enviar e-mail')
            return False

    def notify_task_assigned(self, user, task):
        subject = f'Nova task atribuída: {task.title}'
        body = (
            f"Olá {user.name},\n\nA task '{task.title}' foi atribuída a você.\n\n"
            f'Prioridade: {task.priority}\nStatus: {task.status}'
        )
        return self.send_email(user.email, subject, body)
