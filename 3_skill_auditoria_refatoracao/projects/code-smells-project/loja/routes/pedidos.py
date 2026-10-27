from flask import Blueprint, current_app, g, jsonify, request

from ..auth import admin_obrigatorio, login_obrigatorio
from ..controllers import pedidos
from ..db import get_db
from ..permissoes import exigir_proprio_ou_admin

bp = Blueprint("pedidos", __name__)


def _notificador():
    return current_app.extensions["notificador"]


@bp.post("/pedidos")
@login_obrigatorio
def criar_pedido():
    resultado = pedidos.criar(get_db(), request.get_json(silent=True), g.usuario, _notificador())
    return jsonify({"dados": resultado, "sucesso": True, "mensagem": "Pedido criado com sucesso"}), 201


@bp.get("/pedidos")
@admin_obrigatorio
def listar_todos_pedidos():
    return jsonify({"dados": pedidos.listar(get_db()), "sucesso": True}), 200


@bp.get("/pedidos/usuario/<int:usuario_id>")
@login_obrigatorio
def listar_pedidos_usuario(usuario_id):
    exigir_proprio_ou_admin(g.usuario, usuario_id)
    return jsonify({"dados": pedidos.listar_do_usuario(get_db(), usuario_id), "sucesso": True}), 200


@bp.put("/pedidos/<int:pedido_id>/status")
@admin_obrigatorio
def atualizar_status_pedido(pedido_id):
    pedidos.atualizar_status(get_db(), pedido_id, request.get_json(silent=True), _notificador())
    return jsonify({"sucesso": True, "mensagem": "Status atualizado"}), 200
