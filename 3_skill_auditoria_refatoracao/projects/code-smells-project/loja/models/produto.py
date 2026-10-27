CAMPOS = ("id", "nome", "descricao", "preco", "estoque", "categoria", "ativo", "criado_em")


def _from_row(row):
    return {campo: row[campo] for campo in CAMPOS}


def listar(db):
    return [_from_row(row) for row in db.execute("SELECT * FROM produtos")]


def buscar_por_id(db, produto_id):
    row = db.execute("SELECT * FROM produtos WHERE id = ?", (produto_id,)).fetchone()
    return _from_row(row) if row else None


def criar(db, nome, descricao, preco, estoque, categoria):
    cursor = db.execute(
        "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) VALUES (?, ?, ?, ?, ?)",
        (nome, descricao, preco, estoque, categoria),
    )
    return cursor.lastrowid


def atualizar(db, produto_id, nome, descricao, preco, estoque, categoria):
    cursor = db.execute(
        "UPDATE produtos SET nome = ?, descricao = ?, preco = ?, estoque = ?, categoria = ? WHERE id = ?",
        (nome, descricao, preco, estoque, categoria, produto_id),
    )
    return cursor.rowcount > 0


def deletar(db, produto_id):
    return db.execute("DELETE FROM produtos WHERE id = ?", (produto_id,)).rowcount > 0


def buscar(db, termo="", categoria=None, preco_min=None, preco_max=None):
    clausulas = []
    parametros = []
    if termo:
        clausulas.append("(nome LIKE ? OR descricao LIKE ?)")
        padrao = "%" + termo + "%"
        parametros += [padrao, padrao]
    if categoria:
        clausulas.append("categoria = ?")
        parametros.append(categoria)
    if preco_min is not None:
        clausulas.append("preco >= ?")
        parametros.append(preco_min)
    if preco_max is not None:
        clausulas.append("preco <= ?")
        parametros.append(preco_max)
    where = " WHERE " + " AND ".join(clausulas) if clausulas else ""
    return [_from_row(row) for row in db.execute("SELECT * FROM produtos" + where, parametros)]


def baixar_estoque(db, produto_id, quantidade):
    """Baixa condicional: só debita se houver estoque suficiente. Retorna False caso contrário."""
    cursor = db.execute(
        "UPDATE produtos SET estoque = estoque - ? WHERE id = ? AND estoque >= ?",
        (quantidade, produto_id, quantidade),
    )
    return cursor.rowcount > 0


def devolver_estoque(db, produto_id, quantidade):
    db.execute("UPDATE produtos SET estoque = estoque + ? WHERE id = ?", (quantidade, produto_id))


def contar(db):
    return db.execute("SELECT COUNT(*) FROM produtos").fetchone()[0]
