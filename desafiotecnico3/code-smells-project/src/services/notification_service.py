import logging

from src.models.pedido_model import STATUS_APROVADO, STATUS_CANCELADO


class NotificationService:
    """Ponto único de notificações (e-mail/SMS/push). Hoje só registra em log;
    uma integração real substitui esta classe no composition root."""

    def __init__(self, logger=None):
        self.logger = logger or logging.getLogger(__name__)

    def pedido_criado(self, pedido_id, usuario_id):
        self.logger.info("notificacao pedido_criado pedido=%s usuario=%s canais=email,sms,push", pedido_id, usuario_id)

    def status_pedido_alterado(self, pedido_id, novo_status):
        if novo_status == STATUS_APROVADO:
            self.logger.info("notificacao pedido_aprovado pedido=%s acao=preparar_envio", pedido_id)
        elif novo_status == STATUS_CANCELADO:
            self.logger.info("notificacao pedido_cancelado pedido=%s", pedido_id)
