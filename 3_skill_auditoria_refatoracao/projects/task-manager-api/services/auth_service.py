from flask import current_app
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from database import db
from models.user import User

TOKEN_SALT = 'task-manager-auth'


def _serializer():
    return URLSafeTimedSerializer(current_app.config['SECRET_KEY'], salt=TOKEN_SALT)


def issue_token(user):
    """Token assinado com SECRET_KEY e com expiração (substitui o 'fake-jwt-token-<id>')."""
    return _serializer().dumps({'uid': user.id})


def user_from_token(token):
    try:
        payload = _serializer().loads(token, max_age=current_app.config['TOKEN_MAX_AGE_SECONDS'])
    except (BadSignature, SignatureExpired):
        return None
    user = db.session.get(User, payload.get('uid'))
    return user if user and user.active else None
