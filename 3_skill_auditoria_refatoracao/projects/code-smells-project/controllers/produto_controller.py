import logging

from controllers.validators import validar_faixa_preco, validar_produto
from errors import NotFoundError
from models import produto_model

logger = logging.getLogger(__name__)


def listar():
    return produto_model.listar()


def buscar_por_id(produto_id):
    produto = produto_model.buscar_por_id(produto_id)
    if produto is None:
        raise NotFoundError("Produto não encontrado", sucesso=False)
    return produto


def criar(dados):
    produto = validar_produto(dados)
    produto_id = produto_model.criar(**produto)
    logger.info("Produto criado: id=%s", produto_id)
    return {"id": produto_id}


def atualizar(produto_id, dados):
    if produto_model.buscar_por_id(produto_id) is None:
        raise NotFoundError("Produto não encontrado")
    produto_model.atualizar(produto_id, **validar_produto(dados))


def deletar(produto_id):
    if produto_model.buscar_por_id(produto_id) is None:
        raise NotFoundError("Produto não encontrado")
    produto_model.deletar(produto_id)
    logger.info("Produto deletado: id=%s", produto_id)


def buscar(filtros):
    return produto_model.buscar(
        filtros.get("q", ""),
        filtros.get("categoria") or None,
        validar_faixa_preco(filtros.get("preco_min"), "preco_min"),
        validar_faixa_preco(filtros.get("preco_max"), "preco_max"),
    )
