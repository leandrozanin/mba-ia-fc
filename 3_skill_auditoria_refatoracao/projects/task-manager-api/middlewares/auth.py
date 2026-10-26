from functools import wraps

from flask import g, request

from errors import ForbiddenError, UnauthorizedError
from services.auth_service import user_from_token


def load_current_user():
    """Identifica o usuário pelo header Authorization: Bearer <token>, se houver."""
    g.current_user = None
    header = request.headers.get('Authorization', '')
    if header.startswith('Bearer '):
        g.current_user = user_from_token(header.removeprefix('Bearer ').strip())


def require_auth(*roles):
    def decorator(view):
        @wraps(view)
        def wrapper(*args, **kwargs):
            user = g.get('current_user')
            if user is None:
                raise UnauthorizedError('Autenticação necessária')
            if roles and user.role not in roles:
                raise ForbiddenError('Permissão insuficiente')
            return view(*args, **kwargs)
        return wrapper
    return decorator
