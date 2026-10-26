from errors import ConflictError, NotFoundError, ValidationError
from models.database import get_db

STATUS_PENDENTE = "pendente"
STATUS_CANCELADO = "cancelado"


def criar(usuario_id, quantidades):
    """Cria pedido, itens e baixa de estoque numa única transação.

    `quantidades` mapeia produto_id -> quantidade total já agregada.
    """
    db = get_db()
    with db:
        produtos = {}
        for produto_id, quantidade in quantidades.items():
            produto = db.execute("SELECT nome, preco, estoque FROM produtos WHERE id = ?", (produto_id,)).fetchone()
            if produto is None:
                raise ValidationError(f"Produto {produto_id} não encontrado", sucesso=False)
            if produto["estoque"] < quantidade:
                raise ValidationError(f"Estoque insuficiente para {produto['nome']}", sucesso=False)
            produtos[produto_id] = produto

        total = sum(produtos[pid]["preco"] * qtd for pid, qtd in quantidades.items())
        pedido_id = db.execute(
            "INSERT INTO pedidos (usuario_id, status, total) VALUES (?, ?, ?)",
            (usuario_id, STATUS_PENDENTE, total),
        ).lastrowid

        for produto_id, quantidade in quantidades.items():
            db.execute(
                "INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario) VALUES (?, ?, ?, ?)",
                (pedido_id, produto_id, quantidade, produtos[produto_id]["preco"]),
            )
            baixa = db.execute(
                "UPDATE produtos SET estoque = estoque - ? WHERE id = ? AND estoque >= ?",
                (quantidade, produto_id, quantidade),
            )
            if baixa.rowcount != 1:
                raise ValidationError(f"Estoque insuficiente para {produtos[produto_id]['nome']}", sucesso=False)

    return {"pedido_id": pedido_id, "total": total}


def listar(usuario_id=None):
    db = get_db()
    if usuario_id is None:
        pedidos = db.execute("SELECT * FROM pedidos ORDER BY id").fetchall()
    else:
        pedidos = db.execute("SELECT * FROM pedidos WHERE usuario_id = ? ORDER BY id", (usuario_id,)).fetchall()
    if not pedidos:
        return []

    # Uma consulta para todos os itens, em vez de uma por pedido e por produto.
    ids = [pedido["id"] for pedido in pedidos]
    marcadores = ",".join("?" * len(ids))
    itens = db.execute(
        f"""
        SELECT i.pedido_id, i.produto_id, i.quantidade, i.preco_unitario, p.nome AS produto_nome
        FROM itens_pedido i LEFT JOIN produtos p ON p.id = i.produto_id
        WHERE i.pedido_id IN ({marcadores})
        ORDER BY i.id
        """,
        ids,
    ).fetchall()

    itens_por_pedido = {pedido_id: [] for pedido_id in ids}
    for item in itens:
        itens_por_pedido[item["pedido_id"]].append({
            "produto_id": item["produto_id"],
            "produto_nome": item["produto_nome"] or "Desconhecido",
            "quantidade": item["quantidade"],
            "preco_unitario": item["preco_unitario"],
        })

    return [
        {
            "id": pedido["id"],
            "usuario_id": pedido["usuario_id"],
            "status": pedido["status"],
            "total": pedido["total"],
            "criado_em": pedido["criado_em"],
            "itens": itens_por_pedido[pedido["id"]],
        }
        for pedido in pedidos
    ]


def atualizar_status(pedido_id, novo_status):
    """Muda o status; ao cancelar, devolve o estoque na mesma transação."""
    db = get_db()
    with db:
        pedido = db.execute("SELECT status FROM pedidos WHERE id = ?", (pedido_id,)).fetchone()
        if pedido is None:
            raise NotFoundError("Pedido não encontrado")
        if pedido["status"] == STATUS_CANCELADO and novo_status != STATUS_CANCELADO:
            raise ConflictError("Pedido cancelado não pode mudar de status")

        if novo_status == STATUS_CANCELADO and pedido["status"] != STATUS_CANCELADO:
            db.execute(
                """
                UPDATE produtos SET estoque = estoque + (
                    SELECT SUM(quantidade) FROM itens_pedido
                    WHERE pedido_id = ? AND produto_id = produtos.id
                )
                WHERE id IN (SELECT produto_id FROM itens_pedido WHERE pedido_id = ?)
                """,
                (pedido_id, pedido_id),
            )
        db.execute("UPDATE pedidos SET status = ? WHERE id = ?", (novo_status, pedido_id))


def resumo_vendas():
    db = get_db()
    total_pedidos, faturamento = db.execute("SELECT COUNT(*), COALESCE(SUM(total), 0) FROM pedidos").fetchone()
    por_status = dict(db.execute("SELECT status, COUNT(*) FROM pedidos GROUP BY status").fetchall())
    return {"total_pedidos": total_pedidos, "faturamento": faturamento, "por_status": por_status}


def contar():
    return get_db().execute("SELECT COUNT(*) FROM pedidos").fetchone()[0]
