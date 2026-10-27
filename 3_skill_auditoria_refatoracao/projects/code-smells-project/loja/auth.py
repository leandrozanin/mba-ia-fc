"""Autenticação por token assinado (itsdangerous, dependência do Flask) e autorização por papel."""
from functools import wraps

from flask import current_app, g, request
from itsdangerous import BadSignature, URLSafeTimedSerializer

from .db import get_db
from .errors import AuthenticationError
from .models import usuario as usuario_model
from .permissoes import exigir_admin

TOKEN_SALT = "loja-auth"


def _serializer():
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"], salt=TOKEN_SALT)


def gerar_token(usuario_id):
    return _serializer().dumps({"id": usuario_id})


def usuario_autenticado():
    """Usuário dono do token Bearer da requisição; levanta AuthenticationError se ausente/inválido."""
    cabecalho = request.headers.get("Authorization", "")
    esquema, _, token = cabecalho.partition(" ")
    if esquema.lower() != "bearer" or not token:
        raise AuthenticationError("Autenticação necessária")
    try:
        dados = _serializer().loads(token, max_age=current_app.config["TOKEN_MAX_AGE"])
    except BadSignature:
        raise AuthenticationError("Token inválido ou expirado") from None
    usuario = usuario_model.buscar_por_id(get_db(), dados.get("id"))
    if usuario is None:
        raise AuthenticationError("Token inválido ou expirado")
    return usuario


def login_obrigatorio(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        g.usuario = usuario_autenticado()
        return view(*args, **kwargs)
    return wrapper


def admin_obrigatorio(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        g.usuario = usuario_autenticado()
        exigir_admin(g.usuario)
        return view(*args, **kwargs)
    return wrapper
