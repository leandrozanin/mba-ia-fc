from .constants import TIPO_ADMIN
from .errors import ForbiddenError


def eh_admin(usuario):
    return usuario["tipo"] == TIPO_ADMIN


def exigir_admin(usuario):
    if not eh_admin(usuario):
        raise ForbiddenError("Acesso negado")


def exigir_proprio_ou_admin(usuario, usuario_id):
    if usuario["id"] != usuario_id and not eh_admin(usuario):
        raise ForbiddenError("Acesso negado")
