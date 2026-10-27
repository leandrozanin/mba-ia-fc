import logging

logger = logging.getLogger(__name__)


class NotificadorLog:
    """Notificador padrão: registra os eventos no log.

    Não há integração real de e-mail/SMS/push; substitua por uma implementação
    com a mesma interface e registre-a em app.extensions["notificador"].
    """

    def pedido_criado(self, pedido_id, usuario_id):
        logger.info("Evento pedido_criado: pedido=%s usuario=%s", pedido_id, usuario_id)

    def pedido_aprovado(self, pedido_id):
        logger.info("Evento pedido_aprovado: pedido=%s", pedido_id)

    def pedido_cancelado(self, pedido_id):
        logger.info("Evento pedido_cancelado: pedido=%s", pedido_id)
