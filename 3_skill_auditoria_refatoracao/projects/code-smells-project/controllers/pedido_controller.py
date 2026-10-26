from controllers.validators import exigir_corpo, validar_itens_pedido
from errors import ValidationError
from models import pedido_model
from services import notification_service

STATUS_VALIDOS = ["pendente", "aprovado", "enviado", "entregue", "cancelado"]


def criar(dados):
    exigir_corpo(dados)
    usuario_id = dados.get("usuario_id")
    if not usuario_id:
        raise ValidationError("Usuario ID é obrigatório")
    quantidades = validar_itens_pedido(dados.get("itens"))

    resultado = pedido_model.criar(usuario_id, quantidades)
    notification_service.pedido_criado(resultado["pedido_id"], usuario_id)
    return resultado


def listar_todos():
    return pedido_model.listar()


def listar_por_usuario(usuario_id):
    return pedido_model.listar(usuario_id)


def atualizar_status(pedido_id, dados):
    exigir_corpo(dados)
    novo_status = dados.get("status", "")
    if novo_status not in STATUS_VALIDOS:
        raise ValidationError("Status inválido")

    pedido_model.atualizar_status(pedido_id, novo_status)
    notification_service.status_alterado(pedido_id, novo_status)
