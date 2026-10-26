"""Camada HTTP: converte request/response e delega aos controllers."""
from flask import Blueprint, jsonify, request

from config.settings import VERSAO_API
from controllers import (
    pedido_controller,
    produto_controller,
    relatorio_controller,
    sistema_controller,
    usuario_controller,
)

bp = Blueprint("api", __name__)


def _corpo():
    return request.get_json(silent=True)


@bp.get("/")
def index():
    return jsonify({
        "mensagem": "Bem-vindo à API da Loja",
        "versao": VERSAO_API,
        "endpoints": {
            "produtos": "/produtos",
            "usuarios": "/usuarios",
            "pedidos": "/pedidos",
            "login": "/login",
            "relatorios": "/relatorios/vendas",
            "health": "/health",
        },
    })


# Produtos
@bp.get("/produtos")
def listar_produtos():
    return jsonify({"dados": produto_controller.listar(), "sucesso": True}), 200


@bp.get("/produtos/busca")
def buscar_produtos():
    resultados = produto_controller.buscar(request.args)
    return jsonify({"dados": resultados, "total": len(resultados), "sucesso": True}), 200


@bp.get("/produtos/<int:produto_id>")
def buscar_produto(produto_id):
    return jsonify({"dados": produto_controller.buscar_por_id(produto_id), "sucesso": True}), 200


@bp.post("/produtos")
def criar_produto():
    dados = produto_controller.criar(_corpo())
    return jsonify({"dados": dados, "sucesso": True, "mensagem": "Produto criado"}), 201


@bp.put("/produtos/<int:produto_id>")
def atualizar_produto(produto_id):
    produto_controller.atualizar(produto_id, _corpo())
    return jsonify({"sucesso": True, "mensagem": "Produto atualizado"}), 200


@bp.delete("/produtos/<int:produto_id>")
def deletar_produto(produto_id):
    produto_controller.deletar(produto_id)
    return jsonify({"sucesso": True, "mensagem": "Produto deletado"}), 200


# Usuários
@bp.get("/usuarios")
def listar_usuarios():
    return jsonify({"dados": usuario_controller.listar(), "sucesso": True}), 200


@bp.get("/usuarios/<int:usuario_id>")
def buscar_usuario(usuario_id):
    return jsonify({"dados": usuario_controller.buscar_por_id(usuario_id), "sucesso": True}), 200


@bp.post("/usuarios")
def criar_usuario():
    return jsonify({"dados": usuario_controller.criar(_corpo()), "sucesso": True}), 201


@bp.post("/login")
def login():
    usuario = usuario_controller.login(_corpo())
    return jsonify({"dados": usuario, "sucesso": True, "mensagem": "Login OK"}), 200


# Pedidos
@bp.post("/pedidos")
def criar_pedido():
    resultado = pedido_controller.criar(_corpo())
    return jsonify({"dados": resultado, "sucesso": True, "mensagem": "Pedido criado com sucesso"}), 201


@bp.get("/pedidos")
def listar_todos_pedidos():
    return jsonify({"dados": pedido_controller.listar_todos(), "sucesso": True}), 200


@bp.get("/pedidos/usuario/<int:usuario_id>")
def listar_pedidos_usuario(usuario_id):
    return jsonify({"dados": pedido_controller.listar_por_usuario(usuario_id), "sucesso": True}), 200


@bp.put("/pedidos/<int:pedido_id>/status")
def atualizar_status_pedido(pedido_id):
    pedido_controller.atualizar_status(pedido_id, _corpo())
    return jsonify({"sucesso": True, "mensagem": "Status atualizado"}), 200


# Relatórios e sistema
@bp.get("/relatorios/vendas")
def relatorio_vendas():
    return jsonify({"dados": relatorio_controller.relatorio_vendas(), "sucesso": True}), 200


@bp.get("/health")
def health_check():
    return jsonify(sistema_controller.health()), 200


@bp.post("/admin/reset-db")
def reset_database():
    sistema_controller.resetar_banco()
    return jsonify({"mensagem": "Banco de dados resetado", "sucesso": True}), 200

# /admin/query (SQL arbitrário vindo do cliente) foi removido intencionalmente.
