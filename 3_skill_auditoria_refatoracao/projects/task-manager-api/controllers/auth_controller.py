import logging

from controllers.errors import AuthenticationError, ForbiddenError, ValidationError, commit
from database import db
from models.user import User

logger = logging.getLogger(__name__)


def login(data, auth_service):
    if not isinstance(data, dict) or not data:
        raise ValidationError('Dados inválidos')

    email = data.get('email')
    password = data.get('password')
    if not email or not password:
        raise ValidationError('Email e senha são obrigatórios')
    if not isinstance(email, str) or not isinstance(password, str):
        raise AuthenticationError('Credenciais inválidas')

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        raise AuthenticationError('Credenciais inválidas')
    if not user.active:
        raise ForbiddenError('Usuário inativo')

    if user.has_legacy_password():
        user.set_password(password)
        commit('Erro ao atualizar credenciais')
        logger.info('Hash de senha legado migrado: user_id=%s', user.id)

    return user, auth_service.issue_token(user)


def user_from_token(token, auth_service):
    """Usuário ativo dono do token, ou None se o token for inválido/expirado."""
    user_id = auth_service.user_id_from_token(token)
    if user_id is None:
        return None
    user = db.session.get(User, user_id)
    if not user or not user.active:
        return None
    return user
