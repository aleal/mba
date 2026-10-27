import logging
import smtplib
from email.message import EmailMessage

logger = logging.getLogger(__name__)


class NotificationService:
    """Notificações por e-mail. Desligado por padrão (só registra no log); falhas nunca derrubam a requisição."""

    def __init__(self, enabled, smtp_host, smtp_port, smtp_user, smtp_password):
        self.enabled = enabled
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password

    @classmethod
    def from_config(cls, config):
        return cls(
            enabled=config['NOTIFICATIONS_ENABLED'],
            smtp_host=config['SMTP_HOST'],
            smtp_port=config['SMTP_PORT'],
            smtp_user=config['SMTP_USER'],
            smtp_password=config['SMTP_PASSWORD'],
        )

    def notify_task_assigned(self, user, task):
        subject = f'Nova task atribuída: {task.title}'
        body = (
            f"Olá {user.name},\n\nA task '{task.title}' foi atribuída a você.\n\n"
            f'Prioridade: {task.priority}\nStatus: {task.status}'
        )
        self.send_email(user.email, subject, body)

    def send_email(self, to, subject, body):
        if not self.enabled:
            logger.info('notificação (envio desligado) para=%s assunto=%s', to, subject)
            return False
        message = EmailMessage()
        message['From'], message['To'], message['Subject'] = self.smtp_user, to, subject
        message.set_content(body)
        try:
            with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=10) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(message)
            logger.info('e-mail enviado para=%s', to)
            return True
        except (smtplib.SMTPException, OSError):
            logger.exception('falha ao enviar e-mail para=%s', to)
            return False
