import logging
import smtplib

from utils.helpers import utc_now

logger = logging.getLogger(__name__)


class NotificationService:
    """Envio de e-mails; credenciais SMTP vêm da configuração (SMTP_*), nunca do código."""

    def __init__(self, host, port, user, password):
        self.notifications = []
        self.email_host = host
        self.email_port = port
        self.email_user = user
        self._email_password = password

    @classmethod
    def from_config(cls, config):
        return cls(config['SMTP_HOST'], config['SMTP_PORT'], config['SMTP_USER'], config['SMTP_PASSWORD'])

    def send_email(self, to, subject, body):
        if not (self.email_host and self.email_user and self._email_password):
            logger.warning('SMTP não configurado; e-mail não enviado')
            return False
        try:
            with smtplib.SMTP(self.email_host, self.email_port) as server:
                server.starttls()
                server.login(self.email_user, self._email_password)
                server.sendmail(self.email_user, to, f"Subject: {subject}\n\n{body}")
            logger.info('E-mail enviado')
            return True
        except (smtplib.SMTPException, OSError):
            logger.exception('Falha ao enviar e-mail')
            return False

    def notify_task_assigned(self, user, task):
        subject = f"Nova task atribuída: {task.title}"
        body = f"Olá {user.name},\n\nA task '{task.title}' foi atribuída a você.\n\nPrioridade: {task.priority}\nStatus: {task.status}"
        sent = self.send_email(user.email, subject, body)
        self.notifications.append({
            'type': 'task_assigned',
            'user_id': user.id,
            'task_id': task.id,
            'sent': sent,
            'timestamp': utc_now(),
        })
        return sent

    def notify_task_overdue(self, user, task):
        subject = f"Task atrasada: {task.title}"
        body = f"Olá {user.name},\n\nA task '{task.title}' está atrasada!\n\nData limite: {task.due_date}"
        return self.send_email(user.email, subject, body)

    def get_notifications(self, user_id):
        return [n for n in self.notifications if n['user_id'] == user_id]
