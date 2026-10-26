import logging

logger = logging.getLogger(__name__)


def pedido_criado(pedido_id, usuario_id):
    # Ponto único de integração com e-mail/SMS/push; hoje apenas registra o evento.
    logger.info("Notificação: pedido %s criado para usuário %s", pedido_id, usuario_id)


def status_alterado(pedido_id, novo_status):
    logger.info("Notificação: pedido %s mudou para %s", pedido_id, novo_status)
