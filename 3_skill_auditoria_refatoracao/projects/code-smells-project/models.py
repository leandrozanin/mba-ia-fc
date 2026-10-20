from database import get_db
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

def get_todos_produtos():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM produtos")
    rows = cursor.fetchall()
    result = []
    for row in rows:

        result.append({
            "id": row["id"],
            "nome": row["nome"],
            "descricao": row["descricao"],
            "preco": row["preco"],
            "estoque": row["estoque"],
            "categoria": row["categoria"],
            "ativo": row["ativo"],
            "criado_em": row["criado_em"]
        })
    return result

def get_produto_por_id(id):
    db = get_db()
    cursor = db.cursor()

    cursor.execute("SELECT * FROM produtos WHERE id = ?", (id,))
    row = cursor.fetchone()
    if row:
        return {
            "id": row["id"],
            "nome": row["nome"],
            "descricao": row["descricao"],
            "preco": row["preco"],
            "estoque": row["estoque"],
            "categoria": row["categoria"],
            "ativo": row["ativo"],
            "criado_em": row["criado_em"]
        }
    return None

def criar_produto(nome, descricao, preco, estoque, categoria):
    db = get_db()
    cursor = db.execute("INSERT INTO produtos (nome, descricao, preco, estoque, categoria) VALUES (?, ?, ?, ?, ?)",
                        (nome, descricao, preco, estoque, categoria))
    db.commit()
    return cursor.lastrowid

def atualizar_produto(id, nome, descricao, preco, estoque, categoria):
    db = get_db()
    db.execute("UPDATE produtos SET nome = ?, descricao = ?, preco = ?, estoque = ?, categoria = ? WHERE id = ?",
               (nome, descricao, preco, estoque, categoria, id))
    db.commit()
    return True

