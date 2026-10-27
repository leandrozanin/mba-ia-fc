from flask import Blueprint, g, jsonify, request

from ..auth import admin_obrigatorio, gerar_token, login_obrigatorio
from ..controllers import usuarios
from ..db import get_db
from ..permissoes import exigir_proprio_ou_admin

bp = Blueprint("usuarios", __name__)


@bp.get("/usuarios")
@admin_obrigatorio
def listar_usuarios():
    return jsonify({"dados": usuarios.listar(get_db()), "sucesso": True}), 200


@bp.get("/usuarios/<int:id>")
@login_obrigatorio
def buscar_usuario(id):
    exigir_proprio_ou_admin(g.usuario, id)
    return jsonify({"dados": usuarios.buscar(get_db(), id), "sucesso": True}), 200


@bp.post("/usuarios")
def criar_usuario():
    usuario_id = usuarios.criar(get_db(), request.get_json(silent=True))
    return jsonify({"dados": {"id": usuario_id}, "sucesso": True}), 201


@bp.post("/login")
def login():
    usuario = usuarios.autenticar(get_db(), request.get_json(silent=True))
    return jsonify({
        "dados": usuario,
        "token": gerar_token(usuario["id"]),
        "sucesso": True,
        "mensagem": "Login OK",
    }), 200
