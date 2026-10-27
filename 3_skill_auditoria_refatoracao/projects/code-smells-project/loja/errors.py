import logging

from flask import jsonify
from werkzeug.exceptions import HTTPException

logger = logging.getLogger(__name__)


class AppError(Exception):
    status_code = 400

    def __init__(self, mensagem):
        super().__init__(mensagem)
        self.mensagem = mensagem


class ValidationError(AppError):
    status_code = 400


class AuthenticationError(AppError):
    status_code = 401


class ForbiddenError(AppError):
    status_code = 403


class NotFoundError(AppError):
    status_code = 404


class ConflictError(AppError):
    status_code = 409


def erro_json(mensagem, status):
    return jsonify({"erro": mensagem, "sucesso": False}), status


def register_error_handlers(app):
    @app.errorhandler(AppError)
    def handle_app_error(erro):
        return erro_json(erro.mensagem, erro.status_code)

    @app.errorhandler(HTTPException)
    def handle_http_error(erro):
        return erro_json(erro.description, erro.code)

    @app.errorhandler(Exception)
    def handle_unexpected(erro):
        logger.exception("Erro inesperado ao processar requisição")
        return erro_json("Erro interno do servidor", 500)
