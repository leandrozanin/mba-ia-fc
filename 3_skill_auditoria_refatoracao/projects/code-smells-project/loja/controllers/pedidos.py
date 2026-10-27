from ..constants import STATUS_APROVADO, STATUS_CANCELADO
from ..db import transacao
from ..errors import NotFoundError, ValidationError
from ..models import pedido as pedido_model
from ..models import produto as produto_model
from ..models import usuario as usuario_model
from ..permissoes import exigir_proprio_ou_admin
from ..validators import validar_pedido, validar_status


def criar(db, dados, usuario_atual, notificador):
    dados = validar_pedido(dados)
    usuario_id = dados["usuario_id"]
    exigir_proprio_ou_admin(usuario_atual, usuario_id)
    if usuario_model.buscar_por_id(db, usuario_id) is None:
        raise ValidationError("Usuário " + str(usuario_id) + " não encontrado")

    with transacao(db):
        total = 0
        itens = []
        for item in dados["itens"]:
            produto = produto_model.buscar_por_id(db, item["produto_id"])
            if produto is None:
                raise ValidationError("Produto " + str(item["produto_id"]) + " não encontrado")
            if not produto_model.baixar_estoque(db, item["produto_id"], item["quantidade"]):
                raise ValidationError("Estoque insuficiente para " + produto["nome"])
            total = total + (produto["preco"] * item["quantidade"])
            itens.append((item["produto_id"], item["quantidade"], produto["preco"]))

        pedido_id = pedido_model.criar(db, usuario_id, total)
        for produto_id, quantidade, preco_unitario in itens:
            pedido_model.adicionar_item(db, pedido_id, produto_id, quantidade, preco_unitario)

    notificador.pedido_criado(pedido_id, usuario_id)
    return {"pedido_id": pedido_id, "total": total}


def listar(db):
    return pedido_model.listar(db)


def listar_do_usuario(db, usuario_id):
    return pedido_model.listar(db, usuario_id=usuario_id)


def atualizar_status(db, pedido_id, dados, notificador):
    novo_status = validar_status(dados)

    with transacao(db):
        pedido = pedido_model.buscar_por_id(db, pedido_id)
        if pedido is None:
            raise NotFoundError("Pedido não encontrado")
        status_atual = pedido["status"]
        if status_atual == STATUS_CANCELADO and novo_status != STATUS_CANCELADO:
            raise ValidationError("Pedido cancelado não pode mudar de status")
        if novo_status == STATUS_CANCELADO and status_atual != STATUS_CANCELADO:
            for item in pedido_model.itens_do_pedido(db, pedido_id):
                produto_model.devolver_estoque(db, item["produto_id"], item["quantidade"])
        pedido_model.atualizar_status(db, pedido_id, novo_status)

    if novo_status != status_atual:
        if novo_status == STATUS_APROVADO:
            notificador.pedido_aprovado(pedido_id)
        elif novo_status == STATUS_CANCELADO:
            notificador.pedido_cancelado(pedido_id)
