from flask import current_app

from config.settings import VERSAO_API
from errors import ForbiddenError
from models import database, pedido_model, produto_model, usuario_model


def health():
    # Só status e contagens: nada de segredos, caminhos ou flags de debug.
    return {
        "status": "ok",
        "database": "connected",
        "counts": {
            "produtos": produto_model.contar(),
            "usuarios": usuario_model.contar(),
            "pedidos": pedido_model.contar(),
        },
        "versao": VERSAO_API,
        "ambiente": current_app.config["AMBIENTE"],
    }


def resetar_banco():
    if not current_app.config["ALLOW_DB_RESET"]:
        raise ForbiddenError("Reset do banco desabilitado neste ambiente")
    database.resetar_dados()
