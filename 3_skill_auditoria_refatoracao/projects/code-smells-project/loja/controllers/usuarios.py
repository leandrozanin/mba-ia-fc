import sqlite3

from werkzeug.security import check_password_hash, generate_password_hash

from ..errors import AuthenticationError, ConflictError, NotFoundError
from ..models import usuario as usuario_model
from ..validators import validar_login, validar_usuario


def listar(db):
    return usuario_model.listar(db)


def buscar(db, usuario_id):
    usuario = usuario_model.buscar_por_id(db, usuario_id)
    if usuario is None:
        raise NotFoundError("Usuário não encontrado")
    return usuario


def criar(db, dados):
    dados = validar_usuario(dados)
    if usuario_model.email_existe(db, dados["email"]):
        raise ConflictError("Email já cadastrado")
    try:
        return usuario_model.criar(db, dados["nome"], dados["email"], generate_password_hash(dados["senha"]))
    except sqlite3.IntegrityError:
        # corrida entre a checagem e o INSERT, barrada pelo índice único
        raise ConflictError("Email já cadastrado") from None


def autenticar(db, dados):
    """Retorna os dados públicos do usuário ou levanta AuthenticationError."""
    dados = validar_login(dados)
    credenciais = usuario_model.buscar_credenciais_por_email(db, dados["email"])
    if credenciais is None or not check_password_hash(credenciais["senha"] or "", dados["senha"]):
        raise AuthenticationError("Email ou senha inválidos")
    return {campo: credenciais[campo] for campo in ("id", "nome", "email", "tipo")}
