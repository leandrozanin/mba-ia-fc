import logging
import sqlite3

from flask import Blueprint, abort, current_app, jsonify

from ..auth import usuario_autenticado
from ..constants import APP_VERSION
from ..controllers import sistema
from ..db import get_db
from ..permissoes import exigir_admin

logger = logging.getLogger(__name__)

bp = Blueprint("sistema", __name__)


@bp.get("/")
def index():
    return jsonify({
        "mensagem": "Bem-vindo à API da Loja",
        "versao": APP_VERSION,
        "endpoints": {
            "produtos": "/produtos",
            "usuarios": "/usuarios",
            "pedidos": "/pedidos",
            "login": "/login",
            "relatorios": "/relatorios/vendas",
            "health": "/health"
        }
    })


@bp.get("/health")
def health_check():
    try:
        contagens = sistema.contagens(get_db())
    except sqlite3.Error:
        logger.exception("Health check: falha ao consultar o banco")
        return jsonify({"status": "erro", "detalhes": "Banco de dados indisponível"}), 500
    return jsonify({"status": "ok", "database": "connected", "counts": contagens, "versao": APP_VERSION}), 200


@bp.post("/admin/reset-db")
def reset_database():
    # Desabilitado por padrão: sem ENABLE_ADMIN_RESET a rota responde 404, como se não existisse
    if not current_app.config["ENABLE_ADMIN_RESET"]:
        abort(404)
    exigir_admin(usuario_autenticado())
    sistema.resetar_banco(get_db())
    logger.warning("Banco de dados resetado via /admin/reset-db")
    return jsonify({"mensagem": "Banco de dados resetado", "sucesso": True}), 200
