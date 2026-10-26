import logging

from flask import jsonify
from werkzeug.exceptions import HTTPException

from errors import AppError

logger = logging.getLogger(__name__)


def register_error_handlers(app):
    @app.errorhandler(AppError)
    def handle_app_error(error):
        return jsonify(error.to_dict()), error.status_code

    @app.errorhandler(HTTPException)
    def handle_http_error(error):
        return jsonify({"erro": error.description}), error.code

    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        # Detalhes ficam no log do servidor; o cliente recebe mensagem genérica.
        logger.exception("Erro inesperado")
        return jsonify({"erro": "Erro interno do servidor"}), 500
