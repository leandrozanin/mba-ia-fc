import logging

from sqlalchemy.exc import SQLAlchemyError

from database import db

logger = logging.getLogger(__name__)


class AppError(Exception):
    """Erro de aplicação convertido em {'error': message} com status_code."""

    status_code = 400

    def __init__(self, message):
        super().__init__(message)
        self.message = message


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


class PersistenceError(AppError):
    status_code = 500


def commit(error_message):
    """Confirma a transação atual; em falha faz rollback e levanta PersistenceError."""
    try:
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        logger.exception('Falha ao persistir: %s', error_message)
        raise PersistenceError(error_message) from None
