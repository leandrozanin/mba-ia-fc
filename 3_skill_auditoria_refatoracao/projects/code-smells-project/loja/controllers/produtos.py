from ..errors import NotFoundError
from ..models import produto as produto_model
from ..validators import validar_busca, validar_produto


def _exigir_produto(db, produto_id):
    produto = produto_model.buscar_por_id(db, produto_id)
    if produto is None:
        raise NotFoundError("Produto não encontrado")
    return produto


def listar(db):
    return produto_model.listar(db)


def buscar(db, produto_id):
    return _exigir_produto(db, produto_id)


def pesquisar(db, args):
    return produto_model.buscar(db, **validar_busca(args))


def criar(db, dados):
    return produto_model.criar(db, **validar_produto(dados))


def atualizar(db, produto_id, dados):
    _exigir_produto(db, produto_id)
    produto_model.atualizar(db, produto_id, **validar_produto(dados))


def deletar(db, produto_id):
    _exigir_produto(db, produto_id)
    produto_model.deletar(db, produto_id)
