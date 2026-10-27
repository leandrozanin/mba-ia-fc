from functools import wraps

from flask import current_app, g, request

from controllers.auth_controller import user_from_token
from controllers.errors import AuthenticationError, ForbiddenError


def _bearer_token():
    scheme, _, token = request.headers.get('Authorization', '').partition(' ')
    if scheme.lower() != 'bearer' or not token.strip():
        return None
    return token.strip()


def current_user_or_none():
    token = _bearer_token()
    if not token:
        return None
    return user_from_token(token, current_app.extensions['auth_service'])


def login_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if not _bearer_token():
            raise AuthenticationError('Autenticação necessária')
        user = current_user_or_none()
        if not user:
            raise AuthenticationError('Token inválido ou expirado')
        g.current_user = user
        return view(*args, **kwargs)
    return wrapper


def admin_required(view):
    @login_required
    @wraps(view)
    def wrapper(*args, **kwargs):
        if not g.current_user.is_admin():
            raise ForbiddenError('Acesso negado')
        return view(*args, **kwargs)
    return wrapper
