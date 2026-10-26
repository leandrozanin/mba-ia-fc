import logging

from controllers.validators import EMAIL_REGEX, exigir_corpo, texto_obrigatorio
from errors import ConflictError, NotFoundError, UnauthorizedError, ValidationError
from models import usuario_model

logger = logging.getLogger(__name__)


def listar():
    return usuario_model.listar()


def buscar_por_id(usuario_id):
    usuario = usuario_model.buscar_por_id(usuario_id)
    if usuario is None:
        raise NotFoundError("Usuário não encontrado")
    return usuario


def criar(dados):
    exigir_corpo(dados)
    valores = texto_obrigatorio(dados, "nome", "email", "senha")
    if valores is None:
        raise ValidationError("Nome, email e senha são obrigatórios")
    nome, email, senha = valores
    if not EMAIL_REGEX.match(email):
        raise ValidationError("Email inválido")
    if usuario_model.email_existe(email):
        raise ConflictError("Email já cadastrado")

    usuario_id = usuario_model.criar(nome, email, senha)
    logger.info("Usuário criado: id=%s", usuario_id)
    return {"id": usuario_id}


def login(dados):
    exigir_corpo(dados)
    valores = texto_obrigatorio(dados, "email", "senha")
    if valores is None:
        raise ValidationError("Email e senha são obrigatórios")

    usuario = usuario_model.autenticar(*valores)
    if usuario is None:
        logger.info("Tentativa de login recusada")
        raise UnauthorizedError("Email ou senha inválidos", sucesso=False)
    return usuario
