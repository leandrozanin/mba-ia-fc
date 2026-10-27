"""Validação de entrada na fronteira HTTP. Cada função devolve os dados normalizados ou levanta ValidationError."""
import re

from .constants import (
    CATEGORIA_PADRAO,
    CATEGORIAS_VALIDAS,
    NOME_PRODUTO_MAX,
    NOME_PRODUTO_MIN,
    STATUS_PEDIDO_VALIDOS,
)
from .errors import ValidationError

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _numero(valor):
    return isinstance(valor, (int, float)) and not isinstance(valor, bool)


def _inteiro(valor):
    return isinstance(valor, int) and not isinstance(valor, bool)


def _texto_preenchido(valor):
    return isinstance(valor, str) and valor.strip() != ""


def validar_produto(dados):
    if not isinstance(dados, dict) or not dados:
        raise ValidationError("Dados inválidos")
    for campo, mensagem in (("nome", "Nome é obrigatório"), ("preco", "Preço é obrigatório"), ("estoque", "Estoque é obrigatório")):
        if campo not in dados:
            raise ValidationError(mensagem)

    nome = dados["nome"]
    preco = dados["preco"]
    estoque = dados["estoque"]
    descricao = dados.get("descricao") or ""
    categoria = dados.get("categoria") or CATEGORIA_PADRAO

    if not isinstance(nome, str):
        raise ValidationError("Nome deve ser texto")
    if not isinstance(descricao, str):
        raise ValidationError("Descrição deve ser texto")
    if not _numero(preco):
        raise ValidationError("Preço deve ser numérico")
    if not _inteiro(estoque):
        raise ValidationError("Estoque deve ser um número inteiro")
    if preco < 0:
        raise ValidationError("Preço não pode ser negativo")
    if estoque < 0:
        raise ValidationError("Estoque não pode ser negativo")
    nome = nome.strip()
    if len(nome) < NOME_PRODUTO_MIN:
        raise ValidationError("Nome muito curto")
    if len(nome) > NOME_PRODUTO_MAX:
        raise ValidationError("Nome muito longo")
    if categoria not in CATEGORIAS_VALIDAS:
        raise ValidationError("Categoria inválida. Válidas: " + str(CATEGORIAS_VALIDAS))

    return {"nome": nome, "descricao": descricao, "preco": preco, "estoque": estoque, "categoria": categoria}


def _float_opcional(args, nome):
    valor = args.get(nome)
    if valor is None or valor == "":
        return None
    try:
        return float(valor)
    except ValueError:
        raise ValidationError(nome + " deve ser numérico") from None


def validar_busca(args):
    return {
        "termo": args.get("q", ""),
        "categoria": args.get("categoria") or None,
        "preco_min": _float_opcional(args, "preco_min"),
        "preco_max": _float_opcional(args, "preco_max"),
    }


def validar_usuario(dados):
    if not isinstance(dados, dict) or not dados:
        raise ValidationError("Dados inválidos")
    nome, email, senha = dados.get("nome"), dados.get("email"), dados.get("senha")
    if not (_texto_preenchido(nome) and _texto_preenchido(email) and _texto_preenchido(senha)):
        raise ValidationError("Nome, email e senha são obrigatórios")
    if not EMAIL_REGEX.match(email):
        raise ValidationError("Email inválido")
    return {"nome": nome.strip(), "email": email, "senha": senha}


def validar_login(dados):
    dados = dados if isinstance(dados, dict) else {}
    email, senha = dados.get("email"), dados.get("senha")
    if not (_texto_preenchido(email) and _texto_preenchido(senha)):
        raise ValidationError("Email e senha são obrigatórios")
    return {"email": email, "senha": senha}


def validar_pedido(dados):
    if not isinstance(dados, dict) or not dados:
        raise ValidationError("Dados inválidos")
    usuario_id = dados.get("usuario_id")
    itens = dados.get("itens")
    if not usuario_id:
        raise ValidationError("Usuario ID é obrigatório")
    if not _inteiro(usuario_id) or usuario_id < 1:
        raise ValidationError("Usuario ID deve ser um inteiro positivo")
    if not isinstance(itens, list) or not itens:
        raise ValidationError("Pedido deve ter pelo menos 1 item")
    normalizados = []
    for item in itens:
        if not isinstance(item, dict):
            raise ValidationError("Item inválido: produto_id e quantidade são obrigatórios")
        produto_id, quantidade = item.get("produto_id"), item.get("quantidade")
        if not _inteiro(produto_id) or not _inteiro(quantidade) or quantidade < 1:
            raise ValidationError("Item inválido: produto_id e quantidade (inteiro maior que zero) são obrigatórios")
        normalizados.append({"produto_id": produto_id, "quantidade": quantidade})
    return {"usuario_id": usuario_id, "itens": normalizados}


def validar_status(dados):
    status = dados.get("status") if isinstance(dados, dict) else None
    if status not in STATUS_PEDIDO_VALIDOS:
        raise ValidationError("Status inválido")
    return status
