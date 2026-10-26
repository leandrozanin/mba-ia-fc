import re

from errors import ValidationError

CATEGORIAS_VALIDAS = ["informatica", "moveis", "vestuario", "geral", "eletronicos", "livros"]
CATEGORIA_PADRAO = "geral"
NOME_PRODUTO_MIN = 2
NOME_PRODUTO_MAX = 200
EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def exigir_corpo(dados):
    if not isinstance(dados, dict) or not dados:
        raise ValidationError("Dados inválidos")
    return dados


def _numero(valor):
    return isinstance(valor, (int, float)) and not isinstance(valor, bool)


def _inteiro(valor):
    return isinstance(valor, int) and not isinstance(valor, bool)


def validar_produto(dados):
    """Regra única para criar e atualizar produto."""
    exigir_corpo(dados)
    for campo, rotulo in (("nome", "Nome"), ("preco", "Preço"), ("estoque", "Estoque")):
        if campo not in dados:
            raise ValidationError(f"{rotulo} é obrigatório")

    nome = dados["nome"]
    descricao = dados.get("descricao", "")
    preco = dados["preco"]
    estoque = dados["estoque"]
    categoria = dados.get("categoria", CATEGORIA_PADRAO)

    if not isinstance(nome, str) or not isinstance(descricao, str):
        raise ValidationError("Nome e descrição devem ser texto")
    if not _numero(preco):
        raise ValidationError("Preço deve ser numérico")
    if not _inteiro(estoque):
        raise ValidationError("Estoque deve ser inteiro")
    if preco < 0:
        raise ValidationError("Preço não pode ser negativo")
    if estoque < 0:
        raise ValidationError("Estoque não pode ser negativo")
    if len(nome) < NOME_PRODUTO_MIN:
        raise ValidationError("Nome muito curto")
    if len(nome) > NOME_PRODUTO_MAX:
        raise ValidationError("Nome muito longo")
    if categoria not in CATEGORIAS_VALIDAS:
        raise ValidationError("Categoria inválida. Válidas: " + str(CATEGORIAS_VALIDAS))

    return {"nome": nome, "descricao": descricao, "preco": preco, "estoque": estoque, "categoria": categoria}


def validar_faixa_preco(valor, rotulo):
    if valor in (None, ""):
        return None
    try:
        return float(valor)
    except ValueError:
        raise ValidationError(f"{rotulo} deve ser numérico") from None


def validar_itens_pedido(itens):
    """Valida os itens e agrega quantidades por produto."""
    if not isinstance(itens, list) or not itens:
        raise ValidationError("Pedido deve ter pelo menos 1 item")
    quantidades = {}
    for item in itens:
        if not isinstance(item, dict) or not _inteiro(item.get("produto_id")):
            raise ValidationError("Cada item precisa de produto_id inteiro")
        quantidade = item.get("quantidade")
        if not _inteiro(quantidade) or quantidade <= 0:
            raise ValidationError("Quantidade deve ser um inteiro positivo")
        quantidades[item["produto_id"]] = quantidades.get(item["produto_id"], 0) + quantidade
    return quantidades


def texto_obrigatorio(dados, *campos):
    valores = [dados.get(campo, "") for campo in campos]
    if not all(isinstance(valor, str) and valor.strip() for valor in valores):
        return None
    return valores
