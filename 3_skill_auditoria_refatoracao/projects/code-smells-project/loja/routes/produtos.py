from flask import Blueprint, jsonify, request

from ..auth import admin_obrigatorio
from ..controllers import produtos
from ..db import get_db

bp = Blueprint("produtos", __name__)


@bp.get("/produtos")
def listar_produtos():
    return jsonify({"dados": produtos.listar(get_db()), "sucesso": True}), 200


@bp.get("/produtos/busca")
def buscar_produtos():
    resultados = produtos.pesquisar(get_db(), request.args)
    return jsonify({"dados": resultados, "total": len(resultados), "sucesso": True}), 200


@bp.get("/produtos/<int:id>")
def buscar_produto(id):
    return jsonify({"dados": produtos.buscar(get_db(), id), "sucesso": True}), 200


@bp.post("/produtos")
@admin_obrigatorio
def criar_produto():
    produto_id = produtos.criar(get_db(), request.get_json(silent=True))
    return jsonify({"dados": {"id": produto_id}, "sucesso": True, "mensagem": "Produto criado"}), 201


@bp.put("/produtos/<int:id>")
@admin_obrigatorio
def atualizar_produto(id):
    produtos.atualizar(get_db(), id, request.get_json(silent=True))
    return jsonify({"sucesso": True, "mensagem": "Produto atualizado"}), 200


@bp.delete("/produtos/<int:id>")
@admin_obrigatorio
def deletar_produto(id):
    produtos.deletar(get_db(), id)
    return jsonify({"sucesso": True, "mensagem": "Produto deletado"}), 200