def deletar_produto(id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM produtos WHERE id = ?", (id,))
    db.commit()
    return True

def get_todos_usuarios():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM usuarios")
    rows = cursor.fetchall()
    result = []
    for row in rows:
        result.append({
            "id": row["id"],
            "nome": row["nome"],
            "email": row["email"],
            "senha": row["senha"],
            "tipo": row["tipo"],
            "criado_em": row["criado_em"]
        })
    return result

def get_usuario_por_id(id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM usuarios WHERE id = ?", (id,))
    row = cursor.fetchone()
    if row:
        return {
            "id": row["id"],
            "nome": row["nome"],
            "email": row["email"],
            "senha": row["senha"],
            "tipo": row["tipo"],
            "criado_em": row["criado_em"]
        }
    return None

def login_usuario(email, senha):
    row = get_db().execute("SELECT * FROM usuarios WHERE email = ?", (email,)).fetchone()
    if not row:
        return None
    stored = row["senha"]
    valid = check_password_hash(stored, senha) if stored.startswith("scrypt:") or stored.startswith("pbkdf2:") else stored == senha
    if not valid:
        return None
    return {"id": row["id"], "nome": row["nome"], "email": row["email"], "tipo": row["tipo"]}

def criar_usuario(nome, email, senha, tipo="cliente"):
    db = get_db()
    cursor = db.execute("INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
                        (nome, email, generate_password_hash(senha), tipo))
    db.commit()
    return cursor.lastrowid

def criar_pedido(usuario_id, itens):
    db = get_db()
    try:
        total = 0
        produtos = []
        for item in itens:
            quantidade = int(item['quantidade'])
            if quantidade <= 0:
                return {"erro": "Quantidade inv?lida"}
            produto = db.execute("SELECT * FROM produtos WHERE id = ?", (int(item['produto_id']),)).fetchone()
            if produto is None:
                return {"erro": f"Produto {item['produto_id']} n?o encontrado"}
            if produto['estoque'] < quantidade:
                return {"erro": f"Estoque insuficiente para {produto['nome']}"}
            produtos.append((produto, quantidade))
            total += produto['preco'] * quantidade
        cursor = db.execute("INSERT INTO pedidos (usuario_id, status, total) VALUES (?, 'pendente', ?)",
                            (int(usuario_id), total))
        pedido_id = cursor.lastrowid
        for produto, quantidade in produtos:
            db.execute("INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario) VALUES (?, ?, ?, ?)",
                       (pedido_id, produto['id'], quantidade, produto['preco']))
            db.execute("UPDATE produtos SET estoque = estoque - ? WHERE id = ?", (quantidade, produto['id']))
        db.commit()
        return {"pedido_id": pedido_id, "total": total}
    except (TypeError, ValueError, KeyError):
        db.rollback()
        return {"erro": "Itens do pedido inv?lidos"}
    except Exception:
        db.rollback()
        raise

def get_pedidos_usuario(usuario_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM pedidos WHERE usuario_id = ?", (usuario_id,))
    rows = cursor.fetchall()
    result = []
    for row in rows:
        pedido = {
            "id": row["id"],
            "usuario_id": row["usuario_id"],
            "status": row["status"],
            "total": row["total"],
            "criado_em": row["criado_em"],
            "itens": []
        }

        cursor2 = db.cursor()
        cursor2.execute("SELECT * FROM itens_pedido WHERE pedido_id = ?", (row["id"],))
        itens = cursor2.fetchall()
        for item in itens:
            cursor3 = db.cursor()
            cursor3.execute("SELECT nome FROM produtos WHERE id = ?", (item["produto_id"],))
            prod = cursor3.fetchone()
            pedido["itens"].append({
                "produto_id": item["produto_id"],
                "produto_nome": prod["nome"] if prod else "Desconhecido",
                "quantidade": item["quantidade"],
                "preco_unitario": item["preco_unitario"]
            })
        result.append(pedido)
    return result

def get_todos_pedidos():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM pedidos")
    rows = cursor.fetchall()
    result = []
    for row in rows:

        pedido = {
            "id": row["id"],
            "usuario_id": row["usuario_id"],
            "status": row["status"],
            "total": row["total"],
            "criado_em": row["criado_em"],
            "itens": []
        }
        cursor2 = db.cursor()
        cursor2.execute("SELECT * FROM itens_pedido WHERE pedido_id = ?", (row["id"],))
        itens = cursor2.fetchall()
        for item in itens:
            cursor3 = db.cursor()
            cursor3.execute("SELECT nome FROM produtos WHERE id = ?", (item["produto_id"],))
            prod = cursor3.fetchone()
            pedido["itens"].append({
                "produto_id": item["produto_id"],
                "produto_nome": prod["nome"] if prod else "Desconhecido",
                "quantidade": item["quantidade"],
                "preco_unitario": item["preco_unitario"]
            })
        result.append(pedido)
    return result

def relatorio_vendas():
    db = get_db()
    cursor = db.cursor()

    cursor.execute("SELECT COUNT(*) FROM pedidos")
    total_pedidos = cursor.fetchone()[0]

    cursor.execute("SELECT SUM(total) FROM pedidos")
    faturamento = cursor.fetchone()[0]
    if faturamento is None:
        faturamento = 0

    cursor.execute("SELECT COUNT(*) FROM pedidos WHERE status = 'pendente'")
    pendentes = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM pedidos WHERE status = 'aprovado'")
    aprovados = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM pedidos WHERE status = 'cancelado'")
    cancelados = cursor.fetchone()[0]

    desconto = 0
    if faturamento > 10000:
        desconto = faturamento * 0.1
    elif faturamento > 5000:
        desconto = faturamento * 0.05
    elif faturamento > 1000:
        desconto = faturamento * 0.02

    return {
        "total_pedidos": total_pedidos,
        "faturamento_bruto": round(faturamento, 2),
        "desconto_aplicavel": round(desconto, 2),
        "faturamento_liquido": round(faturamento - desconto, 2),
        "pedidos_pendentes": pendentes,
        "pedidos_aprovados": aprovados,
        "pedidos_cancelados": cancelados,
        "ticket_medio": round(faturamento / total_pedidos, 2) if total_pedidos > 0 else 0
    }

def atualizar_status_pedido(pedido_id, novo_status):
    db = get_db()
    cursor = db.cursor()

    cursor.execute(
        "UPDATE pedidos SET status = '" + novo_status + "' WHERE id = " + str(pedido_id)
    )
    db.commit()
    return True

def buscar_produtos(termo, categoria=None, preco_min=None, preco_max=None):
    db = get_db()
    clauses = []
    params = []
    if termo:
        clauses.append("(nome LIKE ? OR descricao LIKE ?)")
        params.extend([f"%{termo}%", f"%{termo}%"])
    if categoria:
        clauses.append("categoria = ?")
        params.append(categoria)
    if preco_min is not None:
        clauses.append("preco >= ?")
        params.append(preco_min)
    if preco_max is not None:
        clauses.append("preco <= ?")
        params.append(preco_max)
    sql = "SELECT * FROM produtos" + (" WHERE " + " AND ".join(clauses) if clauses else "")
    rows = db.execute(sql, params).fetchall()
    return [{key: row[key] for key in row.keys()} for row in rows]
